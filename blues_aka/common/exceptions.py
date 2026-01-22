"""
业务异常辅助类

提供便捷的异常抛出方法，自动关联异常码和HTTP状态码
"""

from typing import Optional, Dict, Any
from blues_aka.common.exception import BusinessException
from blues_aka.common.error_codes import ErrorCodes, get_http_status_code, get_error_message


class Exceptions:
    """
    异常抛出辅助类

    使用示例:
        # 简单使用
        raise Exceptions.User.invalid_credentials()

        # 带自定义消息
        raise Exceptions.User.user_not_found("用户ID: 123 不存在")

        # 带额外数据
        raise Exceptions.User.weak_password(data={"min_length": 8})
    """

    class Common:
        """通用异常"""

        @staticmethod
        def invalid_params(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """参数校验失败"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Common.INVALID_PARAMS),
                message=message or get_error_message(ErrorCodes.Common.INVALID_PARAMS),
                error_code=ErrorCodes.Common.INVALID_PARAMS,
                data=data or {}
            )

        @staticmethod
        def empty_request_body(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """请求体为空"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Common.EMPTY_REQUEST_BODY),
                message=message or get_error_message(ErrorCodes.Common.EMPTY_REQUEST_BODY),
                error_code=ErrorCodes.Common.EMPTY_REQUEST_BODY,
                data=data or {}
            )

        @staticmethod
        def internal_server_error(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """服务器内部错误"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Common.INTERNAL_SERVER_ERROR),
                message=message or get_error_message(ErrorCodes.Common.INTERNAL_SERVER_ERROR),
                error_code=ErrorCodes.Common.INTERNAL_SERVER_ERROR,
                data=data or {}
            )

        @staticmethod
        def database_error(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """数据库错误"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Common.DATABASE_ERROR),
                message=message or get_error_message(ErrorCodes.Common.DATABASE_ERROR),
                error_code=ErrorCodes.Common.DATABASE_ERROR,
                data=data or {}
            )

        @staticmethod
        def rate_limit_exceeded(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """超出速率限制"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Common.RATE_LIMIT_EXCEEDED),
                message=message or get_error_message(ErrorCodes.Common.RATE_LIMIT_EXCEEDED),
                error_code=ErrorCodes.Common.RATE_LIMIT_EXCEEDED,
                data=data or {}
            )

    class User:
        """用户模块异常"""

        @staticmethod
        def user_not_found(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """用户不存在"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.USER_NOT_FOUND),
                message=message or get_error_message(ErrorCodes.User.USER_NOT_FOUND),
                error_code=ErrorCodes.User.USER_NOT_FOUND,
                data=data or {}
            )

        @staticmethod
        def invalid_credentials(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """用户名或密码错误"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.INVALID_CREDENTIALS),
                message=message or get_error_message(ErrorCodes.User.INVALID_CREDENTIALS),
                error_code=ErrorCodes.User.INVALID_CREDENTIALS,
                data=data or {}
            )

        @staticmethod
        def account_locked(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """账户已锁定"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.ACCOUNT_LOCKED),
                message=message or get_error_message(ErrorCodes.User.ACCOUNT_LOCKED),
                error_code=ErrorCodes.User.ACCOUNT_LOCKED,
                data=data or {}
            )

        @staticmethod
        def account_disabled(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """账户已禁用"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.ACCOUNT_DISABLED),
                message=message or get_error_message(ErrorCodes.User.ACCOUNT_DISABLED),
                error_code=ErrorCodes.User.ACCOUNT_DISABLED,
                data=data or {}
            )

        @staticmethod
        def token_expired(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """令牌已过期"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.TOKEN_EXPIRED),
                message=message or get_error_message(ErrorCodes.User.TOKEN_EXPIRED),
                error_code=ErrorCodes.User.TOKEN_EXPIRED,
                data=data or {}
            )

        @staticmethod
        def token_invalid(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """令牌无效"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.TOKEN_INVALID),
                message=message or get_error_message(ErrorCodes.User.TOKEN_INVALID),
                error_code=ErrorCodes.User.TOKEN_INVALID,
                data=data or {}
            )

        @staticmethod
        def weak_password(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """密码强度不足"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.WEAK_PASSWORD),
                message=message or get_error_message(ErrorCodes.User.WEAK_PASSWORD),
                error_code=ErrorCodes.User.WEAK_PASSWORD,
                data=data or {}
            )

        @staticmethod
        def password_same_as_old(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """新密码不能与旧密码相同"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.PASSWORD_SAME_AS_OLD),
                message=message or get_error_message(ErrorCodes.User.PASSWORD_SAME_AS_OLD),
                error_code=ErrorCodes.User.PASSWORD_SAME_AS_OLD,
                data=data or {}
            )

        @staticmethod
        def invalid_current_password(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """当前密码不正确"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.INVALID_CURRENT_PASSWORD),
                message=message or get_error_message(ErrorCodes.User.INVALID_CURRENT_PASSWORD),
                error_code=ErrorCodes.User.INVALID_CURRENT_PASSWORD,
                data=data or {}
            )

        @staticmethod
        def password_change_failed(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """密码修改失败"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.User.PASSWORD_CHANGE_FAILED),
                message=message or get_error_message(ErrorCodes.User.PASSWORD_CHANGE_FAILED),
                error_code=ErrorCodes.User.PASSWORD_CHANGE_FAILED,
                data=data or {}
            )

        @staticmethod
        def duplicate_username(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """用户名已存在"""
            return BusinessException(
                code=409,
                message=message or "用户名已存在",
                error_code=ErrorCodes.User.DUPLICATE_USERNAME,
                data=data or {}
            )

        @staticmethod
        def duplicate_email(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """邮箱已存在"""
            return BusinessException(
                code=409,
                message=message or "邮箱已存在",
                error_code=ErrorCodes.User.DUPLICATE_EMAIL,
                data=data or {}
            )

        @staticmethod
        def unauthorized(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """未授权"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Permission.UNAUTHORIZED),
                message=message or get_error_message(ErrorCodes.Permission.UNAUTHORIZED),
                error_code=ErrorCodes.Permission.UNAUTHORIZED,
                data=data or {}
            )

    class Agent:
        """Agent模块异常"""

        @staticmethod
        def agent_not_found(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """智能体不存在"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Agent.AGENT_NOT_FOUND),
                message=message or get_error_message(ErrorCodes.Agent.AGENT_NOT_FOUND),
                error_code=ErrorCodes.Agent.AGENT_NOT_FOUND,
                data=data or {}
            )

        @staticmethod
        def agent_creation_failed(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """智能体创建失败"""
            return BusinessException(
                code=500,
                message=message or get_error_message(ErrorCodes.Agent.AGENT_CREATION_FAILED),
                error_code=ErrorCodes.Agent.AGENT_CREATION_FAILED,
                data=data or {}
            )

        @staticmethod
        def agent_access_denied(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """无权访问智能体"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Agent.AGENT_ACCESS_DENIED),
                message=message or get_error_message(ErrorCodes.Agent.AGENT_ACCESS_DENIED),
                error_code=ErrorCodes.Agent.AGENT_ACCESS_DENIED,
                data=data or {}
            )

        @staticmethod
        def invalid_agent_config(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """智能体配置无效"""
            return BusinessException(
                code=400,
                message=message or "智能体配置无效",
                error_code=ErrorCodes.Agent.INVALID_AGENT_CONFIG,
                data=data or {}
            )

    class Conversation:
        """会话模块异常"""

        @staticmethod
        def conversation_not_found(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """对话不存在"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Conversation.CONVERSATION_NOT_FOUND),
                message=message or get_error_message(ErrorCodes.Conversation.CONVERSATION_NOT_FOUND),
                error_code=ErrorCodes.Conversation.CONVERSATION_NOT_FOUND,
                data=data or {}
            )

        @staticmethod
        def conversation_access_denied(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """无权访问对话"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Conversation.CONVERSATION_ACCESS_DENIED),
                message=message or get_error_message(ErrorCodes.Conversation.CONVERSATION_ACCESS_DENIED),
                error_code=ErrorCodes.Conversation.CONVERSATION_ACCESS_DENIED,
                data=data or {}
            )

        @staticmethod
        def conversation_creation_failed(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """对话创建失败"""
            return BusinessException(
                code=500,
                message=message or "对话创建失败",
                error_code=ErrorCodes.Conversation.CONVERSATION_CREATION_FAILED,
                data=data or {}
            )

    class Chat:
        """聊天模块异常"""

        @staticmethod
        def message_not_found(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """消息不存在"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Chat.MESSAGE_NOT_FOUND),
                message=message or get_error_message(ErrorCodes.Chat.MESSAGE_NOT_FOUND),
                error_code=ErrorCodes.Chat.MESSAGE_NOT_FOUND,
                data=data or {}
            )

        @staticmethod
        def message_send_failed(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """消息发送失败"""
            return BusinessException(
                code=500,
                message=message or get_error_message(ErrorCodes.Chat.MESSAGE_SEND_FAILED),
                error_code=ErrorCodes.Chat.MESSAGE_SEND_FAILED,
                data=data or {}
            )

        @staticmethod
        def ai_response_failed(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """AI响应失败"""
            return BusinessException(
                code=500,
                message=message or get_error_message(ErrorCodes.Chat.AI_RESPONSE_FAILED),
                error_code=ErrorCodes.Chat.AI_RESPONSE_FAILED,
                data=data or {}
            )

        @staticmethod
        def message_too_long(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """消息过长"""
            return BusinessException(
                code=400,
                message=message or get_error_message(ErrorCodes.Chat.MESSAGE_TOO_LONG),
                error_code=ErrorCodes.Chat.MESSAGE_TOO_LONG,
                data=data or {}
            )

        @staticmethod
        def message_content_empty(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """消息内容为空"""
            return BusinessException(
                code=400,
                message=message or get_error_message(ErrorCodes.Chat.MESSAGE_CONTENT_EMPTY),
                error_code=ErrorCodes.Chat.MESSAGE_CONTENT_EMPTY,
                data=data or {}
            )

    class Permission:
        """权限模块异常"""

        @staticmethod
        def permission_denied(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """权限不足"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Permission.PERMISSION_DENIED),
                message=message or get_error_message(ErrorCodes.Permission.PERMISSION_DENIED),
                error_code=ErrorCodes.Permission.PERMISSION_DENIED,
                data=data or {}
            )

        @staticmethod
        def forbidden(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """禁止访问"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Permission.FORBIDDEN),
                message=message or get_error_message(ErrorCodes.Permission.FORBIDDEN),
                error_code=ErrorCodes.Permission.FORBIDDEN,
                data=data or {}
            )

        @staticmethod
        def unauthorized(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """未授权"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Permission.UNAUTHORIZED),
                message=message or get_error_message(ErrorCodes.Permission.UNAUTHORIZED),
                error_code=ErrorCodes.Permission.UNAUTHORIZED,
                data=data or {}
            )

        @staticmethod
        def admin_required(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """需要管理员权限"""
            return BusinessException(
                code=get_http_status_code(ErrorCodes.Permission.ADMIN_REQUIRED),
                message=message or get_error_message(ErrorCodes.Permission.ADMIN_REQUIRED),
                error_code=ErrorCodes.Permission.ADMIN_REQUIRED,
                data=data or {}
            )

    class RAG:
        """RAG模块异常"""

        @staticmethod
        def document_not_found(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """文档不存在"""
            return BusinessException(
                code=404,
                message=message or get_error_message(ErrorCodes.RAG.DOCUMENT_NOT_FOUND),
                error_code=ErrorCodes.RAG.DOCUMENT_NOT_FOUND,
                data=data or {}
            )

        @staticmethod
        def document_upload_failed(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """文档上传失败"""
            return BusinessException(
                code=500,
                message=message or get_error_message(ErrorCodes.RAG.DOCUMENT_UPLOAD_FAILED),
                error_code=ErrorCodes.RAG.DOCUMENT_UPLOAD_FAILED,
                data=data or {}
            )

        @staticmethod
        def retrieval_failed(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """检索失败"""
            return BusinessException(
                code=500,
                message=message or get_error_message(ErrorCodes.RAG.RETRIEVAL_FAILED),
                error_code=ErrorCodes.RAG.RETRIEVAL_FAILED,
                data=data or {}
            )

        @staticmethod
        def invalid_document_format(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """文档格式无效"""
            return BusinessException(
                code=400,
                message=message or get_error_message(ErrorCodes.RAG.INVALID_DOCUMENT_FORMAT),
                error_code=ErrorCodes.RAG.INVALID_DOCUMENT_FORMAT,
                data=data or {}
            )

        @staticmethod
        def document_too_large(message: str = None, data: Dict[str, Any] = None) -> BusinessException:
            """文档过大"""
            return BusinessException(
                code=413,
                message=message or get_error_message(ErrorCodes.RAG.DOCUMENT_TOO_LARGE),
                error_code=ErrorCodes.RAG.DOCUMENT_TOO_LARGE,
                data=data or {}
            )


# 便捷导入
E = Exceptions  # 简写别名
