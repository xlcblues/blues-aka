import logging

from dataclasses_json.mm import schema
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from blues_aka.Agent.models.agent import Agent
from blues_aka.Agent.schemas import CreateAgentSchema, UpdateAgentSchema
from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.extensions import db

logger = logging.getLogger(__name__)
agent_bp = Blueprint('agent', __name__, url_prefix='/agent')

@agent_bp.route('/agents', methods=['POST'])
@handle_api_response
@jwt_required()
def create_agent():
    """创建智能体"""
    try:
        logger.info('create agent')
        schema = CreateAgentSchema()
        data = schema.load(request.get_json())

        user_id = get_jwt_identity()

        agent = Agent(
            user_id=user_id,
            name=data['name'],
            description=data.get('description'),
            avatar=data.get('avatar'),
            model=data.get('model', 'gpt-4'),
            system_prompt=data.get('system_prompt'),
            prompt_mode=data.get('prompt_mode', 'default'),
            tools=data.get('tools'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 20000),
            top_p=data.get('top_p', 1.0),
            is_public=data.get('is_public', False),
            config=data.get('config')
        )

        db.session.add(agent)
        db.session.commit()

        return success(data=agent.to_dict(), message='智能体创建成功')


    except ValidationError as e:
        logger.warning(f"智能体创建参数验证失败: {e.messages}")
        raise BusinessException(code=400, message="参数校验失败", error_code="INVALID_PARAMS")

    except Exception as e:
        db.session.rollback()
        logger.error(f"智能体创建失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="智能体创建失败", error_code="AGENT_CREATION_FAILED")

@agent_bp.route('/agents', methods=['GET'])
@jwt_required()
@handle_api_response
def get_agent():
    """获取智能体列表"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('size', 20, type=int)  # 前端发送的是 'size'
        is_public = request.args.get('is_public', type=bool)

        query = Agent.query

        if is_public:
            # 查询公开的智能体或自己的智能体
            query = query.filter((Agent.is_public == True) | (Agent.user_id == user_id))
        else:
            # 只查询自己的智能体
            query = query.filter(Agent.user_id == user_id)

        pagination = query.order_by(Agent.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)

        items = [agent.to_dict() for agent in pagination.items]

        data = {
            'items': items,
            'total': pagination.total,
            'page': page,
            'size': page_size
        }

        return success(data=data)

    except ValidationError as e:
        raise BusinessException(code=400, message="参数校验失败", error_code="INVALID_PARAMS")

    except Exception as e:
        # 其他异常
        logger.error(f"查询智能体失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message="查询智能体失败", error_code="AGENT_QUERY_FAILED")

@agent_bp.route('/agents/<int:agent_id>', methods=['GET'])
@jwt_required()
@handle_api_response
def get_agent_detail(agent_id):
    """查看智能体详情"""
    try:
        user_id = get_jwt_identity()
        agent = Agent.query.filter_by(id=agent_id).first()

        if agent is None:
            raise BusinessException(code=404, message="智能体不存在", error_code="EMPTY_REQUEST_BODY")

        if agent.user_id != user_id and not agent.is_public:
            raise BusinessException(code=403, message="无权限", error_code="EMPTY_REQUEST_BODY")

        data = agent.to_dict()
        return success(data=data)
    except Exception as e:
        raise BusinessException(message=f"获取失败: {str(e)}")

@agent_bp.route('/agents/<int:agent_id>', methods=['PUT'])
@jwt_required()
@handle_api_response
def update_agent(agent_id):
    """更新智能体"""
    try:
        schema = UpdateAgentSchema()
        data = schema.load(request.get_json())

        user_id = get_jwt_identity()
        agent = Agent.query.filter_by(id=agent_id).first()

        if agent is None:
            raise BusinessException(code=404, message="智能体不存在", error_code="EMPTY_REQUEST_BODY")

        for key, value in data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        db.session.commit()
        return success(data=agent.to_dict(), message="智能体更新成功")

    except ValidationError as err:
        raise BusinessException(message="数据验证失败", code=500, error_code=str(err))
    except Exception as e:
        db.session.rollback()
        raise BusinessException(message=f"更新失败: {str(e)}", code=400, error_code=str(e))

@agent_bp.route('/agents/<int:agent_id>', methods=['DELETE'])
@jwt_required()
@handle_api_response
def delete_agent(agent_id):
    """删除智能体"""
    try:
        user_id = get_jwt_identity()
        agent = Agent.query.filter_by(id=agent_id).first()
        if agent is None:
            raise BusinessException(code=404, message="智能体不存在", error_code="EMPTY_REQUEST_BODY")
        db.session.delete(agent)
        db.session.commit()
        return success(message="智能体删除成功")
    except Exception as e:
        db.session.rollback()
        raise BusinessException(message=f"删除失败: {str(e)}", code=500, error_code=str(e))