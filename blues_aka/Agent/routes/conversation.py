import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from blues_aka.Agent.models.agent import Agent
from blues_aka.Agent.models.conversation import Conversation
from blues_aka.Agent.schemas import CreateConversationSchema
from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.extensions import db

logger = logging.getLogger(__name__)
conversation_bp = Blueprint('conversation', __name__, url_prefix='/conversation')

@conversation_bp.route('/conversations', methods=['POST'])
@jwt_required()
@handle_api_response
def create_conversation():
    """创建新对话"""
    try:
        schema = CreateConversationSchema()
        data = schema.load(request.json)
        user_id = get_jwt_identity()

        if data.get('agent_id'):
            agent = Agent.query.filter_by(id=data['agent_id']).first()
            if not agent or (agent.user_id != user_id and not agent.is_public):
                raise BusinessException(code=404, message="智能体不存在或无权访问", error_code=404)

        conversation = Conversation(
            user_id=user_id,
            agent_id=data.get('agent_id'),
            title=data['title'],
            description=data.get('description'),
            model=data.get('model')
        )

        db.session.add(conversation)
        db.session.commit()

        return success(data=conversation.to_dict(include_agent=True), message="创建成功")

    except ValidationError as err:
        raise BusinessException(code=400, message="数据验证失败", error_code=err.messages)

    except Exception as e:
        db.session.rollback()
        raise BusinessException(code=500, message=str(e), error_code=500)

@conversation_bp.route('/conversations', methods=['GET'])
@jwt_required()
@handle_api_response
def get_conversations():
    """获取对话列表"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        status = request.args.get('status', 'active')

        query = Conversation.query.filter_by(user_id=user_id, status=status)

        pagination = query.order_by(Conversation.last_message_at.desc().nullslast()).paginate(page, size, error_out=False)

        items = [conversation.to_dict(include_agent = True) for conversation in pagination.items]

        data = {
            'items': items,
            'total': pagination.total,
            'page': page,
            'size': size,
        }

        return success(data=data, message="对话查询成功")

    except Exception as e:
        raise BusinessException(code=500, message=str(e), error_code=500)

@conversation_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@jwt_required()
@handle_api_response
def get_conversation(conversation_id):
    """获取对话详情"""
    try:
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise BusinessException(code=404, message="对话不存在", error_code=404)

        data = conversation.to_dict(include_agent = True)

        return success(data=data)

    except Exception as e:
        raise BusinessException(code=500, message=str(e), error_code=500)

@conversation_bp.route('/conversations/<int:conversation_id>', methods=['PUT'])
@jwt_required()
@handle_api_response
def update_conversation(conversation_id):
    """更新对话"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise BusinessException(code=404, message="对话不存在", error_code=404)

        if data.get('title'):
            conversation.title = data.get('title')
        if data.get('description'):
            conversation.description = data.get('description')
        db.session.commit()

        return success(data=conversation.to_dict(), message="更新成功")

    except Exception as e:
        db.session.rollback()
        raise BusinessException(code=500, message=str(e), error_code=500)

@conversation_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@jwt_required()
@handle_api_response
def delete_conversation(conversation_id):
    """删除对话"""
    try:
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise BusinessException(code=404, message="对话不存在", error_code=404)

        conversation.delete_soft()
        return success(message="删除成功！")

    except Exception as e:
        db.session.rollback()
        raise BusinessException(code=500, message=str(e), error_code=500)

@conversation_bp.route('/conversations/<int:conversation_id>/archive', methods=['PATCH'])
@jwt_required()
@handle_api_response
def archive_conversation(conversation_id):
    """归档对话"""
    try:
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise BusinessException(code=404, message="对话不存在", error_code=404)

        conversation.archive()
        return success(message="归档成功！")

    except Exception as e:
        db.session.rollback()
        raise BusinessException(code=500, message=str(e), error_code=500)

