"""
Agent 路由模块

本模块定义了智能体(Agent)相关的所有 API 端点，包括智能体的创建、查询、更新和删除操作。

主要功能:
    - 创建智能体: 用户可以创建自定义的 AI 智能体，配置其属性和行为
    - 查询智能体: 支持分页查询、公开/私有筛选
    - 查看智能体详情: 获取特定智能体的完整配置信息
    - 更新智能体: 修改已有智能体的配置和属性
    - 删除智能体: 删除不再需要的智能体

权限控制:
    - 所有端点都需要 JWT 认证 (@jwt_required)
    - 用户只能操作自己创建的智能体
    - 公开智能体可以被所有用户查看

API 端点:
    - POST   /agent/agents           - 创建智能体
    - GET    /agent/agents           - 获取智能体列表
    - GET    /agent/agents/<id>      - 获取智能体详情
    - PUT    /agent/agents/<id>      - 更新智能体
    - DELETE /agent/agents/<id>      - 删除智能体

Example:
    创建智能体请求示例::

        POST /agent/agents
        Authorization: Bearer <access_token>
        Content-Type: application/json

        {
            "name": "客服助手",
            "description": "智能客服机器人",
            "avatar": "🤖",
            "model": "glm-4.5",
            "system_prompt": "你是一个专业的客服助手",
            "temperature": 0.7,
            "is_public": true
        }

    查询智能体列表请求示例::

        GET /agent/agents?page=1&size=20&is_public=true
        Authorization: Bearer <access_token>

Author: Blues AKA Team
"""

import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from blues_aka.Agent.models.agent import Agent
from blues_aka.Agent.schemas import CreateAgentSchema, UpdateAgentSchema
from blues_aka.common.error_codes import ErrorCodes
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
    """
    创建新的智能体

    允许已认证用户创建自定义的 AI 智能体。智能体可以配置各种参数，
    包括名称、描述、模型、系统提示词等。

    请求头:
        Authorization: Bearer <access_token> (必需)
        Content-Type: application/json

    请求体 (JSON):
        name (str): 智能体名称 (必需)
        description (str, optional): 智能体描述
        avatar (str, optional): 智能体头像 (emoji或图标)
        model (str, optional): 使用的语言模型，默认 'glm-4.5'
        system_prompt (str, optional): 系统提示词，定义智能体行为
        prompt_mode (str, optional): 提示词模式，默认 'default'
        tools (list, optional): 智能体可用的工具列表
        temperature (float, optional): 温度参数 (0.0-2.0)，默认 0.7
        max_tokens (int, optional): 最大生成 token 数，默认 20000
        top_p (float, optional): top-p 采样参数，默认 1.0
        is_public (bool, optional): 是否公开，默认 False
        config (dict, optional): 其他自定义配置

    Returns:
        dict: 包含创建的智能体信息的响应
        {
            "code": 200,
            "message": "智能体创建成功",
            "data": {
                "id": 1,
                "name": "客服助手",
                "description": "...",
                "user_id": 123,
                ...
            }
        }

    Raises:
        BusinessException: 参数校验失败 (400)
        BusinessException: 智能体创建失败 (500)

    Example:
        >>> import requests
        >>> response = requests.post(
        ...     'http://localhost:5000/agent/agents',
        ...     headers={'Authorization': f'Bearer {token}'},
        ...     json={
        ...         'name': '编程助手',
        ...         'description': '帮助解决编程问题',
        ...         'model': 'glm-4.5',
        ...         'temperature': 0.7
        ...     }
        ... )
    """
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
        raise BusinessException(
            code=400,
            message="参数校验失败",
            error_code=ErrorCodes.Common.INVALID_PARAMS
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"智能体创建失败: {str(e)}", exc_info=True)
        raise BusinessException(
            code=500,
            message="智能体创建失败",
            error_code=ErrorCodes.Agent.AGENT_CREATION_FAILED
        )

@agent_bp.route('/agents', methods=['GET'])
@jwt_required()
@handle_api_response
def get_agent():
    """
    获取智能体列表

    支持分页查询和筛选功能，可以根据是否公开来过滤智能体。
    用户可以查看所有公开的智能体和自己创建的所有智能体。

    请求头:
        Authorization: Bearer <access_token> (必需)

    查询参数:
        page (int, optional): 页码，默认 1
        size (int, optional): 每页数量，默认 20
        is_public (bool, optional):
            - true: 只查询公开智能体
            - false: 只查询自己创建的智能体
            - 不传: 查询公开智能体和自己创建的智能体

    Returns:
        dict: 包含智能体列表和分页信息的响应
        {
            "code": 200,
            "data": {
                "items": [
                    {
                        "id": 1,
                        "name": "客服助手",
                        "description": "...",
                        "is_public": true,
                        ...
                    }
                ],
                "total": 100,
                "page": 1,
                "size": 20
            }
        }

    Raises:
        BusinessException: 参数校验失败 (400)
        BusinessException: 查询失败 (500)

    Example:
        >>> # 查询所有公开智能体
        >>> response = requests.get(
        ...     'http://localhost:5000/agent/agents?is_public=true&page=1&size=20',
        ...     headers={'Authorization': f'Bearer {token}'}
        ... )
        >>>
        >>> # 查询自己的智能体
        >>> response = requests.get(
        ...     'http://localhost:5000/agent/agents?is_public=false',
        ...     headers={'Authorization': f'Bearer {token}'}
        ... )
    """
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
        raise BusinessException(
            code=400,
            message="参数校验失败",
            error_code=ErrorCodes.Common.INVALID_PARAMS
        )

    except Exception as e:
        # 其他异常
        logger.error(f"查询智能体失败: {str(e)}", exc_info=True)
        raise BusinessException(
            code=500,
            message="查询智能体失败",
            error_code=ErrorCodes.Agent.AGENT_QUERY_FAILED
        )

@agent_bp.route('/agents/<int:agent_id>', methods=['GET'])
@jwt_required()
@handle_api_response
def get_agent_detail(agent_id):
    """
    获取智能体详情

    根据智能体ID获取特定智能体的完整配置信息。
    用户可以查看自己创建的智能体和所有公开的智能体。

    请求头:
        Authorization: Bearer <access_token> (必需)

    URL 参数:
        agent_id (int): 智能体ID (必需)

    Returns:
        dict: 包含智能体详细信息的响应
        {
            "code": 200,
            "data": {
                "id": 1,
                "name": "客服助手",
                "description": "智能客服机器人",
                "avatar": "🤖",
                "model": "glm-4.5",
                "system_prompt": "...",
                "temperature": 0.7,
                "max_tokens": 20000,
                "is_public": true,
                "user_id": 123,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                ...
            }
        }

    Raises:
        BusinessException: 智能体不存在 (404)
        BusinessException: 无权限访问该智能体 (403)

    Example:
        >>> response = requests.get(
        ...     'http://localhost:5000/agent/agents/123',
        ...     headers={'Authorization': f'Bearer {token}'}
        ... )
        >>> agent_detail = response.json()['data']
    """
    try:
        user_id = get_jwt_identity()
        agent = Agent.query.filter_by(id=agent_id).first()

        if agent is None:
            raise BusinessException(
                code=404,
                message="智能体不存在",
                error_code=ErrorCodes.Agent.AGENT_NOT_FOUND
            )

        if agent.user_id != user_id and not agent.is_public:
            raise BusinessException(
                code=403,
                message="无权限",
                error_code=ErrorCodes.Agent.AGENT_ACCESS_DENIED
            )

        data = agent.to_dict()
        return success(data=data)
    except Exception as e:
        raise BusinessException(message=f"获取失败: {str(e)}")


@agent_bp.route('/agents/<int:agent_id>', methods=['PUT'])
@jwt_required()
@handle_api_response
def update_agent(agent_id):
    """
    更新智能体信息

    允许智能体的创建者修改智能体的配置和属性。
    只能更新自己创建的智能体，不能更新其他用户的智能体。

    请求头:
        Authorization: Bearer <access_token> (必需)
        Content-Type: application/json

    URL 参数:
        agent_id (int): 智能体ID (必需)

    请求体 (JSON):
        name (str, optional): 智能体名称
        description (str, optional): 智能体描述
        avatar (str, optional): 智能体头像
        model (str, optional): 使用的语言模型
        system_prompt (str, optional): 系统提示词
        prompt_mode (str, optional): 提示词模式
        tools (list, optional): 可用工具列表
        temperature (float, optional): 温度参数
        max_tokens (int, optional): 最大 token 数
        top_p (float, optional): top-p 采样参数
        is_public (bool, optional): 是否公开
        config (dict, optional): 自定义配置

    Returns:
        dict: 包含更新后智能体信息的响应
        {
            "code": 200,
            "message": "智能体更新成功",
            "data": {
                "id": 1,
                "name": "客服助手",
                ...
            }
        }

    Raises:
        BusinessException: 智能体不存在 (404)
        BusinessException: 参数校验失败 (400)
        BusinessException: 更新失败 (500)

    Example:
        >>> response = requests.put(
        ...     'http://localhost:5000/agent/agents/123',
        ...     headers={'Authorization': f'Bearer {token}'},
        ...     json={
        ...         'name': '新的名称',
        ...         'description': '更新后的描述',
        ...         'temperature': 0.8
        ...     }
        ... )
    """
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
            # 使用 warning 级别记录业务逻辑上的"未找到"，这通常不是系统错误，但需要关注
            logger.warning(f"智能体不存在, ID: {agent_id}, 用户ID: {user_id}")
            raise BusinessException(
                code=404,
                message="智能体不存在",
                error_code=ErrorCodes.Agent.AGENT_NOT_FOUND
            )

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
        raise BusinessException(
            message="数据验证失败",
            code=400,
            error_code=ErrorCodes.Common.VALIDATION_ERROR
        )
    except Exception as e:
        db.session.rollback()
        # 记录未捕获的系统异常，exc_info=True 会自动打印堆栈跟踪，这对调试至关重要
        logger.error(f"更新智能体失败, ID: {agent_id}, 错误信息: {str(e)}", exc_info=True)
        raise BusinessException(
            message=f"更新失败: {str(e)}",
            code=500,
            error_code=ErrorCodes.Agent.AGENT_UPDATE_FAILED
        )


@agent_bp.route('/agents/<int:agent_id>', methods=['DELETE'])
@jwt_required()
@handle_api_response
def delete_agent(agent_id):
    """
    删除智能体

    永久删除指定的智能体。只能删除自己创建的智能体。
    注意：删除操作不可恢复，请谨慎使用。

    请求头:
        Authorization: Bearer <access_token> (必需)

    URL 参数:
        agent_id (int): 智能体ID (必需)

    Returns:
        dict: 删除成功的响应
        {
            "code": 200,
            "message": "智能体删除成功"
        }

    Raises:
        BusinessException: 智能体不存在 (404)
        BusinessException: 删除失败 (500)

    Note:
        - 删除智能体会同时删除其配置和关联数据
        - 删除操作不可逆，请确认后再执行
        - 如果智能体正在被其他用户使用，删除可能会影响这些用户

    Example:
        >>> response = requests.delete(
        ...     'http://localhost:5000/agent/agents/123',
        ...     headers={'Authorization': f'Bearer {token}'}
        ... )
        >>> if response.status_code == 200:
        ...     print("智能体删除成功")
    """
    try:
        user_id = get_jwt_identity()
        agent = Agent.query.filter_by(id=agent_id).first()
        if agent is None:
            raise BusinessException(
                code=404,
                message="智能体不存在",
                error_code=ErrorCodes.Agent.AGENT_NOT_FOUND
            )
        db.session.delete(agent)
        db.session.commit()
        return success(message="智能体删除成功")
    except Exception as e:
        db.session.rollback()
        raise BusinessException(
            message=f"删除失败: {str(e)}",
            code=500,
            error_code=ErrorCodes.Agent.AGENT_DELETE_FAILED
        )