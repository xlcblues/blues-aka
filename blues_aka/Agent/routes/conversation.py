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
from blues_aka.common.exceptions import E
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.rag.index_manager import IndexManager
from blues_aka.rag.loader import load_document, load_documents_from_paths, get_supported_extensions
from blues_aka.rag.splitters import split_documents
from blues_aka.rag.embeddings import get_embeddings
from blues_aka.extensions import db

logger = logging.getLogger(__name__)
conversation_bp = Blueprint('conversation', __name__, url_prefix='/conversation')

# 允许上传的文件扩展名
ALLOWED_EXTENSIONS = {ext[1:] for ext in get_supported_extensions().keys()}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 16MB

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
                    raise BusinessException(code=404, message="智能体不存在或无权访问", error_code=404)
                conversation.agent_id = agent_id
            else:
                # 允许设置为空（使用默认模型）
                conversation.agent_id = None

        db.session.commit()

        return success(data=conversation.to_dict(include_agent=True), message="更新成功")

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

@conversation_bp.route('/conversations/<int:conversation_id>/rag', methods=['PATCH'])
@jwt_required()
@handle_api_response
def toggle_rag_mode(conversation_id):
    """切换对话关联的智能体的RAG模式"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        conversation = Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()

        if not conversation:
            raise  E.Conversation.conversation_not_found()

        if not conversation.agent:
            raise BusinessException(code=400, message="该对话未关联智能体，无法配置RAG", error_code=400)

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
        raise BusinessException(code=500, message=str(e))

@conversation_bp.route('/rag/indexes', methods=['GET'])
@jwt_required()
@handle_api_response
def list_rag_indexes():
    """获取所有可用的RAG知识库索引列表"""
    try:
        index_manager = IndexManager()
        indexes = index_manager.list_indexes()
        return success(data=indexes, message="获取索引列表成功")

    except Exception as e:
        logger.error(f"获取索引列表失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message=str(e))

@conversation_bp.route('/rag/indexes/<string:index_name>', methods=['GET'])
@jwt_required()
@handle_api_response
def get_rag_index_info(index_name):
    """获取指定知识库索引的详细信息"""
    try:
        index_manager = IndexManager()
        index_info = index_manager.get_index_info(index_name)

        if not index_info:
            raise BusinessException(code=404, message=f"知识库索引不存在: {index_name}")

        return success(data=index_info, message="获取索引详情成功")

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取索引详情失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message=str(e))

@conversation_bp.route('/rag/indexes', methods=['POST'])
@jwt_required()
@handle_api_response
def create_knowledge_base():
    """创建新的知识库索引

    Request Body (multipart/form-data):
        - file: 文档文件 (支持 pdf, txt, md, html, json)
        - index_name: 索引名称 (必填)
        - description: 索引描述 (可选)
        - chunk_size: 分块大小 (可选，默认使用配置)
        - chunk_overlap: 分块重叠 (可选，默认使用配置)
        - splitter_type: 分块器类型 (可选，默认 recursive)
        - overwrite: 是否覆盖已存在的索引 (可选，默认 False)

    Returns:
        创建结果，包含索引信息和文档统计
    """
    try:
        user_id = get_jwt_identity()

        # 检查是否有文件
        if 'file' not in request.files:
            logger.error("未上传文件 - request.files 中没有 'file' 键")
            raise BusinessException(code=400, message="未上传文件", error_code="NO_FILE_UPLOADED")

        file = request.files['file']
        logger.info(f"接收到的文件对象: {file}, filename: {file.filename}")

        # 检查文件名
        if not file.filename or file.filename == '':
            logger.error("文件名为空")
            raise BusinessException(code=400, message="文件名为空", error_code="EMPTY_FILENAME")

        # 检查文件扩展名
        # 先从原始文件名提取扩展名（支持中文文件名）
        original_file_ext = Path(file.filename).suffix.lower()
        logger.info(f"原始文件扩展名: {original_file_ext}")

        # 检查文件扩展名是否为空
        if not original_file_ext:
            logger.error(f"文件扩展名为空，原始文件名: {file.filename}")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise BusinessException(
                code=400,
                message=f"文件缺少扩展名。支持的类型: {supported}",
                error_code="MISSING_FILE_EXTENSION"
            )

        # 检查文件类型是否支持
        file_ext_without_dot = original_file_ext[1:]  # 去掉点号
        if file_ext_without_dot not in ALLOWED_EXTENSIONS:
            logger.error(f"不支持的文件类型: {original_file_ext} ({file_ext_without_dot})")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise BusinessException(
                code=400,
                message=f"不支持的文件类型: {original_file_ext}。支持的类型: {supported}",
                error_code="UNSUPPORTED_FILE_TYPE"
            )

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            size_mb = MAX_FILE_SIZE / 1024 / 1024
            raise BusinessException(
                code=400,
                message=f"文件过大，最大支持 {size_mb:.0f}MB",
                error_code="FILE_TOO_LARGE"
            )

        # 获取参数
        index_name = request.form.get('index_name')
        if not index_name:
            raise BusinessException(code=400, message="索引名称不能为空", error_code="EMPTY_INDEX_NAME")

        # 验证索引名称（只允许字母、数字、下划线、中划线）
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', index_name):
            raise BusinessException(
                code=400,
                message="索引名称只能包含字母、数字、下划线和中划线",
                error_code="INVALID_INDEX_NAME"
            )

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
                raise BusinessException(
                    code=409,
                    message=f"知识库索引已存在: {index_name}。如要覆盖，请设置 overwrite=true",
                    error_code="INDEX_EXISTS"
                )

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
        raise BusinessException(code=500, message=f"创建知识库失败: {str(e)}")

@conversation_bp.route('/rag/indexes/<string:index_name>', methods=['DELETE'])
@jwt_required()
@handle_api_response
def delete_knowledge_base(index_name):
    """删除指定的知识库索引"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"用户 {user_id} 请求删除知识库: {index_name}")

        index_manager = IndexManager()

        # 检查索引是否存在
        if not index_manager.index_exists(index_name):
            raise BusinessException(
                code=404,
                message=f"知识库索引不存在: {index_name}",
                error_code="INDEX_NOT_FOUND"
            )

        # 删除索引
        index_manager.delete_index(index_name)

        logger.info(f"知识库删除成功: {index_name}")
        return success(message=f"知识库 {index_name} 已删除")

    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"删除知识库失败: {str(e)}", exc_info=True)
        raise BusinessException(code=500, message=f"删除知识库失败: {str(e)}")

@conversation_bp.route('/rag/indexes/<string:index_name>/documents', methods=['POST'])
@jwt_required()
@handle_api_response
def add_documents_to_index(index_name):
    """向现有知识库索引添加新文档

    Request Body (multipart/form-data):
        - file: 文档文件 (必填)
        - chunk_size: 分块大小 (可选)
        - chunk_overlap: 分块重叠 (可选)
        - splitter_type: 分块器类型 (可选)

    Returns:
        添加结果，包含新增文档的统计信息
    """
    try:
        user_id = get_jwt_identity()

        # 检查是否有文件
        if 'file' not in request.files:
            logger.error("未上传文件 - request.files 中没有 'file' 键")
            raise BusinessException(code=400, message="未上传文件", error_code="NO_FILE_UPLOADED")

        file = request.files['file']
        logger.info(f"接收到的文件对象: {file}, filename: {file.filename}")

        if not file.filename or file.filename == '':
            logger.error("文件名为空")
            raise BusinessException(code=400, message="文件名为空", error_code="EMPTY_FILENAME")

        # 检查文件扩展名
        # 先从原始文件名提取扩展名（支持中文文件名）
        original_file_ext = Path(file.filename).suffix.lower()
        logger.info(f"原始文件扩展名: {original_file_ext}")

        # 检查文件扩展名是否为空
        if not original_file_ext:
            logger.error(f"文件扩展名为空，原始文件名: {file.filename}")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise BusinessException(
                code=400,
                message=f"文件缺少扩展名。支持的类型: {supported}",
                error_code="MISSING_FILE_EXTENSION"
            )

        # 检查文件类型是否支持
        file_ext_without_dot = original_file_ext[1:]  # 去掉点号
        if file_ext_without_dot not in ALLOWED_EXTENSIONS:
            logger.error(f"不支持的文件类型: {original_file_ext} ({file_ext_without_dot})")
            supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise BusinessException(
                code=400,
                message=f"不支持的文件类型: {original_file_ext}。支持的类型: {supported}",
                error_code="UNSUPPORTED_FILE_TYPE"
            )

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            size_mb = MAX_FILE_SIZE / 1024 / 1024
            raise BusinessException(
                code=400,
                message=f"文件过大，最大支持 {size_mb:.0f}MB",
                error_code="FILE_TOO_LARGE"
            )

        # 获取参数
        chunk_size = int(request.form.get('chunk_size', 0)) or None
        chunk_overlap = int(request.form.get('chunk_overlap', 0)) or None
        splitter_type = request.form.get('splitter_type', 'recursive')

        logger.info(f"用户 {user_id} 向知识库 {index_name} 添加文档")
        logger.info(f"文件: {file.filename} ({file_size / 1024:.1f} KB)")

        # 检查索引是否存在
        index_manager = IndexManager()
        if not index_manager.index_exists(index_name):
            raise BusinessException(
                code=404,
                message=f"知识库索引不存在: {index_name}",
                error_code="INDEX_NOT_FOUND"
            )

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
        raise BusinessException(code=500, message=f"添加文档失败: {str(e)}")

@conversation_bp.route('/rag/supported-formats', methods=['GET'])
@handle_api_response
def get_supported_formats():
    """获取支持的文件格式列表"""
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
        raise BusinessException(code=500, message=str(e))

def _get_file_type_description(file_type: str) -> str:
    """获取文件类型的中文描述"""
    descriptions = {
        'pdf': 'PDF 文档',
        'text': '纯文本文件',
        'markdown': 'Markdown 文档',
        'html': 'HTML 网页',
        'json': 'JSON 数据文件'
    }
    return descriptions.get(file_type, file_type)