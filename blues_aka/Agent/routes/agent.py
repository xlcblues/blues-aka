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
            model=data.get('model', 'glm-4.5'),
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

        # 处理 is_public 参数,支持字符串和布尔值
        is_public_param = request.args.get('is_public')
        is_public = None
        if is_public_param is not None:
            # 将字符串转换为布尔值
            if is_public_param.lower() in ['true', '1', 'yes']:
                is_public = True
            elif is_public_param.lower() in ['false', '0', 'no']:
                is_public = False

        logger.info(f"查询智能体列表 - user_id: {user_id}, is_public_param: {is_public_param}, is_public: {is_public}")

        query = Agent.query

        if is_public is True:
            # 查询所有公开的智能体(包含自己的)
            query = query.filter(Agent.is_public == True)
        elif is_public is False:
            # 只查询自己的智能体(不论是否公开)
            query = query.filter(Agent.user_id == user_id)
        else:
            # is_public为None时,查询公开的智能体或自己的智能体
            query = query.filter((Agent.is_public == True) | (Agent.user_id == user_id))

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
        # 记录请求开始，便于追踪请求链路
        logger.info(f"开始处理更新智能体请求, ID: {agent_id}")

        schema = UpdateAgentSchema()
        data = schema.load(request.get_json())

        user_id = get_jwt_identity()

        # 记录数据库查询操作
        logger.info(f"正在查询智能体, ID: {agent_id}, 用户ID: {user_id}")
        agent = Agent.query.filter_by(id=agent_id, user_id=user_id).first()

        if agent is None:
            # 使用 warning 级别记录业务逻辑上的“未找到”，这通常不是系统错误，但需要关注
            logger.warning(f"智能体不存在, ID: {agent_id}, 用户ID: {user_id}")
            raise BusinessException(code=404, message="智能体不存在", error_code="AGENT_NOT_FOUND")

        # 记录即将更新的字段，方便审计
        logger.info(f"准备更新智能体属性, ID: {agent_id}, 更新字段: {list(data.keys())}")
        for key, value in data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)

        db.session.commit()
        logger.info(f"智能体更新成功, ID: {agent_id}")
        return success(data=agent.to_dict(), message="智能体更新成功")

    except ValidationError as err:
        # 记录数据校验失败的详细信息，包含具体的字段错误
        logger.error(f"数据验证失败, ID: {agent_id}, 错误详情: {err.messages}", exc_info=True)
        raise BusinessException(message="数据验证失败", code=500, error_code=str(err))
    except Exception as e:
        db.session.rollback()
        # 记录未捕获的系统异常，exc_info=True 会自动打印堆栈跟踪，这对调试至关重要
        logger.error(f"更新智能体失败, ID: {agent_id}, 错误信息: {str(e)}", exc_info=True)
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