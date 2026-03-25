"""RAG索引管理API路由

提供RAG索引管理的REST API接口,包括:
- 索引列表和详情查询
- 索引健康检查
- 索引版本管理
- 索引增量更新和重建
"""
import logging
from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from blues_aka.common.exceptions import Exceptions
from blues_aka.common.response_handler import handle_api_response
from blues_aka.common.auth import requires_admin
from blues_aka.rag.index_manager import IndexManager
from blues_aka.rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)

rag_index_bp = Blueprint('rag_index', __name__, url_prefix='/rag/index')


@rag_index_bp.route('/list', methods=['GET'])
@jwt_required()
@handle_api_response
def list_indexes():
    """获取所有索引列表

    Query Parameters:
        include_health (bool): 是否包含健康检查结果 (默认false)

    Returns:
        {
            "code": 200,
            "data": {
                "indexes": [
                    {
                        "name": "索引名称",
                        "description": "索引描述",
                        "created_at": "创建时间",
                        "updated_at": "更新时间",
                        "num_documents": 文档数量,
                        "store_type": "存储类型",
                        "embedding_model": "嵌入模型"
                    }
                ],
                "total": 索引总数
            }
        }
    """
    try:
        # 获取查询参数
        include_health = request.args.get('include_health', 'false').lower() == 'true'

        # 创建索引管理器
        manager = IndexManager()

        # 获取索引列表
        indexes = manager.list_indexes()

        # 如果需要,添加健康检查信息
        if include_health:
            for index_info in indexes:
                name = index_info.get('name')
                if name:
                    health = manager.check_index_health(name)
                    index_info['health'] = health['healthy']
                    index_info['health_issues'] = len(health.get('issues', []))
                    index_info['health_warnings'] = len(health.get('warnings', []))

        logger.info(f"列出 {len(indexes)} 个索引")

        return {
            'indexes': indexes,
            'total': len(indexes)
        }

    except Exception as e:
        logger.error(f"获取索引列表失败: {e}")
        raise Exceptions.Common.internal_error(str(e))


@rag_index_bp.route('/<index_name>/info', methods=['GET'])
@jwt_required()
@handle_api_response
def get_index_info(index_name: str):
    """获取索引详细信息

    Args:
        index_name: 索引名称

    Returns:
        {
            "code": 200,
            "data": {
                "name": "索引名称",
                "description": "索引描述",
                "created_at": "创建时间",
                "updated_at": "更新时间",
                "num_documents": 文档数量,
                "path": "索引路径",
                "size": 字节大小,
                "size_mb": MB大小
            }
        }
    """
    try:
        manager = IndexManager()
        index_info = manager.get_index_info(index_name)

        if not index_info:
            raise Exceptions.Common.not_found(f"索引不存在: {index_name}")

        logger.info(f"获取索引信息: {index_name}")
        return index_info

    except Exceptions.Common.not_found:
        raise
    except Exception as e:
        logger.error(f"获取索引信息失败: {e}")
        raise Exceptions.Common.internal_error(str(e))


@rag_index_bp.route('/<index_name>/health', methods=['GET'])
@jwt_required()
@handle_api_response
def check_index_health(index_name: str):
    """检查索引健康状态

    Args:
        index_name: 索引名称

    Query Parameters:
        deep_check (bool): 是否进行深度检查(需要加载索引) (默认false)

    Returns:
        {
            "code": 200,
            "data": {
                "healthy": true/false,
                "issues": ["问题列表"],
                "warnings": ["警告列表"],
                "info": {
                    "name": "索引名称",
                    "num_documents": 文档数量,
                    "days_since_update": 天数,
                    "size_mb": 大小
                },
                "recommendations": ["修复建议列表"]
            }
        }
    """
    try:
        # 获取查询参数
        deep_check = request.args.get('deep_check', 'false').lower() == 'true'

        manager = IndexManager()

        # 深度检查需要加载索引(需要embeddings)
        embeddings = None
        if deep_check:
            embeddings = get_embeddings()

        # 执行健康检查
        health_report = manager.check_index_health(index_name, embeddings)

        logger.info(f"健康检查: {index_name} - 健康={health_report['healthy']}")

        return health_report

    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise Exceptions.Common.internal_error(str(e))


@rag_index_bp.route('/health-summary', methods=['GET'])
@jwt_required()
@handle_api_response
def get_health_summary():
    """获取所有索引的健康摘要

    Returns:
        {
            "code": 200,
            "data": {
                "total_indexes": 总数,
                "healthy_indexes": 健康数量,
                "unhealthy_indexes": 不健康数量,
                "indexes": [
                    {
                        "name": "索引名称",
                        "healthy": true/false,
                        "issues": 问题数量,
                        "warnings": 警告数量
                    }
                ]
            }
        }
    """
    try:
        manager = IndexManager()
        summary = manager.get_health_summary()

        logger.info(f"获取健康摘要: {summary['total_indexes']} 个索引")

        return summary

    except Exception as e:
        logger.error(f"获取健康摘要失败: {e}")
        raise Exceptions.Common.internal_error(str(e))


@rag_index_bp.route('/<index_name>/versions', methods=['GET'])
@jwt_required()
@handle_api_response
def get_index_versions(index_name: str):
    """获取索引版本历史

    Args:
        index_name: 索引名称

    Returns:
        {
            "code": 200,
            "data": {
                "index_name": "索引名称",
                "versions": [
                    {
                        "version": "版本号",
                        "timestamp": "时间戳",
                        "change_type": "变更类型",
                        "num_documents": 文档数量,
                        "description": "变更描述"
                    }
                ],
                "total_versions": 版本总数
            }
        }
    """
    try:
        manager = IndexManager()

        # 检查索引是否存在
        if not manager.index_exists(index_name):
            raise Exceptions.Common.not_found(f"索引不存在: {index_name}")

        # 获取版本历史
        versions = manager.get_index_versions(index_name)

        logger.info(f"获取版本历史: {index_name} - {len(versions)} 个版本")

        return {
            'index_name': index_name,
            'versions': versions,
            'total_versions': len(versions)
        }

    except Exceptions.Common.not_found:
        raise
    except Exception as e:
        logger.error(f"获取版本历史失败: {e}")
        raise Exceptions.Common.internal_error(str(e))


@rag_index_bp.route('/<index_name>/rebuild', methods=['POST'])
@jwt_required()
@handle_api_response
@requires_admin
def rebuild_index(index_name: str):
    """重建索引

    完全重建索引,替换所有现有内容。

    Args:
        index_name: 要重建的索引名称

    Request Body:
        {
            "description": "新的索引描述",
            "documents": [文档列表]  // 可选,如果不提供则清空索引
        }

    Returns:
        {
            "code": 200,
            "data": {
                "success": true,
                "message": "索引重建成功",
                "index_name": "索引名称",
                "num_documents": 文档数量
            }
        }
    """
    try:
        from blues_aka.user.models.user import User
        from langchain_core.documents import Document

        data = request.get_json() or {}
        description = data.get('description', '')
        documents_data = data.get('documents', [])

        # 转换为Document对象
        documents = [
            Document(
                page_content=doc.get('content', ''),
                metadata=doc.get('metadata', {})
            )
            for doc in documents_data
        ] if documents_data else []

        # 获取当前用户
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)

        manager = IndexManager()
        embeddings = get_embeddings()

        logger.info(f"用户 {user_id} 重建索引: {index_name}")

        # 重建索引
        vector_store = manager.rebuild_index(
            name=index_name,
            documents=documents,
            embeddings=embeddings,
            description=description
        )

        logger.info(f"索引重建成功: {index_name}")

        return {
            'success': True,
            'message': f"索引 {index_name} 重建成功",
            'index_name': index_name,
            'num_documents': len(documents)
        }

    except Exception as e:
        logger.error(f"重建索引失败: {e}")
        raise Exceptions.Common.internal_error(f"重建索引失败: {str(e)}")


@rag_index_bp.route('/<index_name>/update', methods=['PUT'])
@jwt_required()
@handle_api_response
@requires_admin
def update_index_incremental(index_name: str):
    """增量更新索引

    支持添加和删除文档,无需重建整个索引。

    Args:
        index_name: 要更新的索引名称

    Request Body:
        {
            "add_documents": [要添加的文档列表],  // 可选
            "delete_document_ids": [要删除的文档ID列表]  // 可选
        }

    Returns:
        {
            "code": 200,
            "data": {
                "success": true,
                "message": "索引更新成功",
                "index_name": "索引名称",
                "added_count": 添加的文档数,
                "deleted_count": 删除的文档数
            }
        }
    """
    try:
        from blues_aka.user.models.user import User
        from langchain_core.documents import Document

        data = request.get_json()
        if not data:
            raise Exceptions.Common.invalid_params('缺少请求体')

        add_documents_data = data.get('add_documents', [])
        delete_document_ids = data.get('delete_document_ids', [])

        if not add_documents_data and not delete_document_ids:
            raise Exceptions.Common.invalid_params(
                '至少需要提供 add_documents 或 delete_document_ids'
            )

        # 转换为Document对象
        add_documents = [
            Document(
                page_content=doc.get('content', ''),
                metadata=doc.get('metadata', {})
            )
            for doc in add_documents_data
        ] if add_documents_data else None

        # 获取当前用户
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)

        manager = IndexManager()
        embeddings = get_embeddings()

        logger.info(f"用户 {user_id} 更新索引: {index_name}")

        # 增量更新索引
        vector_store = manager.update_index_incremental(
            name=index_name,
            embeddings=embeddings,
            add_documents=add_documents,
            delete_document_ids=delete_document_ids if delete_document_ids else None
        )

        added_count = len(add_documents) if add_documents else 0
        deleted_count = len(delete_document_ids) if delete_document_ids else 0

        logger.info(f"索引更新成功: {index_name} (+{added_count}, -{deleted_count})")

        return {
            'success': True,
            'message': f"索引 {index_name} 更新成功",
            'index_name': index_name,
            'added_count': added_count,
            'deleted_count': deleted_count
        }

    except Exceptions.Common.invalid_params:
        raise
    except Exception as e:
        logger.error(f"更新索引失败: {e}")
        raise Exceptions.Common.internal_error(f"更新索引失败: {str(e)}")


@rag_index_bp.route('/<index_name>', methods=['DELETE'])
@jwt_required()
@handle_api_response
@requires_admin
def delete_index(index_name: str):
    """删除索引

    从磁盘删除指定的向量索引及其所有相关文件。

    Args:
        index_name: 要删除的索引名称

    Returns:
        {
            "code": 200,
            "data": {
                "success": true,
                "message": "索引删除成功",
                "index_name": "索引名称"
            }
        }
    """
    try:
        from blues_aka.user.models.user import User

        # 获取当前用户
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)

        manager = IndexManager()

        # 检查索引是否存在
        if not manager.index_exists(index_name):
            raise Exceptions.Common.not_found(f"索引不存在: {index_name}")

        logger.info(f"用户 {user_id} 删除索引: {index_name}")

        # 删除索引
        manager.delete_index(index_name)

        logger.info(f"索引删除成功: {index_name}")

        return {
            'success': True,
            'message': f"索引 {index_name} 删除成功",
            'index_name': index_name
        }

    except Exceptions.Common.not_found:
        raise
    except Exception as e:
        logger.error(f"删除索引失败: {e}")
        raise Exceptions.Common.internal_error(f"删除索引失败: {str(e)}")
