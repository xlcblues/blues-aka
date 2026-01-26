"""
异常码常量定义

异常码格式：模块编号(2位) + 功能编号(2位) + 具体错误(2位) = 6位数字

模块编号：
- 10: 通用模块
- 20: 用户模块
- 30: Agent模块
- 40: 会话模块
- 50: 聊天模块
- 60: RAG模块
- 70: 权限模块
"""

class ErrorCodes:
    """异常码常量类"""

    # ==================== 通用异常 (10xxxx) ====================
    class Common:
        """通用异常码"""

        # 通用请求异常 (1001xx)
        INVALID_PARAMS = "100001"  # 参数校验失败
        EMPTY_REQUEST_BODY = "100002"  # 请求体为空
        INVALID_REQUEST_METHOD = "100003"  # 不支持的请求方法
        INVALID_CONTENT_TYPE = "100004"  # 不支持的Content-Type
        REQUEST_TIMEOUT = "100005"  # 请求超时
        REQUEST_TOO_LARGE = "100006"  # 请求体过大

        # 通用数据库异常 (1002xx)
        DATABASE_ERROR = "100201"  # 数据库错误
        DATABASE_INTEGRITY_ERROR = "100202"  # 数据库完整性错误
        DATABASE_CONNECTION_ERROR = "100203"  # 数据库连接错误
        DATABASE_QUERY_ERROR = "100204"  # 数据库查询错误

        # 通用服务器异常 (1003xx)
        INTERNAL_SERVER_ERROR = "100301"  # 服务器内部错误
        SERVICE_UNAVAILABLE = "100302"  # 服务不可用
        MAINTENANCE_MODE = "100303"  # 系统维护中

        # 通用验证异常 (1004xx)
        VALIDATION_ERROR = "100401"  # 数据验证失败
        INVALID_FORMAT = "100402"  # 格式无效
        INVALID_LENGTH = "100403"  # 长度无效
        INVALID_RANGE = "100404"  # 范围无效

        # 通用业务异常 (1005xx)
        OPERATION_FAILED = "100501"  # 操作失败
        OPERATION_NOT_SUPPORTED = "100502"  # 操作不支持
        RESOURCE_LOCKED = "100503"  # 资源已锁定
        RATE_LIMIT_EXCEEDED = "100504"  # 超出速率限制

    # ==================== 用户模块异常 (20xxxx) ====================
    class User:
        """用户模块异常码"""

        # 用户查询异常 (2001xx)
        USER_NOT_FOUND = "200101"  # 用户不存在
        USER_QUERY_FAILED = "200102"  # 查询用户失败
        USER_LIST_FAILED = "200103"  # 获取用户列表失败

        # 用户创建异常 (2002xx)
        USER_CREATION_FAILED = "200201"  # 用户创建失败
        DUPLICATE_USERNAME = "200202"  # 用户名已存在
        DUPLICATE_EMAIL = "200203"  # 邮箱已存在
        INVALID_USERNAME = "200204"  # 用户名无效
        INVALID_EMAIL = "200205"  # 邮箱无效

        # 用户更新异常 (2003xx)
        USER_UPDATE_FAILED = "200301"  # 用户更新失败
        USERNAME_EXISTS = "200302"  # 用户名已被使用
        EMAIL_EXISTS = "200303"  # 邮箱已被使用

        # 用户删除异常 (2004xx)
        USER_DELETE_FAILED = "200401"  # 用户删除失败
        USER_HAS_DEPENDENCIES = "200402"  # 用户存在关联数据
        USER_ALREADY_DELETED = "200403"  # 用户已删除
        USER_NOT_DELETED = "200404" # 用户未删除（回复）
        USER_RESTORE_FAILED = "200405" # 用户恢复失败

        # 用户认证异常 (2005xx)
        INVALID_CREDENTIALS = "200501"  # 用户名或密码错误
        ACCOUNT_LOCKED = "200502"  # 账户已锁定
        ACCOUNT_DISABLED = "200503"  # 账户已禁用
        ACCOUNT_NOT_VERIFIED = "200504"  # 账户未验证
        TOKEN_EXPIRED = "200505"  # 令牌已过期
        TOKEN_INVALID = "200506"  # 令牌无效
        TOKEN_MISSING = "200507"  # 令牌缺失
        REFRESH_TOKEN_FAILED = "200508"  # 刷新令牌失败

        # 密码相关异常 (2006xx)
        WEAK_PASSWORD = "200601"  # 密码强度不足
        PASSWORD_SAME_AS_OLD = "200602"  # 新密码不能与旧密码相同
        PASSWORD_EXPIRED = "200603"  # 密码已过期
        INVALID_CURRENT_PASSWORD = "200604"  # 当前密码不正确
        PASSWORD_CHANGE_FAILED = "200605"  # 密码修改失败
        PASSWORD_RESET_FAILED = "200606"  # 密码重置失败

        # 用户状态异常 (2007xx)
        TOO_MANY_LOGIN_ATTEMPTS = "200701"  # 登录尝试次数过多
        SESSION_EXPIRED = "200702"  # 会话已过期
        SESSION_INVALID = "200703"  # 会话无效

    # ==================== Agent模块异常 (30xxxx) ====================
    class Agent:
        """Agent模块异常码"""

        # Agent查询异常 (3001xx)
        AGENT_NOT_FOUND = "300101"  # 智能体不存在
        AGENT_QUERY_FAILED = "300102"  # 查询智能体失败
        AGENT_LIST_FAILED = "300103"  # 获取智能体列表失败

        # Agent创建异常 (3002xx)
        AGENT_CREATION_FAILED = "300201"  # 智能体创建失败
        INVALID_AGENT_NAME = "300202"  # 智能体名称无效
        INVALID_AGENT_CONFIG = "300203"  # 智能体配置无效
        AGENT_LIMIT_EXCEEDED = "300204"  # 智能体数量超限
        DUPLICATE_AGENT_NAME = "300205"  # 智能体名称已存在

        # Agent更新异常 (3003xx)
        AGENT_UPDATE_FAILED = "300301"  # 智能体更新失败
        AGENT_CONFIG_INVALID = "300302"  # 智能体配置无效

        # Agent删除异常 (3004xx)
        AGENT_DELETE_FAILED = "300401"  # 智能体删除失败
        AGENT_HAS_CONVERSATIONS = "300402"  # 智能体存在对话记录

        # Agent权限异常 (3005xx)
        AGENT_ACCESS_DENIED = "300501"  # 无权访问智能体
        AGENT_NOT_OWNER = "300502"  # 不是智能体的所有者
        AGENT_IS_PUBLIC = "300503"  # 智能体为公开状态

        # Agent配置异常 (3006xx)
        INVALID_MODEL_CONFIG = "300601"  # 模型配置无效
        INVALID_TOOL_CONFIG = "300602"  # 工具配置无效
        INVALID_PROMPT = "300603"  # 提示词无效
        MODEL_NOT_AVAILABLE = "300604"  # 模型不可用

    # ==================== 会话模块异常 (40xxxx) ====================
    class Conversation:
        """会话模块异常码"""

        # 会话查询异常 (4001xx)
        CONVERSATION_NOT_FOUND = "400101"  # 对话不存在
        CONVERSATION_QUERY_FAILED = "400102"  # 查询对话失败
        CONVERSATION_LIST_FAILED = "400103"  # 获取对话列表失败

        # 会话创建异常 (4002xx)
        CONVERSATION_CREATION_FAILED = "400201"  # 对话创建失败
        INVALID_CONVERSATION_TITLE = "400202"  # 对话标题无效

        # 会话更新异常 (4003xx)
        CONVERSATION_UPDATE_FAILED = "400301"  # 对话更新失败
        CONVERSATION_TITLE_EXISTS = "400302"  # 对话标题已存在

        # 会话删除异常 (4004xx)
        CONVERSATION_DELETE_FAILED = "400401"  # 对话删除失败
        CONVERSATION_HAS_MESSAGES = "400402"  # 对话包含消息记录

        # 会话权限异常 (4005xx)
        CONVERSATION_ACCESS_DENIED = "400501"  # 无权访问对话
        CONVERSATION_NOT_OWNER = "400502"  # 不是对话的所有者

    # ==================== 聊天模块异常 (50xxxx) ====================
    class Chat:
        """聊天模块异常码"""

        # 消息发送异常 (5001xx)
        MESSAGE_SEND_FAILED = "500101"  # 消息发送失败
        MESSAGE_TOO_LONG = "500102"  # 消息过长
        MESSAGE_CONTENT_EMPTY = "500103"  # 消息内容为空
        INVALID_MESSAGE_TYPE = "500104"  # 消息类型无效

        # 消息查询异常 (5002xx)
        MESSAGE_NOT_FOUND = "500201"  # 消息不存在
        MESSAGE_QUERY_FAILED = "500202"  # 查询消息失败
        MESSAGE_LIST_FAILED = "500203"  # 获取消息列表失败

        # 流式响应异常 (5003xx)
        STREAM_RESPONSE_FAILED = "500301"  # 流式响应失败
        STREAM_INTERRUPTED = "500302"  # 流式响应中断
        STREAM_TIMEOUT = "500303"  # 流式响应超时

        # AI响应异常 (5004xx)
        AI_RESPONSE_FAILED = "500401"  # AI响应失败
        AI_MODEL_ERROR = "500402"  # AI模型错误
        AI_TIMEOUT = "500403"  # AI响应超时
        AI_QUOTA_EXCEEDED = "500404"  # AI配额超限

        # 消息反馈异常 (5005xx)
        FEEDBACK_FAILED = "500501"  # 反馈提交失败
        INVALID_FEEDBACK_TYPE = "500502"  # 反馈类型无效

        # 消息重新生成异常 (5006xx)
        REGENERATE_FAILED = "500601"  # 重新生成失败
        NO_MESSAGE_TO_REGENERATE = "500602"  # 没有可重新生成的消息
        REGENERATE_LIMIT_EXCEEDED = "500603"  # 重新生成次数超限

    # ==================== RAG模块异常 (60xxxx) ====================
    class RAG:
        """RAG模块异常码"""

        # 文档管理异常 (6001xx)
        DOCUMENT_NOT_FOUND = "600101"  # 文档不存在
        DOCUMENT_UPLOAD_FAILED = "600102"  # 文档上传失败
        DOCUMENT_DELETE_FAILED = "600103"  # 文档删除失败
        INVALID_DOCUMENT_FORMAT = "600104"  # 文档格式无效
        DOCUMENT_TOO_LARGE = "600105"  # 文档过大
        DOCUMENT_ALREADY_EXISTS = "600106"  # 文档已存在

        # 知识库异常 (6002xx)
        KNOWLEDGE_BASE_NOT_FOUND = "600201"  # 知识库不存在
        KNOWLEDGE_BASE_CREATION_FAILED = "600202"  # 知识库创建失败
        KNOWLEDGE_BASE_UPDATE_FAILED = "600203"  # 知识库更新失败
        KNOWLEDGE_BASE_DELETE_FAILED = "600204"  # 知识库删除失败

        # 索引异常 (6003xx)
        INDEX_CREATION_FAILED = "600301"  # 索引创建失败
        INDEX_UPDATE_FAILED = "600302"  # 索引更新失败
        INDEX_DELETE_FAILED = "600303"  # 索引删除失败
        INDEX_QUERY_FAILED = "600304"  # 索引查询失败

        # 向量化异常 (6004xx)
        EMBEDDING_FAILED = "600401"  # 向量化失败
        EMBEDDING_MODEL_ERROR = "600402"  # 向量化模型错误
        EMBEDDING_TIMEOUT = "600403"  # 向量化超时

        # 检索异常 (6005xx)
        RETRIEVAL_FAILED = "600501"  # 检索失败
        NO_RELEVANT_DOCUMENT = "600502"  # 没有相关文档
        RETRIEVAL_TIMEOUT = "600503"  # 检索超时

    # ==================== 权限模块异常 (70xxxx) ====================
    class Permission:
        """权限模块异常码"""

        # 权限验证异常 (7001xx)
        PERMISSION_DENIED = "700101"  # 权限不足
        FORBIDDEN = "700102"  # 禁止访问
        UNAUTHORIZED = "700103"  # 未授权

        # 角色管理异常 (7002xx)
        ROLE_NOT_FOUND = "700201"  # 角色不存在
        ROLE_CREATION_FAILED = "700202"  # 角色创建失败
        ROLE_UPDATE_FAILED = "700203"  # 角色更新失败
        ROLE_DELETE_FAILED = "700204"  # 角色删除失败
        ROLE_ALREADY_EXISTS = "700205"  # 角色已存在
        ROLE_IN_USE = "700206"  # 角色正在使用中

        # 资源权限异常 (7003xx)
        RESOURCE_ACCESS_DENIED = "700301"  # 资源访问被拒绝
        RESOURCE_NOT_OWNED = "700302"  # 不拥有该资源
        OPERATION_NOT_ALLOWED = "700303"  # 操作不允许

        # 管理员权限异常 (7004xx)
        ADMIN_REQUIRED = "700401"  # 需要管理员权限
        NOT_ADMIN = "700402"  # 不是管理员


# 异常码对应的HTTP状态码映射
ERROR_CODE_HTTP_MAP = {
    # 客户端错误 4xx
    ErrorCodes.Common.INVALID_PARAMS: 400,
    ErrorCodes.Common.EMPTY_REQUEST_BODY: 400,
    ErrorCodes.Common.INVALID_REQUEST_METHOD: 405,
    ErrorCodes.Common.INVALID_CONTENT_TYPE: 415,
    ErrorCodes.Common.REQUEST_TOO_LARGE: 413,

    ErrorCodes.User.USER_NOT_FOUND: 404,
    ErrorCodes.User.INVALID_CREDENTIALS: 401,
    ErrorCodes.User.ACCOUNT_LOCKED: 423,
    ErrorCodes.User.ACCOUNT_DISABLED: 403,
    ErrorCodes.User.TOKEN_EXPIRED: 401,
    ErrorCodes.User.TOKEN_INVALID: 401,
    ErrorCodes.User.TOKEN_MISSING: 401,
    ErrorCodes.User.WEAK_PASSWORD: 400,
    ErrorCodes.User.PASSWORD_SAME_AS_OLD: 400,
    ErrorCodes.User.INVALID_CURRENT_PASSWORD: 400,

    ErrorCodes.Agent.AGENT_NOT_FOUND: 404,
    ErrorCodes.Agent.AGENT_ACCESS_DENIED: 403,
    ErrorCodes.Agent.AGENT_NOT_OWNER: 403,

    ErrorCodes.Conversation.CONVERSATION_NOT_FOUND: 404,
    ErrorCodes.Conversation.CONVERSATION_ACCESS_DENIED: 403,

    ErrorCodes.Chat.MESSAGE_NOT_FOUND: 404,
    ErrorCodes.Chat.MESSAGE_TOO_LONG: 400,
    ErrorCodes.Chat.MESSAGE_CONTENT_EMPTY: 400,
    ErrorCodes.Chat.AI_QUOTA_EXCEEDED: 429,

    ErrorCodes.Permission.PERMISSION_DENIED: 403,
    ErrorCodes.Permission.FORBIDDEN: 403,
    ErrorCodes.Permission.UNAUTHORIZED: 401,
    ErrorCodes.Permission.ADMIN_REQUIRED: 403,

    # 服务器错误 5xx
    ErrorCodes.Common.INTERNAL_SERVER_ERROR: 500,
    ErrorCodes.Common.SERVICE_UNAVAILABLE: 503,
    ErrorCodes.Common.DATABASE_ERROR: 500,
    ErrorCodes.Common.DATABASE_CONNECTION_ERROR: 503,
    ErrorCodes.Common.RATE_LIMIT_EXCEEDED: 429,

    # 其他默认 400
    "default": 400
}


# 异常码对应的消息模板
ERROR_MESSAGE_TEMPLATES = {
    ErrorCodes.Common.INVALID_PARAMS: "参数校验失败",
    ErrorCodes.Common.EMPTY_REQUEST_BODY: "请求体不能为空",
    ErrorCodes.Common.INTERNAL_SERVER_ERROR: "服务器内部错误",
    ErrorCodes.Common.DATABASE_ERROR: "数据库错误",

    ErrorCodes.User.USER_NOT_FOUND: "用户不存在",
    ErrorCodes.User.INVALID_CREDENTIALS: "用户名或密码错误",
    ErrorCodes.User.ACCOUNT_LOCKED: "账户已锁定",
    ErrorCodes.User.ACCOUNT_DISABLED: "账户已禁用",
    ErrorCodes.User.TOKEN_EXPIRED: "令牌已过期",
    ErrorCodes.User.TOKEN_INVALID: "令牌无效",
    ErrorCodes.User.WEAK_PASSWORD: "密码强度不足",
    ErrorCodes.User.PASSWORD_CHANGE_FAILED: "密码修改失败",

    ErrorCodes.Agent.AGENT_NOT_FOUND: "智能体不存在",
    ErrorCodes.Agent.AGENT_CREATION_FAILED: "智能体创建失败",
    ErrorCodes.Agent.AGENT_ACCESS_DENIED: "无权访问智能体",

    ErrorCodes.Conversation.CONVERSATION_NOT_FOUND: "对话不存在",
    ErrorCodes.Conversation.CONVERSATION_ACCESS_DENIED: "无权访问对话",

    ErrorCodes.Chat.MESSAGE_SEND_FAILED: "消息发送失败",
    ErrorCodes.Chat.MESSAGE_NOT_FOUND: "消息不存在",
    ErrorCodes.Chat.AI_RESPONSE_FAILED: "AI响应失败",

    ErrorCodes.RAG.DOCUMENT_NOT_FOUND: "文档不存在",
    ErrorCodes.RAG.DOCUMENT_UPLOAD_FAILED: "文档上传失败",
    ErrorCodes.RAG.RETRIEVAL_FAILED: "检索失败",

    ErrorCodes.Permission.PERMISSION_DENIED: "权限不足",
    ErrorCodes.Permission.FORBIDDEN: "禁止访问",
    ErrorCodes.Permission.UNAUTHORIZED: "未授权",
    ErrorCodes.Permission.ADMIN_REQUIRED: "需要管理员权限",
}


def get_http_status_code(error_code: str) -> int:
    """
    根据异常码获取对应的HTTP状态码

    Args:
        error_code: 异常码

    Returns:
        HTTP状态码
    """
    return ERROR_CODE_HTTP_MAP.get(error_code, ERROR_CODE_HTTP_MAP["default"])


def get_error_message(error_code: str) -> str:
    """
    根据异常码获取错误消息模板

    Args:
        error_code: 异常码

    Returns:
        错误消息
    """
    return ERROR_MESSAGE_TEMPLATES.get(error_code, "未知错误")
