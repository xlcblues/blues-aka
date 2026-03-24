"""
聊天路由模块

本模块提供聊天相关的 API 接口，包括：

- 发送消息并获取 AI 回复（支持流式和非流式）
- 获取对话消息历史
- 消息反馈功能
- 重新生成最后一条 AI 消息

主要功能：
    1. 支持流式和非流式两种响应模式
    2. 自动保存用户消息和 AI 回复到数据库
    3. 支持智能体配置（系统提示词、模型选择）
    4. 支持 RAG（检索增强生成）功能
    5. 自动更新对话统计信息
    6. 消息反馈和重新生成功能

异常处理：
    - 使用统一的异常码体系
    - 所有异常都通过 Exceptions 辅助类抛出
    - 自动记录错误日志

Author: Blues AKA Team
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import func

from blues_aka.Agent.BaseAgent import BaseAgent
from blues_aka.Agent.models.conversation import Conversation
from blues_aka.Agent.models.message import Message
from blues_aka.Agent.schemas import ChatSchema
from blues_aka.common.exception import BusinessException
from blues_aka.common.exceptions import Exceptions
from blues_aka.common.rate_limit import RateLimits
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.core.tools import BASIC_TOOLS
from blues_aka.extensions import db

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/conversations/<int:conversation_id>/chat', methods=['POST'])
@jwt_required()
@handle_api_response
@RateLimits.CHAT  # 60 次/分钟，基于用户限流
def chat(conversation_id):
    """
    发送消息并获取 AI 回复

    支持流式和非流式两种响应模式。流式模式下，响应以 Server-Sent Events (SSE)
    格式实时返回生成的 token；非流式模式下，等待完整响应后一次性返回。

    请求方法: POST
    认证要求: 需要 JWT Token
    路由参数:
        conversation_id (int): 对话 ID

    请求体 (JSON):
        content (str): 用户消息内容，必填
        stream (bool): 是否使用流式响应，可选，默认为 True

    流式响应事件类型:
        - start: 流式响应开始，包含 message_id
        - token: 每次生成的文本片段
        - end: 流式响应结束，包含 message_id 和 tokens 数量
        - error: 发生错误时的错误信息

    非流式响应 (JSON):
        {
            "code": 200,
            "message": "成功",
            "data": {
                "message": {...},  # AI 消息对象
                "conversation": {...}  # 对话对象
            }
        }

    业务逻辑:
        1. 验证用户身份和对话归属
        2. 保存用户消息到数据库
        3. 加载对话历史（最近 50 条）
        4. 根据对话配置创建 Agent（支持智能体配置和 RAG）
        5. 调用 AI 模型生成响应
        6. 保存 AI 响应到数据库
        7. 更新对话统计信息

    智能体配置:
        - model: AI 模型名称
        - system_prompt: 系统提示词
        - enable_rag: 是否启用 RAG
        - rag_index_name: RAG 索引名称
        - rag_config: RAG 配置（JSON 格式）

    异常处理:
        - 400101: 对话不存在
        - 100001: 参数验证失败
        - 500101: 消息发送失败
        - 100301: 服务器内部错误

    Args:
        conversation_id (int): 对话 ID

    Returns:
        Response: 流式响应返回 SSE 流，非流式返回 JSON 对象

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在
        Exceptions.Common.invalid_params: 参数验证失败
        Exceptions.Chat.message_send_failed: 消息发送失败
        Exceptions.Common.internal_server_error: 服务器内部错误
    """
    try:
        user_id = get_jwt_identity()
        schema = ChatSchema()
        data = schema.load(request.json)
        stream = data.get('stream', True)
        content = data.get('content')
        enable_web_search = data.get('enable_web_search')
        show_reasoning = data.get('show_reasoning', False)
        logger.info(f"收到聊天请求 - conversation_id: {conversation_id}, user_id: {user_id}, stream: {stream}")
        logger.info(f"消息内容: {content[:100]}..." if len(content) > 100 else f"消息内容: {content}")

        # 获取对话
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            logger.error(f"对话不存在 - conversation_id: {conversation_id}, user_id: {user_id}")
            raise Exceptions.Conversation.conversation_not_found()

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

        # 清除历史缓存(因为添加了新消息)
        Message.invalidate_history_cache(conversation_id)

        # 获取智能体配置
        agent_config = {}
        tools_to_use = BASIC_TOOLS.copy()

        if conversation.agent:
            logger.info(f"使用智能体 - id: {conversation.agent.id}, name: {conversation.agent.name}, model: {conversation.agent.model}")

            # 动态加载工具配置
            if conversation.agent.tools:
                try:
                    from blues_aka.core.tools import get_tools_by_names
                    # agent.tools 是 JSON，存储工具名称列表，如 ['get_current_time', 'web_search']
                    custom_tools = get_tools_by_names(conversation.agent.tools)
                    # 使用自定义工具替换基础工具
                    tools_to_use = custom_tools
                    logger.info(f"已加载自定义工具: {conversation.agent.tools}")
                except ValueError as e:
                    # 工具配置有误，使用默认工具并记录警告
                    logger.warning(f"工具配置无效，使用默认工具: {str(e)}")
                    tools_to_use = BASIC_TOOLS.copy()

            agent_config = {
                'model': conversation.agent.model,
                'system_prompt': conversation.agent.system_prompt,
                'enable_thinking': show_reasoning
            }

            if enable_web_search is None:
                enable_web_search = getattr(conversation, 'enable_web_search', False)

            # 如果启用了联网搜索但工具列表中还没有，添加它
            if enable_web_search and 'web_search' not in (conversation.agent.tools or []):
                from blues_aka.core.tools import OPTIONAL_TOOLS
                if 'web_search' in OPTIONAL_TOOLS:
                    tools_to_use.append(OPTIONAL_TOOLS['web_search'])
                    logger.info("已启用联网搜索工具")

        elif conversation.model:
            logger.info(f"使用对话模型 - model: {conversation.model}")
            agent_config = {'model': conversation.model}

            if enable_web_search:
                from blues_aka.core.tools import OPTIONAL_TOOLS
                if 'web_search' in OPTIONAL_TOOLS:
                    tools_to_use.append(OPTIONAL_TOOLS['web_search'])
                    logger.info("已启用联网搜索工具")

        agent_config['tools'] = tools_to_use

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
            if show_reasoning:
                try:
                    response = Response(
                        stream_with_context(generate_streaming_response_with_thinking(agent, content, chat_history, conversation_id, user_id)),
                        mimetype='text/event-stream',
                        headers={
                            'Cache-Control': 'no-cache, no-transform',
                            'X-Accel-Buffering': 'no',
                            'Connection': 'keep-alive',
                        },
                        direct_passthrough=True
                    )
                    return response
                except Exception as e:
                    logger.error(f"流式响应创建失败: {str(e)}", exc_info=True)
                    raise Exceptions.Chat.message_send_failed(f"流式响应创建失败: {str(e)}")

            else:
                try:
                    response = Response(
                        stream_with_context(generate_streaming_response(agent, content, chat_history, conversation_id, user_id)),
                        mimetype='text/event-stream',
                        headers={
                            'Cache-Control': 'no-cache, no-transform',
                            'X-Accel-Buffering': 'no',
                            'Connection': 'keep-alive',
                        },
                        direct_passthrough=True
                    )
                    return response

                except Exception as e:
                    logger.error(f"流式响应创建失败: {str(e)}", exc_info=True)
                    raise Exceptions.Chat.message_send_failed(f"流式响应创建失败: {str(e)}")

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

            # 清除历史缓存(因为添加了新消息)
            Message.invalidate_history_cache(conversation_id)

            conversation.update_message_stats()
            db.session.commit()

            result = {
                'message': ai_message.to_dict(),
                'conversation': conversation.to_dict()
            }

            return success(data=result, message=ai_message.to_dict())

    except ValidationError as err:
        raise Exceptions.Common.invalid_params(str(err))
    except Exception as e:
        db.session.rollback()
        raise Exceptions.Common.internal_server_error(str(e))

def generate_streaming_response(agent, content, chat_history, conversation_id, user_id):
    """
    生成流式响应

    这是一个生成器函数，用于创建 SSE (Server-Sent Events) 格式的流式响应。
    该函数会实时将 AI 生成的每个 token 推送给客户端，提供更好的用户体验。

    工作流程：
        1. 创建空的 AI 消息记录并保存到数据库，获取 message_id
        2. 发送 'start' 事件，通知客户端流式响应开始
        3. 调用 Agent 的 streaming 方法生成响应
        4. 对每个生成的 token，发送 'token' 事件给客户端
        5. 将完整的响应内容保存到数据库
        6. 异步更新对话统计信息（消息数量、最后消息时间）
        7. 发送 'end' 事件，包含最终的消息 ID 和 token 数量
        8. 如果发生错误，发送 'error' 事件并回滚数据库事务

    SSE 事件格式：
        data: {"type": "start", "message_id": 123}

        data: {"type": "token", "content": "你好"}

        data: {"type": "end", "message_id": 123, "tokens": 150}

        data: {"type": "error", "message": "错误信息"}

    Args:
        agent (BaseAgent): Agent 实例，用于生成 AI 响应
        content (str): 用户输入的消息内容
        chat_history (list): 聊天历史记录，包含之前的对话内容
        conversation_id (int): 对话 ID，用于保存消息和更新统计
        user_id (int): 用户 ID，用于关联消息归属

    Yields:
        str: SSE 格式的事件数据，每个事件都以 "data: {...}\\n\\n" 结尾

    异常处理:
        - 捕获流式生成过程中的所有异常
        - 错误发生时，将 AI 消息内容更新为错误信息
        - 通过 SSE 'error' 事件将错误信息发送给客户端
        - 自动回滚数据库事务

    注意事项:
        - 使用 db.session.flush() 而不是 commit() 来获取 message_id
        - 在流式生成过程中不提交事务，避免性能问题
        - 对话统计信息通过后台线程异步更新，不阻塞流式响应
        - 统计更新失败不影响主流程，只记录日志
        - 错误处理中包含数据库回滚逻辑
        - 所有数据库操作都有独立的异常处理

    性能优化:
        - 使用 ThreadPoolExecutor 在后台线程中更新统计信息
        - 避免在生成器中进行数据库查询和更新操作
        - 统计更新失败不会影响用户体验
    """
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
        yield f"data: {json.dumps({'type': 'start', 'message_id': message_id})}\n\n".encode('utf-8')

        # 流式生成响应
        logger.info("开始流式生成...")
        full_content = []
        try:
            for chunk in agent.streaming(input_text=content, chat_history=chat_history):
                if chunk:  # 只处理非空内容
                    full_content.append(chunk)
                    # 发送 token 事件，包含实际内容
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n".encode('utf-8')
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

        # 在流式结束后再保存到数据库（不影响流式输出的体验）
        if ai_message and message_id:
            ai_message.content = final_content

            # 提交到数据库
            try:
                db.session.add(ai_message)
                db.session.commit()
                logger.info(f"AI 消息保存成功，长度: {len(final_content)} 字符")

                # 清除历史缓存
                Message.invalidate_history_cache(conversation_id)

                # 异步更新对话统计信息
                from blues_aka.tasks.conversation_task import update_conversation_stats_async

                if not hasattr(generate_streaming_response, '_executor'):
                    generate_streaming_response._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="conv_stats_")

                generate_streaming_response._executor.submit(
                    update_conversation_stats_async,
                    conversation_id
                )
            except Exception as db_error:
                logger.error(f"保存消息或统计信息失败: {db_error}", exc_info=True)
                try:
                    db.session.rollback()
                except:
                    pass

        # 发送结束事件
        yield f"data: {json.dumps({'type': 'end', 'message_id': message_id, 'tokens': len(final_content)})}\n\n".encode('utf-8')

    except Exception as e:
        logger.error(f"流式响应生成失败: {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except:
            pass
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n".encode('utf-8')

def generate_streaming_response_with_thinking(
    agent, content, chat_history, conversation_id, user_id
):
    """
    生成带推理信息的流式响应

    这是一个生成器函数，用于创建带推理信息的 SSE (Server-Sent Events) 格式流式响应。
    与普通流式响应不同，此函数会先输出 AI 的推理过程，然后输出最终答案。

    工作流程：
        1. 创建空的 AI 消息记录并保存到数据库，获取 message_id
        2. 发送 'start' 事件，通知客户端流式响应开始
        3. 调用 Agent 的 streaming_with_thinking 方法生成响应
        4. 对推理过程的每个 token，发送 'reasoning' 事件给客户端
        5. 推理结束后，发送 'reasoning_end' 事件
        6. 对最终答案的每个 token，发送 'content' 事件给客户端
        7. 将完整的响应内容保存到数据库
        8. 异步更新对话统计信息（消息数量、最后消息时间）
        9. 发送 'end' 事件，包含最终的消息 ID 和 token 数量
        10. 如果发生错误，发送 'error' 事件并回滚数据库事务

    SSE 事件格式：
        data: {"type": "start", "message_id": 123, "reasoning_enabled": true}
        data: {"type": "reasoning", "content": "推理过程..."}
        data: {"type": "reasoning_end", "total_length": 500}
        data: {"type": "content", "content": "最终答案..."}
        data: {"type": "end", "message_id": 123, "tokens": 300}
        data: {"type": "error", "message": "错误信息"}

    Args:
        agent (BaseAgent): Agent 实例，用于生成 AI 响应
        content (str): 用户输入的消息内容
        chat_history (list): 聊天历史记录，包含之前的对话内容
        conversation_id (int): 对话 ID，用于保存消息和更新统计
        user_id (int): 用户 ID，用于关联消息归属

    Yields:
        str: SSE 格式的事件数据，每个事件都以 "data: {...}\\n\\n" 结尾

    异常处理:
        - 捕获流式生成过程中的所有异常
        - 错误发生时，将 AI 消息内容更新为错误信息
        - 通过 SSE 'error' 事件将错误信息发送给客户端
        - 自动回滚数据库事务

    注意事项:
        - 推理过程和最终答案都会实时推送给客户端
        - 对话统计信息通过后台线程异步更新，不阻塞流式响应
        - 统计更新失败不影响主流程，只记录日志
        - 使用 db.session.flush() 获取 message_id，避免过早提交事务
        - 推理完成后会发送 reasoning_end 事件

    性能优化:
        - 使用 ThreadPoolExecutor 在后台线程中更新统计信息
        - 避免在生成器中进行数据库查询和更新操作
        - 统计更新失败不会影响用户体验
    """
    ai_message = None
    message_id = None

    try:
        logger.info(f"开始生成流式响应(推理) - conversation_id: {conversation_id}")

        ai_message = Message(
            conversation_id=conversation_id,
            content='',
            user_id=user_id,
            role='assistant',
        )
        db.session.add(ai_message)
        db.session.flush()
        message_id = ai_message.id
        yield f"data: {json.dumps({'type': 'start', 'message_id': message_id, 'reasoning_enabled': True})}\n\n".encode('utf-8')
        full_reasoning = []
        full_content = []
        reasoning_done = False
        content_started = False

        logger.info("开始进行推理")
        for event in agent.streaming_with_thinking(input_text=content, chat_history=chat_history):
            logger.info(event)
            event_type = event.get('type', 'unknown')

            if event_type == 'reasoning':
                reasoning_text = event.get('content', "")
                full_reasoning.append(reasoning_text)
                yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_text})}\n\n".encode('utf-8')

                if not content_started:
                    logger.debug("推理阶段进行中...")

            elif event_type == 'content':
                content_text = event.get('content', "")
                full_content.append(content_text)
                content_started = True

                if not reasoning_done and full_reasoning:
                    yield f"data: {json.dumps({'type': 'reasoning_end', 'total_length': sum(len(r) for r in full_reasoning)})}\n\n".encode('utf-8')
                    reasoning_done = True
                    logger.debug("推理阶段结束，开始输出最终答案")

                yield f"data: {json.dumps({'type': 'content', 'content': content_text})}\n\n".encode('utf-8')

            elif event_type == 'error':
                yield f"data: {json.dumps({'type': 'error', 'message': event.get('content')})}\n\n".encode('utf-8')
                raise Exception(event.get('content'))

        # 流式生成完成后，保存消息到数据库
        final_content = ''.join(full_content)
        ai_message.content = final_content
        db.session.add(ai_message)
        db.session.commit()

        # 清除历史缓存(因为添加了新消息)
        Message.invalidate_history_cache(conversation_id)

        # 异步更新对话统计信息
        # 使用线程池在后台执行统计更新，避免在生成器中进行数据库操作
        try:
            from blues_aka.tasks.conversation_task import update_conversation_stats_async

            # 创建线程池执行器（如果不存在）
            if not hasattr(generate_streaming_response_with_thinking, '_executor'):
                generate_streaming_response_with_thinking._executor = ThreadPoolExecutor(
                    max_workers=2,
                    thread_name_prefix="conv_stats_"
                )

            # 提交异步任务，不等待结果
            generate_streaming_response_with_thinking._executor.submit(
                update_conversation_stats_async,
                conversation_id
            )
            logger.info(f"已提交对话统计更新任务: conversation_id={conversation_id}")
        except Exception as async_error:
            # 异步任务提交失败不影响主流程，只记录日志
            logger.warning(
                f"提交对话统计更新任务失败: {str(async_error)}",
                exc_info=True
            )

        yield f"data: {json.dumps({'type': 'end', 'message_id': message_id, 'tokens': len(final_content)})}\n\n".encode('utf-8')

    except Exception as e:
        logger.error(f"流式响应生成失败: {str(e)}", exc_info=True)
        try:
            db.session.rollback()
        except:
            pass
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n".encode('utf-8')



@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
@handle_api_response
def get_messages(conversation_id):
    """
    获取对话消息历史

    查询指定对话的所有消息记录，按创建时间升序排列返回。

    请求方法: GET
    认证要求: 需要 JWT Token
    路由参数:
        conversation_id (int): 对话 ID

    响应格式 (JSON):
        {
            "code": 200,
            "message": "成功",
            "data": [
                {
                    "id": 1,
                    "conversation_id": 1,
                    "content": "用户消息内容",
                    "role": "user",
                    "user_id": 1,
                    "created_at": "2024-01-01T00:00:00",
                    "model": null,
                    "feedback": null
                },
                {
                    "id": 2,
                    "conversation_id": 1,
                    "content": "AI 回复内容",
                    "role": "assistant",
                    "user_id": 1,
                    "created_at": "2024-01-01T00:00:01",
                    "model": "glm-4.5",
                    "feedback": null
                }
            ]
        }

    业务逻辑:
        1. 验证用户身份和对话归属
        2. 查询对话的所有消息记录
        3. 按创建时间升序排序（早到晚）
        4. 返回消息列表

    消息角色类型:
        - user: 用户发送的消息
        - assistant: AI 生成的回复

    异常处理:
        - 400101: 对话不存在
        - 100301: 服务器内部错误

    Args:
        conversation_id (int): 对话 ID

    Returns:
        dict: 包含消息列表的响应对象
            {
                "code": 200,
                "message": "成功",
                "data": [list of message objects]
            }

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在
        Exceptions.Common.internal_server_error: 服务器内部错误
    """
    try:
        # 获取对话
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()
        if not conversation:
            raise Exceptions.Conversation.conversation_not_found()

        messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.created_at.asc()).all()

        items = [msg.to_dict() for msg in messages]
        return success(data=items)
    except Exception as e:
        raise Exceptions.Common.internal_server_error(str(e))

@chat_bp.route('/messages/<int:message_id>/feedback', methods=['POST'])
@jwt_required()
@handle_api_response
def message_feedback(message_id):
    """
    提交消息反馈

    允许用户对 AI 生成的消息进行评价和反馈，用于改进 AI 模型效果。
    支持评分和文本反馈两种形式。

    请求方法: POST
    认证要求: 需要 JWT Token
    路由参数:
        message_id (int): 消息 ID

    请求体 (JSON):
        rating (int): 评分，可选，通常为 1-5 的整数
        feedback_text (str): 反馈文本，可选，用户的具体意见或建议

    响应格式 (JSON):
        {
            "code": 200,
            "message": "反馈成功"
        }

    业务逻辑:
        1. 验证用户身份和消息归属
        2. 提取评分和反馈文本
        3. 调用消息模型的 add_feedback 方法保存反馈
        4. 返回成功响应

    使用场景:
        - 用户对 AI 回复质量进行评分
        - 收集用户对 AI 回复的具体意见
        - 用于后续的模型训练和改进

    异常处理:
        - 500201: 消息不存在
        - 500501: 反馈提交失败

    Args:
        message_id (int): 消息 ID

    Returns:
        dict: 成功响应对象
            {
                "code": 200,
                "message": "反馈成功"
            }

    Raises:
        Exceptions.Chat.message_not_found: 消息不存在
        Exceptions.Chat.feedback_failed: 反馈提交失败
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        message = Message.query.filter_by(id=message_id, user_id=user_id).first()
        if not message:
            raise Exceptions.Chat.message_not_found("对话不存在")


        message.add_feedback(rating=data.get('rating', 0), feedback_text=data.get('feedback_text'))

        return success(message="反馈成功")

    except Exception as e:
        raise Exceptions.Chat.feedback_failed()

@chat_bp.route('/conversations/<int:conversation_id>/regenerate', methods=['POST'])
@jwt_required()
@handle_api_response
def regenerate_message(conversation_id):
    """
    重新生成最后一条 AI 消息

    删除对话中最后一条 AI 消息，并基于最后一条用户消息重新生成 AI 回复。
    支持流式和非流式两种响应模式。

    请求方法: POST
    认证要求: 需要 JWT Token
    路由参数:
        conversation_id (int): 对话 ID

    请求体 (JSON):
        stream (bool): 是否使用流式响应，可选，默认为 True

    流式响应事件类型:
        - start: 流式响应开始，包含 message_id
        - token: 每次生成的文本片段
        - end: 流式响应结束，包含 message_id 和 tokens 数量
        - error: 发生错误时的错误信息

    非流式响应 (JSON):
        {
            "code": 200,
            "message": "成功",
            "data": {
                "message": {...},  # 重新生成的 AI 消息对象
                "conversation": {...}  # 对话对象
            }
        }

    业务逻辑:
        1. 验证用户身份和对话归属
        2. 查找并删除最后一条 AI 消息
        3. 如果没有 AI 消息可删除，抛出异常
        4. 获取对话历史（最近 50 条）
        5. 找到最后一条用户消息作为重新生成的输入
        6. 根据对话配置创建 Agent（支持智能体配置和 RAG）
        7. 调用 AI 模型重新生成响应
        8. 保存新的 AI 响应到数据库
        9. 更新对话统计信息

    使用场景:
        - 用户对 AI 回复不满意，希望重新生成
        - AI 回复质量不佳，需要重新尝试
        - 测试不同模型或配置下的回复效果

    智能体配置:
        - model: AI 模型名称
        - system_prompt: 系统提示词
        - enable_rag: 是否启用 RAG
        - rag_index_name: RAG 索引名称
        - rag_config: RAG 配置（JSON 格式）

    异常处理:
        - 400101: 对话不存在
        - 500602: 没有可重新生成的消息
        - 500601: 重新生成失败
        - 100301: 服务器内部错误

    Args:
        conversation_id (int): 对话 ID

    Returns:
        Response: 流式响应返回 SSE 流，非流式返回 JSON 对象

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在
        Exceptions.Chat.no_message_to_regenerate: 没有可重新生成的消息
        Exceptions.Chat.regenerate_failed: 重新生成失败
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        stream = data.get('stream')
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise Exceptions.Conversation.conversation_not_found()

        last_ai_message = Message.query.filter_by(conversation_id=conversation.id, role='assistant').order_by(Message.created_at.desc()).first()
        if not last_ai_message:
            raise Exceptions.Chat.no_message_to_regenerate()

        db.session.delete(last_ai_message)
        db.session.commit()

        chat_history = Message.get_message_history(conversation_id, limit=50)

        last_user_message = Message.query.filter_by(conversation_id=conversation.id, role='user').order_by(Message.created_at.desc()).first()
        if not last_user_message:
            raise Exceptions.Chat.no_message_to_regenerate("没有用户消息")

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
            db.session.commit()

            return success(data={
                'message': ai_message.to_dict(),
                'conversation': conversation.to_dict()
            })

    except Exception as e:
        db.session.rollback()
        raise Exceptions.Chat.regenerate_failed()
