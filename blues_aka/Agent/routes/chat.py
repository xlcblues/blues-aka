import json
import logging

from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import func

from blues_aka.Agent.BaseAgent import BaseAgent
from blues_aka.Agent.models.conversation import Conversation
from blues_aka.Agent.models.message import Message
from blues_aka.Agent.schemas import ChatSchema
from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.extensions import db

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/conversations/<int:conversation_id>/chat', methods=['POST'])
@jwt_required()
@handle_api_response
def chat(conversation_id):
    """发送消息并获取回复"""
    try:
        user_id = get_jwt_identity()
        schema = ChatSchema()
        data = schema.load(request.json)
        stream = data.get('stream', True)
        content = data.get('content')

        logger.info(f"收到聊天请求 - conversation_id: {conversation_id}, user_id: {user_id}, stream: {stream}")
        logger.info(f"消息内容: {content[:100]}..." if len(content) > 100 else f"消息内容: {content}")

        # 获取对话
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            logger.error(f"对话不存在 - conversation_id: {conversation_id}, user_id: {user_id}")
            raise BusinessException(code=404, message="对话不存在", error_code=404)

        # 获取聊天历史（在保存当前用户消息之前）
        chat_history = Message.get_message_history(conversation_id, limit=50)

        # 保存用户对话
        user_message = Message(
            conversation_id=conversation.id,
            content=content,
            user_id=user_id,
            role='user'
        )
        db.session.add(user_message)
        db.session.commit()

        # 获取智能体配置
        agent_config = {}
        if conversation.agent:
            logger.info(f"使用智能体 - id: {conversation.agent.id}, name: {conversation.agent.name}, model: {conversation.agent.model}")
            # tools 从数据库读取的是 JSON，如果是 None 或空列表，不传递给 BaseAgent
            # 让 BaseAgent 使用默认的 BASIC_TOOLS
            tools_param = None
            if conversation.agent.tools:
                # 如果 agent 配置了自定义工具，这里需要处理
                # 目前暂时忽略数据库中的 tools 配置，使用默认工具
                # TODO: 未来可以根据 conversation.agent.tools 中的工具名称动态加载对应的工具
                pass

            agent_config = {
                'model': conversation.agent.model,
                'system_prompt': conversation.agent.system_prompt,
                # 不传递 tools，让 BaseAgent 使用默认工具
                # 注意：temperature 和 max_tokens 应该在模型层面配置，不传给 BaseAgent
            }
        elif conversation.model:
            logger.info(f"使用对话模型 - model: {conversation.model}")
            agent_config = {'model': conversation.model}

        # RAG配置 - 从 agent 获取 RAG 配置
        if conversation.agent and hasattr(conversation.agent, 'enable_rag') and conversation.agent.enable_rag:
            rag_index_name = getattr(conversation.agent, 'rag_index_name', None)
            if rag_index_name:
                logger.info(f"启用RAG - index_name: {rag_index_name}")
                agent_config['enable_rag'] = True
                agent_config['rag_index_name'] = rag_index_name

                rag_config = getattr(conversation.agent, 'rag_config', None)
                if rag_config:
                    try:
                        agent_config['rag_config'] = json.loads(rag_config)
                    except json.JSONDecodeError:
                        logger.warning("RAG配置JSON解析失败，使用默认配置")

        logger.info(f"创建 BaseAgent，配置: {agent_config}")

        # 创建agent实例
        try:
            agent = BaseAgent(**agent_config)
            logger.info("BaseAgent 创建成功")
        except Exception as e:
            logger.error(f"创建 BaseAgent 失败: {str(e)}", exc_info=True)
            raise
        # 流式和非流式输出
        if stream:
            try:
                response = Response(
                    stream_with_context(generate_streaming_response(agent, content, chat_history, conversation_id, user_id)),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no'
                    }
                )
                return response
            except Exception as e:
                logger.error(f"流式响应创建失败: {str(e)}", exc_info=True)
                raise BusinessException(code=500, message=f"流式响应创建失败: {str(e)}")
        else:
            response_content = agent.invoke(input_text=content, chat_history=chat_history)

            # 获取模型名称
            model_name = 'glm-4.5'
            if hasattr(agent.model, 'model_name'):
                model_name = agent.model.model_name
            elif hasattr(agent.model, 'model'):
                model_name = agent.model.model
            elif isinstance(agent.model, str):
                model_name = agent.model
            else:
                model_name = agent_config.get('model', 'glm-4.5')

            #更新ai消息
            ai_message = Message(
                conversation_id=conversation.id,
                content=response_content,
                user_id=user_id,
                role='assistant',
                model=model_name
            )
            db.session.add(ai_message)
            db.session.commit()

            conversation.update_message_stats()

            result = {
                'message': ai_message.to_dict(),
                'conversation': conversation.to_dict()
            }

            return success(data=result, message=ai_message.to_dict())

    except ValidationError as err:
        raise BusinessException(code=400, message=str(err))
    except Exception as e:
        db.session.rollback()
        raise BusinessException(code=500, message=str(e))

def generate_streaming_response(agent, content, chat_history, conversation_id, user_id):
    """生成流式响应"""
    ai_message = None
    message_id = None
    try:
        logger.info(f"开始生成流式响应 - conversation_id: {conversation_id}")
        logger.info(f"聊天历史长度: {len(chat_history)}")

        # 获取模型名称（从模型实例中提取）
        model_name = 'glm-4.5'
        if hasattr(agent.model, 'model_name'):
            model_name = agent.model.model_name
        elif hasattr(agent.model, 'model'):
            model_name = agent.model.model
        elif isinstance(agent.model, str):
            model_name = agent.model

        logger.info(f"使用模型: {model_name}")

        # 创建并添加 AI 消息到数据库
        ai_message = Message(
            conversation_id=conversation_id,
            content='',
            user_id=user_id,
            role='assistant',
            model=model_name
        )

        # 添加到会话并刷新以获取 ID
        db.session.add(ai_message)
        db.session.flush()
        message_id = ai_message.id

        logger.info(f"创建 AI 消息，ID: {message_id}")

        # 发送开始事件
        yield f"data: {json.dumps({'type': 'start', 'message_id': message_id})}\n\n"

        # 流式生成响应
        logger.info("开始流式生成...")
        full_content = []
        try:
            for chunk in agent.streaming(input_text=content, chat_history=chat_history):
                if chunk:  # 只处理非空内容
                    full_content.append(chunk)
                    # 发送 token 事件，包含实际内容
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        except Exception as e:
            logger.error(f"流式生成过程出错: {str(e)}", exc_info=True)
            # 更新消息内容为错误信息
            if ai_message and message_id:
                try:
                    final_content = f"错误: {str(e)}"
                    ai_message.content = final_content
                    db.session.add(ai_message)
                    db.session.commit()
                except:
                    db.session.rollback()
            raise

        # 更新消息内容
        final_content = ''.join(full_content)
        if ai_message and message_id:
            ai_message.content = final_content

            # 提交到数据库
            db.session.add(ai_message)
            db.session.commit()

            logger.info(f"AI 消息保存成功，长度: {len(final_content)} 字符")

            # 更新对话统计（不在这里 commit，避免在流式响应中操作数据库）
            try:
                conversation = Conversation.query.get(conversation_id)
                if conversation:
                    conversation.message_count = Message.query.filter_by(conversation_id=conversation_id).count()
                    conversation.last_message_at = func.now()
                    db.session.add(conversation)
                    db.session.commit()
            except Exception as db_error:
                logger.error(f"更新对话统计失败: {str(db_error)}", exc_info=True)
                db.session.rollback()

        # 发送结束事件
        yield f"data: {json.dumps({'type': 'end', 'message_id': message_id, 'tokens': len(final_content)})}\n\n"

    except Exception as e:
        logger.error(f"流式响应生成失败: {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except:
            pass
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
@handle_api_response
def get_messages(conversation_id):
    """获取对话消息历史"""
    try:
        # 获取对话
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            raise BusinessException(code=404, message="对话不存在", error_code=404)

        messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at.asc()).all()

        items = [msg.to_dict() for msg in messages]
        return success(data=items)
    except Exception as e:
        raise BusinessException(code=500, message=str(e))

@chat_bp.route('/messages/<int:message_id>/feedback', methods=['POST'])
@jwt_required()
@handle_api_response
def message_feedback(message_id):
    """消息反馈"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        message = Message.query.filter_by(id=message_id, user_id=user_id).first()
        if not message:
            raise BusinessException(code=404, message="对话不存在", error_code=404)


        message.add_feedback(rating=data.get('rating', 0), feedback_text=data.get('feedback_text'))

        return success(message="反馈成功")

    except Exception as e:
        raise BusinessException(code=500, message="反馈失败")

@chat_bp.route('/conversations/<int:conversation_id>/regenerate', methods=['POST'])
@jwt_required()
@handle_api_response
def regenerate_message(conversation_id):
    """重新生成最后一条消息"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        stream = data.get('stream')
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise BusinessException(code=404, message="对话不存在", error_code=404)

        last_ai_message = Message.query.filter_by(conversation_id=conversation.id, role='assistant').order_by(Message.created_at.desc()).first()
        if not last_ai_message:
            raise BusinessException(code=400, message="没有可重新生成的消息", error_code=400)

        db.session.delete(last_ai_message)
        db.session.commit()

        chat_history = Message.get_message_history(conversation_id, limit=50)

        last_user_message = Message.query.filter_by(conversation_id=conversation.id, role='user').order_by(Message.created_at.desc()).first()
        if not last_user_message:
            raise BusinessException(code=400, message="没有用户消息", error_code=400)

        # 创建Agent并重新生成
        agent_config = {}
        if conversation.agent:
            # 不传递 tools，让 BaseAgent 使用默认工具
            agent_config = {
                'model': conversation.agent.model,
                'system_prompt': conversation.agent.system_prompt
            }
        elif conversation.model:
            agent_config = {'model': conversation.model}

        # RAG配置 - 从 agent 获取 RAG 配置
        if conversation.agent and hasattr(conversation.agent, 'enable_rag') and conversation.agent.enable_rag:
            rag_index_name = getattr(conversation.agent, 'rag_index_name', None)
            if rag_index_name:
                agent_config['enable_rag'] = True
                agent_config['rag_index_name'] = rag_index_name

                # 解析RAG配置
                rag_config = getattr(conversation.agent, 'rag_config', None)
                if rag_config:
                    try:
                        agent_config['rag_config'] = json.loads(rag_config)
                    except json.JSONDecodeError:
                        logger.warning("RAG配置JSON解析失败，使用默认配置")

        agent = BaseAgent(**agent_config)

        if stream:
            return Response(
                stream_with_context(
                    generate_streaming_response(agent, last_user_message.content, chat_history[:-1],
                                                conversation_id, user_id)
                ),
                mimetype='text/event-stream'
            )
        else:
            response_content = agent.invoke(input_text=last_user_message.content, chat_history=chat_history[:-1])

            # 获取模型名称
            model_name = 'glm-4.5'
            if hasattr(agent.model, 'model_name'):
                model_name = agent.model.model_name
            elif hasattr(agent.model, 'model'):
                model_name = agent.model.model
            elif isinstance(agent.model, str):
                model_name = agent.model
            else:
                model_name = agent_config.get('model', 'glm-4.5')

            ai_message = Message(
                conversation_id=conversation_id,
                user_id=user_id,
                role='assistant',
                content=response_content,
                model=model_name
            )
            db.session.add(ai_message)
            db.session.commit()

            conversation.update_message_stats()

            return success(data={
                'message': ai_message.to_dict(),
                'conversation': conversation.to_dict()
            })

    except Exception as e:
        db.session.rollback()
        raise BusinessException(code=500, message="重新生成失败", error_code=500)
