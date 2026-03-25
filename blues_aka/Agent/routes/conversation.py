"""
对话路由模块

本模块提供对话管理相关的 API 接口，包括：

- 对话的创建、查询、更新、删除和归档
- RAG（检索增强生成）知识库管理
- 文档上传和索引管理
- 支持的文件格式查询

主要功能：
    1. 对话管理
       - 创建新对话（支持关联智能体）
       - 获取对话列表（支持分页和状态过滤）
       - 获取对话详情
       - 更新对话信息（标题、描述、关联智能体）
       - 软删除对话
       - 归档对话

    2. RAG 知识库管理
       - 列出所有可用的知识库索引
       - 获取知识库索引详情
       - 创建新的知识库（上传文档并建立索引）
       - 删除知识库索引
       - 向现有知识库添加新文档
       - 切换对话的 RAG 模式

    3. 文档处理
       - 支持多种文档格式（PDF、TXT、MD、HTML、JSON）
       - 自动文档分块和向量化
       - 文件大小和格式验证

支持的文件格式：
    - .pdf: PDF 文档
    - .txt: 纯文本文件
    - .md: Markdown 文档
    - .html: HTML 网页
    - .json: JSON 数据文件

文件大小限制：
    - 最大 100MB

异常处理：
    - 使用统一的异常码体系
    - 所有异常都通过 Exceptions 辅助类抛出
    - 自动记录错误日志

Author: Blues AKA Team
"""

import json
import logging
import os
import tempfile
import uuid
from gc import enable
from pathlib import Path
from werkzeug.utils import secure_filename

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from blues_aka.Agent.models.agent import Agent
from blues_aka.Agent.models.conversation import Conversation
from blues_aka.Agent.schemas import CreateConversationSchema
from blues_aka.common.exception import BusinessException
from blues_aka.common.exceptions import Exceptions, E
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.rag.index_manager import IndexManager
from blues_aka.rag.loader import load_document, load_documents_from_paths, get_supported_extensions
from blues_aka.rag.splitters import split_documents
from blues_aka.rag.embeddings import get_embeddings
from blues_aka.extensions import db
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)
conversation_bp = Blueprint('conversation', __name__, url_prefix='/conversation')

# 允许上传的文件扩展名
ALLOWED_EXTENSIONS = {ext[1:] for ext in get_supported_extensions().keys()}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

@conversation_bp.route('/conversations', methods=['POST'])
@jwt_required()
@handle_api_response
def create_conversation():
    """
    创建新对话

    创建一个新的对话，可以选择关联到现有的智能体。如果关联了智能体，
    对话将使用该智能体的配置（包括模型、系统提示词、RAG 配置等）。

    请求方法: POST
    认证要求: 需要 JWT Token

    请求体 (JSON):
        title (str): 对话标题，必填
        agent_id (int): 智能体 ID，可选
        description (str): 对话描述，可选
        model (str): 直接指定使用的模型，可选（与 agent_id 二选一）

    响应格式 (JSON):
        {
            "code": 200,
            "message": "创建成功",
            "data": {
                "id": 1,
                "title": "我的对话",
                "description": "对话描述",
                "user_id": 1,
                "agent_id": 1,
                "model": "glm-4.5",
                "status": "active",
                "message_count": 0,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "last_message_at": null,
                "agent": {...}  # 智能体信息（如果关联）
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 验证请求参数
        3. 如果指定了 agent_id，验证智能体存在且用户有权访问
        4. 创建对话记录
        5. 返回对话详情（包含智能体信息）

    权限说明:
        - 用户可以创建自己的对话
        - 只能关联自己创建的或公开的智能体
        - 未关联智能体的对话使用指定的默认模型

    异常处理:
        - 300101: 智能体不存在或无权访问
        - 100001: 数据验证失败
        - 400201: 对话创建失败

    Returns:
        dict: 包含创建的对话对象的响应对象

    Raises:
        Exceptions.Agent.agent_not_found: 智能体不存在或无权访问
        Exceptions.Common.invalid_params: 数据验证失败
        Exceptions.Conversation.conversation_creation_failed: 对话创建失败
    """
    try:
        schema = CreateConversationSchema()
        data = schema.load(request.json)
        user_id = get_jwt_identity()

        if data.get('agent_id'):
            agent = Agent.query.filter_by(id=data['agent_id']).first()
            if not agent or (agent.user_id != user_id and not agent.is_public):
                raise Exceptions.Agent.agent_not_found("智能体不存在或无权访问")

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
        raise Exceptions.Common.invalid_params("数据验证失败")

    except Exception as e:
        db.session.rollback()
        raise Exceptions.Conversation.conversation_creation_failed(str(e))

@conversation_bp.route('/conversations', methods=['GET'])
@jwt_required()
@handle_api_response
def get_conversations():
    """
    获取对话列表

    查询当前用户的对话列表，支持分页和状态过滤。对话按最后消息时间倒序排列。

    请求方法: GET
    认证要求: 需要 JWT Token

    查询参数:
        page (int): 页码，可选，默认为 1
        size (int): 每页数量，可选，默认为 20
        status (str): 对话状态，可选，默认为 'active'
                    - 'active': 活跃对话
                    - 'archived': 已归档对话
                    - 'deleted': 已删除对话

    响应格式 (JSON):
        {
            "code": 200,
            "message": "对话查询成功",
            "data": {
                "items": [
                    {
                        "id": 1,
                        "title": "对话标题",
                        "description": "对话描述",
                        "status": "active",
                        "message_count": 10,
                        "last_message_at": "2024-01-01T00:00:00",
                        "agent": {...}  # 智能体信息
                    },
                    ...
                ],
                "total": 100,        # 总记录数
                "page": 1,           # 当前页码
                "size": 20           # 每页数量
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 获取分页参数和状态过滤参数
        3. 查询用户的对话列表（按状态过滤）
        4. 按最后消息时间倒序排序
        5. 分页返回结果

    排序规则:
        - 按 last_message_at 倒序排列（最新的在前）
        - 没有消息的对话排在最后

    异常处理:
        - 400103: 获取对话列表失败

    Returns:
        dict: 包含对话列表的响应对象，包含分页信息

    Raises:
        Exceptions.Conversation.conversation_list_failed: 获取对话列表失败
    """
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        status = request.args.get('status', 'active')

        # 使用 eager loading 避免 N+1 查询问题
        query = Conversation.query.options(
            joinedload(Conversation.agent)
        ).filter_by(user_id=user_id, status=status)

        pagination = query.order_by(Conversation.last_message_at.desc().nullslast()).paginate(page=page, per_page=size, error_out=False)

        items = [conversation.to_dict(include_agent = True) for conversation in pagination.items]

        data = {
            'items': items,
            'total': pagination.total,
            'page': page,
            'size': size,
        }

        return success(data=data, message="对话查询成功")

    except Exception as e:
        raise Exceptions.Conversation.conversation_list_failed(str(e))

@conversation_bp.route('/conversations/<int:conversation_id>', methods=['GET'])
@jwt_required()
@handle_api_response
def get_conversation(conversation_id):
    """
    获取对话详情

    根据对话 ID 查询指定对话的完整信息，包括关联的智能体信息。

    请求方法: GET
    认证要求: 需要 JWT Token

    路由参数:
        conversation_id (int): 对话 ID

    响应格式 (JSON):
        {
            "code": 200,
            "message": "操作成功",
            "data": {
                "id": 1,
                "title": "我的对话",
                "description": "对话描述",
                "user_id": 1,
                "agent_id": 1,
                "model": "glm-4.5",
                "status": "active",
                "message_count": 10,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "last_message_at": "2024-01-01T01:00:00",
                "agent": {...}  # 智能体信息（如果关联）
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 根据 conversation_id 和 user_id 查询对话
        3. 验证对话是否存在
        4. 返回对话详情（包含智能体信息）

    权限说明:
        - 用户只能查询自己创建的对话
        - 包含完整的对话信息，包括关联的智能体详情

    异常处理:
        - 400202: 对话不存在或无权访问
        - 400104: 获取对话详情失败

    Returns:
        dict: 包含对话详情的响应对象

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在或无权访问
        Exceptions.Conversation.conversation_query_failed: 获取对话详情失败
    """
    try:
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise Exceptions.Conversation.conversation_not_found()

        data = conversation.to_dict(include_agent = True)

        return success(data=data)

    except Exception as e:
        raise Exceptions.Conversation.conversation_query_failed(str(e))

@conversation_bp.route('/conversations/<int:conversation_id>', methods=['PUT'])
@jwt_required()
@handle_api_response
def update_conversation(conversation_id):
    """
    更新对话

    更新指定对话的信息，包括标题、描述和关联的智能体。
    可以更新部分字段，未提供的字段保持不变。

    请求方法: PUT
    认证要求: 需要 JWT Token

    路由参数:
        conversation_id (int): 对话 ID

    请求体 (JSON):
        title (str): 对话标题，可选
        description (str): 对话描述，可选
        agent_id (int): 智能体 ID，可选（设置为 null 可取消关联）

    响应格式 (JSON):
        {
            "code": 200,
            "message": "更新成功",
            "data": {
                "id": 1,
                "title": "更新后的标题",
                "description": "更新后的描述",
                "user_id": 1,
                "agent_id": 2,
                "model": "glm-4.5",
                "status": "active",
                "message_count": 10,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T02:00:00",
                "last_message_at": "2024-01-01T01:00:00",
                "agent": {...}  # 更新后的智能体信息
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 根据 conversation_id 和 user_id 查询对话
        3. 验证对话是否存在
        4. 更新请求中提供的字段：
           - 如果提供 title，更新对话标题
           - 如果提供 description，更新对话描述
           - 如果提供 agent_id：
             * 如果 agent_id 不为空，验证智能体存在且用户有权访问
             * 如果 agent_id 为 null，取消与智能体的关联
        5. 提交数据库事务
        6. 返回更新后的对话详情

    权限说明:
        - 用户只能更新自己创建的对话
        - 只能关联自己创建的或公开的智能体
        - 可以取消与智能体的关联（设置 agent_id 为 null）

    异常处理:
        - 400202: 对话不存在或无权访问
        - 300101: 智能体不存在或无权访问
        - 400203: 对话更新失败

    Returns:
        dict: 包含更新后对话对象的响应对象

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在或无权访问
        Exceptions.Agent.agent_not_found: 智能体不存在或无权访问
        Exceptions.Conversation.conversation_update_failed: 对话更新失败
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise Exceptions.Conversation.conversation_not_found()

        # 更新标题
        if data.get('title'):
            conversation.title = data.get('title')

        # 更新描述
        if data.get('description'):
            conversation.description = data.get('description')

        # 更新智能体
        if 'agent_id' in data:
            agent_id = data.get('agent_id')
            if agent_id:
                # 验证智能体是否存在且用户有权访问
                agent = Agent.query.filter_by(id=agent_id).first()
                if not agent or (agent.user_id != user_id and not agent.is_public):
                    raise Exceptions.Agent.agent_not_found("智能体不存在或无权访问")
                conversation.agent_id = agent_id
            else:
                # 允许设置为空（使用默认模型）
                conversation.agent_id = None

        db.session.commit()

        return success(data=conversation.to_dict(include_agent=True), message="更新成功")

    except Exception as e:
        db.session.rollback()
        raise Exceptions.Conversation.conversation_update_failed(str(e))

@conversation_bp.route('/conversations/<int:conversation_id>', methods=['DELETE'])
@jwt_required()
@handle_api_response
def delete_conversation(conversation_id):
    """
    删除对话

    软删除指定的对话。对话不会被物理删除，而是将状态标记为 "deleted"。
    已删除的对话不会在默认的对话列表中显示，但仍可以通过指定 status="deleted" 查询。

    请求方法: DELETE
    认证要求: 需要 JWT Token

    路由参数:
        conversation_id (int): 对话 ID

    响应格式 (JSON):
        {
            "code": 200,
            "message": "删除成功！",
            "data": null
        }

    业务逻辑:
        1. 验证用户身份
        2. 根据 conversation_id 和 user_id 查询对话
        3. 验证对话是否存在
        4. 调用对话的 delete_soft() 方法进行软删除
        5. 提交数据库事务
        6. 返回成功消息

    软删除说明:
        - 对话状态从 "active" 或 "archived" 变为 "deleted"
        - 对话及其消息仍然保留在数据库中
        - 可以通过 status="deleted" 查询已删除的对话
        - 管理员可以在后台恢复已删除的对话（如果实现该功能）

    权限说明:
        - 用户只能删除自己创建的对话
        - 删除操作不可撤销（除非管理员恢复）

    异常处理:
        - 400202: 对话不存在或无权访问
        - 400204: 对话删除失败

    Returns:
        dict: 成功响应对象

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在或无权访问
        Exceptions.Conversation.conversation_delete_failed: 对话删除失败
    """
    try:
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise Exceptions.Conversation.conversation_not_found()

        conversation.delete_soft()
        db.session.commit()
        return success(message="删除成功！")

    except Exception as e:
        db.session.rollback()
        raise Exceptions.Conversation.conversation_delete_failed(str(e))

@conversation_bp.route('/conversations/<int:conversation_id>/archive', methods=['PATCH'])
@jwt_required()
@handle_api_response
def archive_conversation(conversation_id):
    """
    归档对话

    将指定的对话标记为归档状态。归档的对话不会在活跃对话列表中显示，
    但仍然可以通过指定 status="archived" 查询和访问。

    请求方法: PATCH
    认证要求: 需要 JWT Token

    路由参数:
        conversation_id (int): 对话 ID

    响应格式 (JSON):
        {
            "code": 200,
            "message": "归档成功！",
            "data": null
        }

    业务逻辑:
        1. 验证用户身份
        2. 根据 conversation_id 和 user_id 查询对话
        3. 验证对话是否存在
        4. 调用对话的 archive() 方法将状态标记为归档
        5. 提交数据库事务
        6. 返回成功消息

    归档说明:
        - 对话状态从 "active" 变为 "archived"
        - 归档的对话不会在默认的对话列表（status="active"）中显示
        - 可以通过 status="archived" 查询已归档的对话
        - 归档的对话仍然可以继续使用
        - 可以通过更新对话状态取消归档（如果实现该功能）

    使用场景:
        - 将不常用但需要保留的对话归档
        - 清理活跃对话列表
        - 对话已完成但需要保留记录

    权限说明:
        - 用户只能归档自己创建的对话
        - 归档操作可以撤销（通过更新对话状态）

    异常处理:
        - 400202: 对话不存在或无权访问
        - 400203: 对话归档失败

    Returns:
        dict: 成功响应对象

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在或无权访问
        Exceptions.Conversation.conversation_update_failed: 对话归档失败
    """
    try:
        user_id = get_jwt_identity()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise Exceptions.Conversation.conversation_not_found()

        conversation.archive()
        db.session.commit()
        return success(message="归档成功！")

    except Exception as e:
        db.session.rollback()
        raise Exceptions.Conversation.conversation_update_failed(str(e))

@conversation_bp.route('/conversations/<int:conversation_id>/rag', methods=['PATCH'])
@jwt_required()
@handle_api_response
def toggle_rag_mode(conversation_id):
    """
    切换对话关联的智能体的 RAG 模式

    更新对话关联的智能体的 RAG（检索增强生成）配置，包括启用/禁用 RAG、
    关联知识库索引和配置检索参数。

    请求方法: PATCH
    认证要求: 需要 JWT Token

    路由参数:
        conversation_id (int): 对话 ID

    请求体 (JSON):
        enable_rag (bool): 是否启用 RAG，必填
        rag_index_name (str): 知识库索引名称，可选
        rag_config (dict): RAG 检索配置，可选
            - top_k (int): 检索的文档数量，默认 5
            - score_threshold (float): 相似度阈值，默认 0.7
            - search_type (str): 检索类型，默认 "similarity"
            - 其他自定义检索参数

    响应格式 (JSON):
        {
            "code": 200,
            "message": "RAG配置已更新",
            "data": {
                "id": 1,
                "title": "我的对话",
                "agent": {
                    "id": 1,
                    "enable_rag": true,
                    "rag_index_name": "my_knowledge_base",
                    "rag_config": "{...}"
                }
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 根据 conversation_id 和 user_id 查询对话
        3. 验证对话是否存在
        4. 验证对话是否关联了智能体（未关联智能体的对话无法配置 RAG）
        5. 更新智能体的 RAG 配置：
           - enable_rag: 是否启用 RAG 功能
           - rag_index_name: 关联的知识库索引名称
           - rag_config: JSON 格式的检索配置参数
        6. 提交数据库事务
        7. 返回更新后的对话详情（包含智能体信息）

    RAG 模式说明:
        - RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术
        - 启用 RAG 后，智能体在回答问题时会先从知识库中检索相关文档
        - 检索到的文档会作为上下文提供给模型，提高回答的准确性
        - 可以针对每个对话独立配置 RAG 参数
        - 智能体必须有对应的 knowledge base 索引才能启用 RAG

    配置参数说明:
        - enable_rag: true 启用 RAG，false 禁用 RAG
        - rag_index_name: 要使用的知识库索引名称（必须已创建）
        - rag_config: 检索参数配置，包括：
          * top_k: 返回最相关的 K 个文档片段
          * score_threshold: 相似度分数阈值，低于此值的文档不会被使用
          * search_type: "similarity"（相似度）、"mmr"（多样性）等

    权限说明:
        - 用户只能配置自己创建的对话的 RAG 模式
        - 对话必须关联智能体才能配置 RAG
        - 使用的知识库索引必须存在

    异常处理:
        - 400202: 对话不存在或无权访问
        - 100001: 该对话未关联智能体，无法配置 RAG
        - 500000: RAG 配置更新失败

    Returns:
        dict: 包含更新后对话对象的响应对象

    Raises:
        Exceptions.Conversation.conversation_not_found: 对话不存在或无权访问
        Exceptions.Common.invalid_params: 该对话未关联智能体，无法配置 RAG
        Exceptions.Common.internal_server_error: RAG 配置更新失败
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise Exceptions.Conversation.conversation_not_found()

        if not conversation.agent:
            raise Exceptions.Common.invalid_params("该对话未关联智能体，无法配置RAG")

        enable_rag = data.get('enable_rag', False)
        rag_index_name = data.get('rag_index_name')
        rag_config = data.get('rag_config', {})

        # 更新 Agent 的 RAG 配置
        if hasattr(conversation.agent, 'enable_rag'):
            conversation.agent.enable_rag = enable_rag
        if hasattr(conversation.agent, 'rag_index_name'):
            conversation.agent.rag_index_name = rag_index_name
        if hasattr(conversation.agent, 'rag_config'):
            conversation.agent.rag_config = json.dumps(rag_config) if rag_config else None

        db.session.commit()
        return success(data=conversation.to_dict(include_agent=True), message="RAG配置已更新")

    except Exception as e:
        db.session.rollback()
        raise Exceptions.Common.internal_server_error(str(e))

@conversation_bp.route('/rag/indexes', methods=['GET'])
@jwt_required()
@handle_api_response
def list_rag_indexes():
    """
    获取 RAG 知识库索引列表

    查询系统中所有可用的 RAG 知识库索引，返回索引名称、描述、文档数量等基本信息。

    请求方法: GET
    认证要求: 需要 JWT Token

    查询参数: 无

    响应格式 (JSON):
        {
            "code": 200,
            "message": "获取索引列表成功",
            "data": [
                {
                    "name": "my_knowledge_base",
                    "description": "我的知识库",
                    "doc_count": 100,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T01:00:00"
                },
                {
                    "name": "product_docs",
                    "description": "产品文档",
                    "doc_count": 250,
                    "created_at": "2024-01-02T00:00:00",
                    "updated_at": "2024-01-02T02:00:00"
                }
            ]
        }

    业务逻辑:
        1. 验证用户身份
        2. 创建 IndexManager 实例
        3. 调用 list_indexes() 方法获取所有索引
        4. 返回索引列表（包含索引名称、描述、文档数量等信息）

    索引信息说明:
        - name: 索引名称，用于唯一标识知识库
        - description: 索引描述，说明知识库的用途和内容
        - doc_count: 知识库中的文档片段数量
        - created_at: 索引创建时间
        - updated_at: 索引最后更新时间

    使用场景:
        - 在创建或配置智能体时选择要关联的知识库
        - 查看可用的知识库资源
        - 管理和维护知识库

    权限说明:
        - 所有已认证用户都可以查询索引列表
        - 返回的索引列表包含系统中的所有索引

    异常处理:
        - 500301: 获取索引列表失败

    Returns:
        dict: 包含索引列表的响应对象

    Raises:
        Exceptions.RAG.retrieval_failed: 获取索引列表失败
    """
    try:
        index_manager = IndexManager()
        indexes = index_manager.list_indexes()
        return success(data=indexes, message="获取索引列表成功")

    except Exception as e:
        logger.error(f"获取索引列表失败: {str(e)}", exc_info=True)
        raise Exceptions.RAG.retrieval_failed(str(e))

@conversation_bp.route('/rag/indexes/<string:index_name>', methods=['GET'])
@jwt_required()
@handle_api_response
def get_rag_index_info(index_name):
    """
    获取 RAG 知识库索引详情

    查询指定知识库索引的详细信息，包括索引配置、文档统计、元数据等。

    请求方法: GET
    认证要求: 需要 JWT Token

    路由参数:
        index_name (str): 知识库索引名称

    响应格式 (JSON):
        {
            "code": 200,
            "message": "获取索引详情成功",
            "data": {
                "name": "my_knowledge_base",
                "description": "我的知识库",
                "doc_count": 100,
                "vector_count": 500,
                "dimension": 1024,
                "metadata": {
                    "chunk_size": 512,
                    "chunk_overlap": 50,
                    "splitter_type": "recursive"
                },
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T01:00:00"
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 创建 IndexManager 实例
        3. 调用 get_index_info(index_name) 方法获取索引详情
        4. 验证索引是否存在
        5. 返回索引详细信息

    索引详情说明:
        - name: 索引名称
        - description: 索引描述
        - doc_count: 原始文档数量
        - vector_count: 向量片段总数（一个文档可能被分成多个片段）
        - dimension: 向量维度（由嵌入模型决定）
        - metadata: 索引元数据，包括：
          * chunk_size: 文档分块大小
          * chunk_overlap: 分块重叠大小
          * splitter_type: 分块器类型
        - created_at: 索引创建时间
        - updated_at: 索引最后更新时间

    使用场景:
        - 查看知识库的详细配置和统计信息
        - 验证索引是否正常工作
        - 了解索引的容量和性能指标
        - 在配置智能体时查看索引详情

    权限说明:
        - 所有已认证用户都可以查询索引详情
        - 只能查询已存在的索引

    异常处理:
        - 500303: 知识库索引不存在
        - 500301: 获取索引详情失败

    Returns:
        dict: 包含索引详细信息的响应对象

    Raises:
        Exceptions.RAG.knowledge_base_not_found: 知识库索引不存在
        Exceptions.RAG.retrieval_failed: 获取索引详情失败
    """
    try:
        index_manager = IndexManager()
        index_info = index_manager.get_index_info(index_name)

        if not index_info:
            raise Exceptions.RAG.knowledge_base_not_found(f"知识库索引不存在: {index_name}")

        return success(data=index_info, message="获取索引详情成功")

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取索引详情失败: {str(e)}", exc_info=True)
        raise Exceptions.RAG.retrieval_failed(str(e))

@conversation_bp.route('/rag/indexes', methods=['POST'])
@jwt_required()
@handle_api_response
def create_knowledge_base():
    """
    创建知识库

    上传文档文件并创建新的 RAG 知识库索引。支持多种文档格式，
    系统会自动进行文档分块和向量化处理。

    请求方法: POST
    认证要求: 需要 JWT Token

    请求体 (multipart/form-data):
        file (file): 文档文件，必填
            支持的格式：PDF、TXT、MD、HTML、JSON
            最大文件大小：100MB
        index_name (str): 索引名称，必填
            只能包含字母、数字、下划线和中划线
            用于唯一标识知识库
        description (str): 索引描述，可选
            默认值为 "{文件名} 的知识库"
        chunk_size (int): 分块大小，可选
            单个文本块的字符数
            默认使用系统配置
        chunk_overlap (int): 分块重叠，可选
            相邻文本块之间的重叠字符数
            默认使用系统配置
        splitter_type (str): 分块器类型，可选
            支持的类型：recursive（递归分块，默认）
            默认值为 "recursive"
        overwrite (bool): 是否覆盖已存在的索引，可选
            如果为 true，覆盖同名索引
            如果为 false（默认），同名索引会报错

    响应格式 (JSON):
        {
            "code": 200,
            "message": "知识库创建成功",
            "data": {
                "index_name": "my_knowledge_base",
                "filename": "document.pdf",
                "original_chunks": 10,
                "total_chunks": 150,
                "index_info": {
                    "name": "my_knowledge_base",
                    "description": "我的知识库",
                    "doc_count": 10,
                    "vector_count": 150
                }
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 验证上传的文件：
           - 检查文件是否存在
           - 检查文件名是否有效
           - 检查文件扩展名是否支持
           - 检查文件大小是否超过限制
        3. 验证和获取参数：
           - 验证索引名称格式
           - 获取分块配置参数
        4. 保存临时文件
        5. 加载文档内容：
           - 根据文件类型使用对应的加载器
           - 提取文档文本和元数据
        6. 文档分块处理：
           - 使用指定的分块器进行文本分块
           - 记录分块统计信息
        7. 生成向量嵌入：
           - 加载嵌入模型
           - 为所有文本块生成向量
        8. 创建向量索引：
           - 检查索引是否已存在
           - 创建或覆盖向量索引
        9. 清理临时文件
        10. 返回创建结果

    文档处理流程:
        1. 文档加载：将文档转换为文本格式
        2. 文本分块：将长文本分成多个小块
        3. 向量化：为每个文本块生成向量表示
        4. 索引创建：将向量存储到向量数据库中

    支持的文件格式:
        - PDF (.pdf): Adobe PDF 文档
        - TXT (.txt): 纯文本文件
        - Markdown (.md): Markdown 文档
        - HTML (.html): HTML 网页
        - JSON (.json): JSON 数据文件

    分块配置说明:
        - chunk_size: 控制文本块的大小，影响检索的粒度
          * 较小的值：更精细的检索，但块数更多
          * 较大的值：更宽泛的检索，但可能包含无关信息
        - chunk_overlap: 相邻块之间的重叠，保证上下文连续性
          * 通常设置为 chunk_size 的 10-20%
        - splitter_type: 分块算法
          * recursive: 递归分块，尝试不同分隔符（推荐）

    权限说明:
        - 所有已认证用户都可以创建知识库
        - 索引名称必须唯一（除非设置 overwrite=true）
        - 创建的索引可以被所有用户使用

    异常处理:
        - 100004: 未上传文件
        - 100001: 文件名为空或索引名称格式错误
        - 500302: 文件格式不支持或文件过大
        - 500304: 知识库索引已存在（未设置 overwrite）
        - 500305: 创建知识库失败

    Returns:
        dict: 包含创建结果的响应对象

    Raises:
        Exceptions.Common.empty_request_body: 未上传文件
        Exceptions.Common.invalid_params: 文件名为空或索引名称格式错误
        Exceptions.RAG.invalid_document_format: 文件格式不支持
        Exceptions.RAG.document_too_large: 文件过大
        Exceptions.RAG.document_already_exists: 知识库索引已存在
        Exceptions.RAG.knowledge_base_creation_failed: 创建知识库失败
    """
    try:
        user_id = get_jwt_identity()

        # 检查是否有文件
        if 'file' not in request.files:
            logger.error("未上传文件 - request.files 中没有 'file' 键")
            raise Exceptions.Common.empty_request_body("未上传文件")

        file = request.files['file']
        logger.info(f"接收到的文件对象: {file}, filename: {file.filename}")

        # 检查文件名
        if not file.filename or file.filename == '':
            logger.error("文件名为空")
            raise Exceptions.Common.invalid_params("文件名为空")

        # 检查文件扩展名
        # 先从原始文件名提取扩展名（支持中文文件名）
        # 清理文件名：去除首尾空格和换行符
        cleaned_filename = file.filename.strip() if file.filename else ''
        original_file_ext = Path(cleaned_filename).suffix.lower()
        logger.info(f"原始文件名: {repr(file.filename)}")
        logger.info(f"清理后文件名: {repr(cleaned_filename)}")
        logger.info(f"原始文件扩展名: {repr(original_file_ext)}")
        logger.info(f"ALLOWED_EXTENSIONS内容: {ALLOWED_EXTENSIONS}")

        # 检查文件扩展名是否为空
        if not original_file_ext:
            logger.error(f"文件扩展名为空，原始文件名: {file.filename}")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise Exceptions.RAG.invalid_document_format(f"文件缺少扩展名。支持的类型: {supported}")

        # 检查文件类型是否支持
        file_ext_without_dot = original_file_ext[1:]  # 去掉点号
        logger.info(f"去掉点号的扩展名: '{file_ext_without_dot}', 类型: {type(file_ext_without_dot)}")
        logger.info(f"检查 '{file_ext_without_dot}' in {ALLOWED_EXTENSIONS}: {file_ext_without_dot in ALLOWED_EXTENSIONS}")

        if file_ext_without_dot not in ALLOWED_EXTENSIONS:
            logger.error(f"不支持的文件类型: {original_file_ext} ({file_ext_without_dot})")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise Exceptions.RAG.invalid_document_format(f"不支持的文件类型: {original_file_ext}。支持的类型: {supported}")

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            size_mb = MAX_FILE_SIZE / 1024 / 1024
            raise Exceptions.RAG.document_too_large(f"文件过大，最大支持 {size_mb:.0f}MB")

        # 获取参数
        index_name = request.form.get('index_name')
        if not index_name:
            raise Exceptions.Common.invalid_params("索引名称不能为空")

        # 验证索引名称（只允许字母、数字、下划线、中划线）
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', index_name):
            raise Exceptions.Common.invalid_params("索引名称只能包含字母、数字、下划线和中划线")

        description = request.form.get('description', f"{file.filename} 的知识库")
        chunk_size = int(request.form.get('chunk_size', 0)) or None
        chunk_overlap = int(request.form.get('chunk_overlap', 0)) or None
        splitter_type = request.form.get('splitter_type', 'recursive')
        overwrite = request.form.get('overwrite', 'false').lower() == 'true'

        logger.info(f"用户 {user_id} 开始创建知识库: {index_name}")
        logger.info(f"文件: {file.filename} ({file_size / 1024:.1f} KB)")
        logger.info(f"分块配置: {splitter_type}, chunk_size={chunk_size}, overlap={chunk_overlap}")

        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=original_file_ext) as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name

        try:
            # 加载文档
            logger.info("正在加载文档...")
            documents = load_document(tmp_file_path, add_metadata=True)
            logger.info(f"文档加载完成，共 {len(documents)} 个文档块")

            # 分块处理
            logger.info("正在进行文本分块...")
            chunks = split_documents(
                documents=documents,
                splitter_type=splitter_type,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            logger.info(f"文档分块完成，共 {len(chunks)} 个文本块")

            # 获取嵌入模型
            logger.info("正在加载嵌入模型...")
            embeddings = get_embeddings()

            # 创建索引
            logger.info("正在创建向量索引...")
            index_manager = IndexManager()

            # 检查索引是否已存在
            if index_manager.index_exists(index_name) and not overwrite:
                raise Exceptions.RAG.document_already_exists(f"知识库索引已存在: {index_name}。如要覆盖，请设置 overwrite=true")

            vector_store = index_manager.create_index(
                name=index_name,
                documents=chunks,
                embeddings=embeddings,
                description=description,
                overwrite=overwrite
            )

            logger.info(f"知识库创建成功: {index_name}")

            # 获取索引信息
            index_info = index_manager.get_index_info(index_name)

            return success(
                data={
                    'index_name': index_name,
                    'filename': file.filename,
                    'original_chunks': len(documents),
                    'total_chunks': len(chunks),
                    'index_info': index_info
                },
                message="知识库创建成功"
            )

        finally:
            # 删除临时文件
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"创建知识库失败: {str(e)}", exc_info=True)
        db.session.rollback()
        raise Exceptions.RAG.knowledge_base_creation_failed(f"创建知识库失败: {str(e)}")

@conversation_bp.route('/rag/indexes/<string:index_name>', methods=['DELETE'])
@jwt_required()
@handle_api_response
def delete_knowledge_base(index_name):
    """
    删除知识库

    永久删除指定的知识库索引及其所有向量数据。删除操作不可撤销。

    请求方法: DELETE
    认证要求: 需要 JWT Token

    路由参数:
        index_name (str): 知识库索引名称

    响应格式 (JSON):
        {
            "code": 200,
            "message": "知识库 my_knowledge_base 已删除",
            "data": null
        }

    业务逻辑:
        1. 验证用户身份
        2. 创建 IndexManager 实例
        3. 检查索引是否存在
        4. 调用 delete_index(index_name) 删除索引
        5. 返回成功消息

    删除操作说明:
        - 物理删除：索引及其所有向量数据将被永久删除
        - 不可撤销：删除后无法恢复，除非重新创建和上传文档
        - 级联影响：使用该索引的智能体将无法正常使用 RAG 功能
        - 完全清理：所有相关的向量数据和元数据都会被删除

    使用场景:
        - 删除不再需要的知识库
        - 重新创建知识库前清理旧数据
        - 清理测试数据
        - 释放存储空间

    注意事项:
        - 删除前确保没有智能体正在使用该索引
        - 删除操作不可逆，请谨慎操作
        - 建议在删除前备份重要数据

    权限说明:
        - 所有已认证用户都可以删除知识库
        - 删除操作需要谨慎，建议添加二次确认

    异常处理:
        - 500303: 知识库索引不存在
        - 500306: 删除知识库失败

    Returns:
        dict: 成功响应对象

    Raises:
        Exceptions.RAG.knowledge_base_not_found: 知识库索引不存在
        Exceptions.RAG.knowledge_base_delete_failed: 删除知识库失败
    """
    try:
        user_id = get_jwt_identity()
        logger.info(f"用户 {user_id} 请求删除知识库: {index_name}")

        index_manager = IndexManager()

        # 检查索引是否存在
        if not index_manager.index_exists(index_name):
            raise Exceptions.RAG.knowledge_base_not_found(f"知识库索引不存在: {index_name}")

        # 删除索引
        index_manager.delete_index(index_name)

        logger.info(f"知识库删除成功: {index_name}")
        return success(message=f"知识库 {index_name} 已删除")

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"删除知识库失败: {str(e)}", exc_info=True)
        raise Exceptions.RAG.knowledge_base_delete_failed(f"删除知识库失败: {str(e)}")

@conversation_bp.route('/rag/indexes/<string:index_name>/documents', methods=['POST'])
@jwt_required()
@handle_api_response
def add_documents_to_index(index_name):
    """
    向知识库添加文档

    向现有的知识库索引添加新文档。系统会自动进行文档分块和向量化处理，
    并将新的向量数据追加到现有索引中。

    请求方法: POST
    认证要求: 需要 JWT Token

    路由参数:
        index_name (str): 知识库索引名称

    请求体 (multipart/form-data):
        file (file): 文档文件，必填
            支持的格式：PDF、TXT、MD、HTML、JSON
            最大文件大小：100MB
        chunk_size (int): 分块大小，可选
            单个文本块的字符数
            默认使用索引的配置或系统默认值
        chunk_overlap (int): 分块重叠，可选
            相邻文本块之间的重叠字符数
            默认使用索引的配置或系统默认值
        splitter_type (str): 分块器类型，可选
            支持的类型：recursive（递归分块，默认）
            默认值为 "recursive"

    响应格式 (JSON):
        {
            "code": 200,
            "message": "文档添加成功",
            "data": {
                "index_name": "my_knowledge_base",
                "filename": "new_document.pdf",
                "added_chunks": 50,
                "index_info": {
                    "name": "my_knowledge_base",
                    "doc_count": 15,
                    "vector_count": 200
                }
            }
        }

    业务逻辑:
        1. 验证用户身份
        2. 验证上传的文件：
           - 检查文件是否存在
           - 检查文件名是否有效
           - 检查文件扩展名是否支持
           - 检查文件大小是否超过限制
        3. 检查索引是否存在
        4. 获取分块配置参数（如未指定则使用默认值）
        5. 保存临时文件
        6. 加载文档内容：
           - 根据文件类型使用对应的加载器
           - 提取文档文本和元数据
        7. 文档分块处理：
           - 使用指定的分块器进行文本分块
           - 记录分块统计信息
        8. 生成向量嵌入：
           - 加载嵌入模型
           - 为所有文本块生成向量
        9. 更新向量索引：
           - 将新的向量数据追加到现有索引
           - 更新索引的元数据
        10. 清理临时文件
        11. 返回添加结果

    文档处理流程:
        1. 文档加载：将文档转换为文本格式
        2. 文本分块：将长文本分成多个小块
        3. 向量化：为每个文本块生成向量表示
        4. 索引更新：将向量追加到现有向量数据库中

    更新操作说明:
        - 增量更新：只添加新的文档，不影响现有数据
        - 自动扩展：索引的向量数量会相应增加
        - 原子操作：更新过程是原子的，失败会回滚
        - 元数据更新：索引的文档数量和更新时间会自动更新

    使用场景:
        - 向现有知识库添加新文档
        - 扩充知识库内容
        - 定期更新知识库
        - 多个文档分批上传

    注意事项:
        - 索引必须已存在才能添加文档
        - 新文档会与现有文档一起被检索
        - 重复的文档会被重复索引（需要自行去重）
        - 大量文档可能需要较长的处理时间

    权限说明:
        - 所有已认证用户都可以向知识库添加文档
        - 不限制单个索引的文档数量

    异常处理:
        - 100004: 未上传文件
        - 100001: 文件名为空
        - 500302: 文件格式不支持或文件过大
        - 500303: 知识库索引不存在
        - 500307: 添加文档失败

    Returns:
        dict: 包含添加结果的响应对象

    Raises:
        Exceptions.Common.empty_request_body: 未上传文件
        Exceptions.Common.invalid_params: 文件名为空
        Exceptions.RAG.invalid_document_format: 文件格式不支持
        Exceptions.RAG.document_too_large: 文件过大
        Exceptions.RAG.knowledge_base_not_found: 知识库索引不存在
        Exceptions.RAG.document_upload_failed: 添加文档失败
    """
    try:
        user_id = get_jwt_identity()

        # 检查是否有文件
        if 'file' not in request.files:
            logger.error("未上传文件 - request.files 中没有 'file' 键")
            raise Exceptions.Common.empty_request_body("未上传文件")

        file = request.files['file']
        logger.info(f"接收到的文件对象: {file}, filename: {file.filename}")

        if not file.filename or file.filename == '':
            logger.error("文件名为空")
            raise Exceptions.Common.invalid_params("文件名为空")

        # 检查文件扩展名
        # 先从原始文件名提取扩展名（支持中文文件名）
        # 清理文件名：去除首尾空格和换行符
        cleaned_filename = file.filename.strip() if file.filename else ''
        original_file_ext = Path(cleaned_filename).suffix.lower()

        # 检查文件扩展名是否为空
        if not original_file_ext:
            logger.error(f"文件扩展名为空，原始文件名: {file.filename}")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise Exceptions.RAG.invalid_document_format(f"文件缺少扩展名。支持的类型: {supported}")

        # 检查文件类型是否支持
        file_ext_without_dot = original_file_ext[1:]  # 去掉点号
        if file_ext_without_dot not in ALLOWED_EXTENSIONS:
            logger.error(f"不支持的文件类型: {original_file_ext} ({file_ext_without_dot})")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise Exceptions.RAG.invalid_document_format(f"不支持的文件类型: {original_file_ext}。支持的类型: {supported}")

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            size_mb = MAX_FILE_SIZE / 1024 / 1024
            raise Exceptions.RAG.document_too_large(f"文件过大，最大支持 {size_mb:.0f}MB")

        # 获取参数
        chunk_size = int(request.form.get('chunk_size', 0)) or None
        chunk_overlap = int(request.form.get('chunk_overlap', 0)) or None
        splitter_type = request.form.get('splitter_type', 'recursive')

        logger.info(f"用户 {user_id} 向知识库 {index_name} 添加文档")
        logger.info(f"文件: {file.filename} ({file_size / 1024:.1f} KB)")

        # 检查索引是否存在
        index_manager = IndexManager()
        if not index_manager.index_exists(index_name):
            raise Exceptions.RAG.knowledge_base_not_found(f"知识库索引不存在: {index_name}")

        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=original_file_ext) as tmp_file:
            file.save(tmp_file.name)
            tmp_file_path = tmp_file.name

        try:
            # 加载文档
            logger.info("正在加载文档...")
            documents = load_document(tmp_file_path, add_metadata=True)
            logger.info(f"文档加载完成，共 {len(documents)} 个文档块")

            # 分块处理
            logger.info("正在进行文本分块...")
            chunks = split_documents(
                documents=documents,
                splitter_type=splitter_type,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            logger.info(f"文档分块完成，共 {len(chunks)} 个文本块")

            # 获取嵌入模型
            logger.info("正在加载嵌入模型...")
            embeddings = get_embeddings()

            # 更新索引
            logger.info("正在更新向量索引...")
            vector_store = index_manager.update_index(
                name=index_name,
                documents=chunks,
                embeddings=embeddings
            )

            # 获取更新后的索引信息
            index_info = index_manager.get_index_info(index_name)

            logger.info(f"文档添加成功: {index_name}")

            return success(
                data={
                    'index_name': index_name,
                    'filename': file.filename,
                    'added_chunks': len(chunks),
                    'index_info': index_info
                },
                message="文档添加成功"
            )

        finally:
            # 删除临时文件
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"添加文档失败: {str(e)}", exc_info=True)
        db.session.rollback()
        raise Exceptions.RAG.document_upload_failed(f"添加文档失败: {str(e)}")

@conversation_bp.route('/rag/supported-formats', methods=['GET'])
@handle_api_response
def get_supported_formats():
    """
    获取支持的文件格式列表

    查询系统支持的所有文档格式及其描述信息，用于前端显示和验证。

    请求方法: GET
    认证要求: 不需要认证（公开接口）

    查询参数: 无

    响应格式 (JSON):
        {
            "code": 200,
            "message": "获取支持格式成功",
            "data": {
                "formats": [
                    {
                        "extension": ".pdf",
                        "type": "pdf",
                        "description": "PDF 文档"
                    },
                    {
                        "extension": ".txt",
                        "type": "text",
                        "description": "纯文本文件"
                    },
                    {
                        "extension": ".md",
                        "type": "markdown",
                        "description": "Markdown 文档"
                    },
                    {
                        "extension": ".html",
                        "type": "html",
                        "description": "HTML 网页"
                    },
                    {
                        "extension": ".json",
                        "type": "json",
                        "description": "JSON 数据文件"
                    }
                ],
                "max_file_size_mb": 100
            }
        }

    业务逻辑:
        1. 调用 get_supported_extensions() 获取支持的文件扩展名
        2. 为每种文件类型生成描述信息
        3. 计算最大文件大小（MB）
        4. 返回格式列表和大小限制

    响应字段说明:
        - formats: 支持的文件格式列表
          * extension: 文件扩展名（带点号）
          * type: 文件类型标识符
          * description: 类型的中文描述
        - max_file_size_mb: 最大文件大小（MB）

    使用场景:
        - 前端文件上传组件的格式限制
        - 显示支持的文件类型列表
        - 文件格式验证
        - 用户提示和帮助文档

    支持的文件类型:
        1. PDF 文档 (.pdf)
           - 便携式文档格式
           - 支持文本提取
           - 保留文档格式

        2. 纯文本文件 (.txt)
           - 最简单的文本格式
           - 无格式信息
           - 通用性强

        3. Markdown 文档 (.md)
           - 轻量级标记语言
           - 支持基本格式
           - 适合技术文档

        4. HTML 网页 (.html)
           - 超文本标记语言
           - 支持富文本和链接
           - 自动提取主要内容

        5. JSON 数据文件 (.json)
           - 结构化数据格式
           - 支持嵌套和数组
           - 适合配置和数据

    文件大小限制:
        - 最大文件大小：100MB
        - 超过限制的文件会被拒绝
        - 大文件建议先压缩或分割

    权限说明:
        - 公开接口，无需认证
        - 所有用户都可以访问

    异常处理:
        - 500000: 获取支持格式失败

    Returns:
        dict: 包含支持格式列表的响应对象

    Raises:
        Exceptions.Common.internal_server_error: 获取支持格式失败
    """
    try:
        extensions = get_supported_extensions()
        formats = [
            {
                'extension': ext,
                'type': file_type,
                'description': _get_file_type_description(file_type)
            }
            for ext, file_type in extensions.items()
        ]

        return success(
            data={
                'formats': formats,
                'max_file_size_mb': MAX_FILE_SIZE / 1024 / 1024
            },
            message="获取支持格式成功"
        )

    except Exception as e:
        logger.error(f"获取支持格式失败: {str(e)}", exc_info=True)
        raise Exceptions.Common.internal_server_error(str(e))

def _get_file_type_description(file_type: str) -> str:
    """
    获取文件类型的中文描述

    根据文件类型标识符返回对应的中文描述信息。
    这是一个辅助函数，用于为文件类型提供用户友好的描述。

    参数:
        file_type (str): 文件类型标识符
            支持的类型：
            - 'pdf': PDF 文档
            - 'text': 纯文本文件
            - 'markdown': Markdown 文档
            - 'html': HTML 网页
            - 'json': JSON 数据文件

    返回值:
        str: 文件类型的中文描述
            如果类型未知，返回原始的 file_type 值

    业务逻辑:
        1. 接收文件类型标识符
        2. 在预定义的描述字典中查找对应的中文描述
        3. 如果找到，返回中文描述
        4. 如果未找到，返回原始的类型标识符

    描述映射表:
        - 'pdf' -> 'PDF 文档'
        - 'text' -> '纯文本文件'
        - 'markdown' -> 'Markdown 文档'
        - 'html' -> 'HTML 网页'
        - 'json' -> 'JSON 数据文件'

    使用场景:
        - 在 API 响应中提供文件类型描述
        - 前端显示文件类型信息
        - 用户界面展示支持的格式

    设计说明:
        - 使用字典实现 O(1) 查找效率
        - 对未知类型返回原始值，确保不会抛出异常
        - 集中管理文件类型描述，便于维护

    Returns:
        str: 文件类型的中文描述或原始类型标识符

    Raises:
        无（不会抛出异常）
    """
    descriptions = {
        'pdf': 'PDF 文档',
        'text': '纯文本文件',
        'markdown': 'Markdown 文档',
        'html': 'HTML 网页',
        'json': 'JSON 数据文件'
    }
    return descriptions.get(file_type, file_type)


# ==================== RAG 评估相关 API ====================

@conversation_bp.route('/rag/feedback', methods=['POST'])
@jwt_required()
@handle_api_response
def submit_rag_feedback():
    """提交 RAG 回答的用户反馈
    
    请求体:
    {
        "query": "用户查询",
        "answer": "RAG 生成的回答",
        "feedback": 5,  // 1-5 分
        "conversation_id": 123,  // 可选
        "message_id": 456  // 可选
    }
    
    Returns:
        {
            "success": true,
            "message": "反馈已记录"
        }
    """
    from blues_aka.rag.evaluator import get_rag_evaluator
    from blues_aka.user.models.user import User
    
    data = request.get_json()
    
    # 验证必需字段
    required_fields = ['query', 'answer', 'feedback']
    for field in required_fields:
        if field not in data:
            raise Exceptions.Common.invalid_params(f'缺少必需参数: {field}')
    
    query = data['query']
    answer = data['answer']
    feedback = data['feedback']
    
    # 验证反馈分数
    if not isinstance(feedback, int) or not 1 <= feedback <= 5:
        raise Exceptions.Common.invalid_params('feedback 必须是 1-5 之间的整数')
    
    # 获取当前用户
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # 记录反馈
    evaluator = get_rag_evaluator()
    evaluator.log_rag_feedback(
        query=query,
        answer=answer,
        feedback=feedback,
        context={
            'conversation_id': data.get('conversation_id'),
            'message_id': data.get('message_id'),
            'user_id': user_id
        }
    )
    
    logger.info(f"用户 {user_id} 提交 RAG 反馈: 查询='{query[:30]}...', 反馈={feedback}/5")
    
    return {
        'success': True,
        'message': '反馈已记录，感谢您的反馈！'
    }


@conversation_bp.route('/rag/metrics', methods=['GET'])
@jwt_required()
@handle_api_response
def get_rag_metrics():
    """获取 RAG 性能指标（管理员）"""
    from blues_aka.rag.evaluator import get_rag_evaluator, get_rag_metrics_tracker
    from blues_aka.user.models.user import User

    # 获取当前用户
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)

    # 检查权限（只有管理员可以查看）
    if not current_user.is_admin:
        raise Exceptions.Auth.forbidden('只有管理员可以查看 RAG 指标')

    # 获取查询参数
    return_summary = request.args.get('summary', 'true').lower() == 'true'

    result = {}
    
    # 获取评估摘要
    if return_summary:
        evaluator = get_rag_evaluator()
        result['summary'] = evaluator.get_performance_summary()
    
    # 获取持久化指标
    tracker = get_rag_metrics_tracker()
    result['metrics'] = tracker.get_metrics()
    
    logger.info(f"管理员 {user_id} 查看 RAG 指标")
    
    return result


@conversation_bp.route('/rag/export', methods=['POST'])
@jwt_required()
@handle_api_response
def export_rag_evaluations():
    """导出 RAG 评估数据（管理员）"""
    from blues_aka.rag.evaluator import get_rag_evaluator
    from blues_aka.user.models.user import User
    
    # 获取当前用户
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    # 检查权限
    if not current_user.is_admin:
        raise Exceptions.Auth.forbidden('只有管理员可以导出评估数据')
    
    data = request.get_json() or {}
    file_path = data.get('file_path')
    
    # 导出数据
    evaluator = get_rag_evaluator()
    exported_path = evaluator.export_evaluations(file_path)
    
    logger.info(f"管理员 {user_id} 导出 RAG 评估数据: {exported_path}")
    
    return {
        'success': True,
        'file_path': exported_path,
        'message': '评估数据已导出'
    }
