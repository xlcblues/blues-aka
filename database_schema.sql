-- ================================================
-- 数据库建表语句
-- 生成时间: 2026-03-29
-- 数据库: PostgreSQL (兼容 MySQL)
-- ================================================

-- 启用 UUID 扩展（PostgreSQL）
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用 CITEXT 扩展（不区分大小写的文本类型，PostgreSQL）
CREATE EXTENSION IF NOT EXISTS citext;

-- ================================================
-- 1. 用户表 (users)
-- ================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email CITEXT NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    phone VARCHAR(20),

    -- 状态字段
    status VARCHAR(20) DEFAULT 'inactive',
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,

    -- 登录相关
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    last_login_at TIMESTAMP,
    last_login_ip VARCHAR(45),
    login_count INTEGER DEFAULT 0,

    -- 安全相关
    password_changed_at TIMESTAMP,
    email_verified_at TIMESTAMP,
    verification_token VARCHAR(255),
    reset_password_token VARCHAR(255),
    reset_password_expires TIMESTAMP,

    -- 扩展信息
    profile JSON,
    preferences JSON,

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_is_verified ON users(is_verified);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);
CREATE INDEX idx_users_is_deleted ON users(is_deleted);

-- 添加注释
COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.status IS '用户状态: active, inactive, suspended, deleted';
COMMENT ON COLUMN users.profile IS '用户扩展信息（JSON格式）';
COMMENT ON COLUMN users.preferences IS '用户偏好设置（JSON格式）';


-- ================================================
-- 2. 角色表 (roles)
-- ================================================
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    description TEXT,

    -- 状态字段
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX idx_roles_name ON roles(name);
CREATE INDEX idx_roles_created_at ON roles(created_at);
CREATE INDEX idx_roles_deleted_at ON roles(deleted_at);
CREATE INDEX idx_roles_is_deleted ON roles(is_deleted);

-- 添加注释
COMMENT ON TABLE roles IS '角色表';


-- ================================================
-- 3. 权限表 (permissions)
-- ================================================
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    description TEXT,
    resource VARCHAR(50),
    action VARCHAR(50),

    -- 状态字段
    is_active BOOLEAN DEFAULT TRUE,

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX idx_permissions_name ON permissions(name);
CREATE INDEX idx_permissions_resource ON permissions(resource);
CREATE INDEX idx_permissions_action ON permissions(action);
CREATE INDEX idx_permissions_created_at ON permissions(created_at);
CREATE INDEX idx_permissions_deleted_at ON permissions(deleted_at);
CREATE INDEX idx_permissions_is_deleted ON permissions(is_deleted);

-- 添加注释
COMMENT ON TABLE permissions IS '权限表';
COMMENT ON COLUMN permissions.resource IS '资源类型: user, role, permission, agent等';
COMMENT ON COLUMN permissions.action IS '操作类型: create, read, update, delete等';


-- ================================================
-- 4. 用户角色关联表 (user_roles)
-- ================================================
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 复合主键
    PRIMARY KEY (user_id, role_id),

    -- 外键约束
    CONSTRAINT fk_user_roles_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_roles_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
        ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);

-- 添加注释
COMMENT ON TABLE user_roles IS '用户角色关联表（多对多）';


-- ================================================
-- 5. 用户权限关联表 (user_permissions)
-- ================================================
CREATE TABLE user_permissions (
    user_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 复合主键
    PRIMARY KEY (user_id, permission_id),

    -- 外键约束
    CONSTRAINT fk_user_permissions_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_permissions_permission
        FOREIGN KEY (permission_id)
        REFERENCES permissions(id)
        ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_user_permissions_user_id ON user_permissions(user_id);
CREATE INDEX idx_user_permissions_permission_id ON user_permissions(permission_id);

-- 添加注释
COMMENT ON TABLE user_permissions IS '用户权限关联表（多对多）';


-- ================================================
-- 6. Agent表 (agents)
-- ================================================
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,

    -- 基本信息
    name VARCHAR(100) NOT NULL,
    description TEXT,
    avatar VARCHAR(255),

    -- 配置信息
    model VARCHAR(50) DEFAULT 'glm-4.5',
    system_prompt TEXT,
    prompt_mode VARCHAR(20) DEFAULT 'default',

    -- 工具配置
    tools JSON,

    -- 智能体配置
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 2000,
    top_p DECIMAL(3,2) DEFAULT 1.0,

    -- 状态信息
    is_public BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- 使用统计
    usage_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2),

    -- 扩展配置
    config JSON,

    -- RAG配置
    enable_rag BOOLEAN DEFAULT FALSE,
    rag_index_name VARCHAR(100),
    rag_config TEXT,

    -- Web搜索配置
    enable_web_search BOOLEAN DEFAULT FALSE,
    web_search_config TEXT,

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    -- 外键约束
    CONSTRAINT fk_agents_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
);

-- 创建索引
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_agents_is_public ON agents(is_public);
CREATE INDEX idx_agents_created_at ON agents(created_at);
CREATE INDEX idx_agents_deleted_at ON agents(deleted_at);
CREATE INDEX idx_agents_is_deleted ON agents(is_deleted);
CREATE INDEX idx_agents_rag_index_name ON agents(rag_index_name);

-- 添加注释
COMMENT ON TABLE agents IS 'AI智能体表';
COMMENT ON COLUMN agents.tools IS '工具列表（JSON格式）';
COMMENT ON COLUMN agents.config IS '扩展配置（JSON格式）';
COMMENT ON COLUMN agents.rag_config IS 'RAG配置（JSON格式字符串）';
COMMENT ON COLUMN agents.web_search_config IS 'Web搜索配置（JSON格式字符串）';


-- ================================================
-- 7. 对话表 (conversations)
-- ================================================
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    agent_id INTEGER,

    -- 对话信息
    title VARCHAR(200) NOT NULL,
    description TEXT,

    -- 配置信息
    model VARCHAR(50),
    system_prompt TEXT,

    -- 状态信息
    status VARCHAR(20) DEFAULT 'active',
    is_pinned BOOLEAN DEFAULT FALSE,

    -- 统计信息
    message_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,

    -- 时间戳
    last_message_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    -- 外键约束
    CONSTRAINT fk_conversations_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_conversations_agent
        FOREIGN KEY (agent_id)
        REFERENCES agents(id)
        ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_agent_id ON conversations(agent_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_message_at ON conversations(last_message_at);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_deleted_at ON conversations(deleted_at);
CREATE INDEX idx_conversations_is_deleted ON conversations(is_deleted);

-- 添加注释
COMMENT ON TABLE conversations IS '对话表';
COMMENT ON COLUMN conversations.status IS '对话状态: active, archived, deleted';


-- ================================================
-- 8. 消息表 (messages)
-- ================================================
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,

    -- 消息内容
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,

    -- 元数据
    model VARCHAR(50),
    tokens INTEGER,
    cost DECIMAL(10,6),

    -- 工具调用记录
    tool_calls JSON,

    -- 反馈
    feedback INTEGER,
    feedback_text TEXT,

    -- 状态
    status VARCHAR(20) DEFAULT 'sent',

    -- 推理过程数据
    reasoning_data JSON,
    has_reasoning BOOLEAN DEFAULT FALSE,

    -- 时间戳
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,

    -- 外键约束
    CONSTRAINT fk_messages_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_messages_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
);

-- 创建索引
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_deleted_at ON messages(deleted_at);
CREATE INDEX idx_messages_is_deleted ON messages(is_deleted);

-- 添加注释
COMMENT ON TABLE messages IS '消息表';
COMMENT ON COLUMN messages.role IS '消息角色: user, assistant, system';
COMMENT ON COLUMN messages.status IS '消息状态: sent, pending, failed';
COMMENT ON COLUMN messages.feedback IS '用户反馈评分（1-5）';
COMMENT ON COLUMN messages.reasoning_data IS '推理过程数据（包含 content 和 length）';
COMMENT ON COLUMN messages.has_reasoning IS '是否包含推理信息';


-- ================================================
-- 9. 角色权限关联表 (role_permissions)
-- ================================================
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 复合主键
    PRIMARY KEY (role_id, permission_id),

    -- 外键约束
    CONSTRAINT fk_role_permissions_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_role_permissions_permission
        FOREIGN KEY (permission_id)
        REFERENCES permissions(id)
        ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX idx_role_permissions_role_id ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON role_permissions(permission_id);

-- 添加注释
COMMENT ON TABLE role_permissions IS '角色权限关联表（多对多）';


-- ================================================
-- 创建更新时间戳触发器（PostgreSQL）
-- ================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表创建触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permissions_updated_at BEFORE UPDATE ON permissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ================================================
-- 插入初始数据
-- ================================================

-- 插入默认角色
INSERT INTO roles (name, display_name, description, is_default) VALUES
    ('admin', '管理员', '系统管理员，拥有所有权限', FALSE),
    ('user', '普通用户', '普通用户角色', TRUE);

-- 插入默认权限
INSERT INTO permissions (name, display_name, description, resource, action) VALUES
    -- 用户权限
    ('user.create', '创建用户', '创建新用户', 'user', 'create'),
    ('user.read', '查看用户', '查看用户信息', 'user', 'read'),
    ('user.update', '更新用户', '更新用户信息', 'user', 'update'),
    ('user.delete', '删除用户', '删除用户', 'user', 'delete'),

    -- 角色权限
    ('role.create', '创建角色', '创建新角色', 'role', 'create'),
    ('role.read', '查看角色', '查看角色信息', 'role', 'read'),
    ('role.update', '更新角色', '更新角色信息', 'role', 'update'),
    ('role.delete', '删除角色', '删除角色', 'role', 'delete'),

    -- 权限权限
    ('permission.create', '创建权限', '创建新权限', 'permission', 'create'),
    ('permission.read', '查看权限', '查看权限信息', 'permission', 'read'),
    ('permission.update', '更新权限', '更新权限信息', 'permission', 'update'),
    ('permission.delete', '删除权限', '删除权限', 'permission', 'delete'),

    -- Agent权限
    ('agent.create', '创建Agent', '创建新Agent', 'agent', 'create'),
    ('agent.read', '查看Agent', '查看Agent信息', 'agent', 'read'),
    ('agent.update', '更新Agent', '更新Agent信息', 'agent', 'update'),
    ('agent.delete', '删除Agent', '删除Agent', 'agent', 'delete'),

    -- 对话权限
    ('conversation.create', '创建对话', '创建新对话', 'conversation', 'create'),
    ('conversation.read', '查看对话', '查看对话信息', 'conversation', 'read'),
    ('conversation.update', '更新对话', '更新对话信息', 'conversation', 'update'),
    ('conversation.delete', '删除对话', '删除对话', 'conversation', 'delete');

-- 为管理员角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin';

-- 为普通用户分配基本权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'user'
AND p.name IN (
    'agent.create', 'agent.read', 'agent.update', 'agent.delete',
    'conversation.create', 'conversation.read', 'conversation.update', 'conversation.delete'
);


-- ================================================
-- 完成
-- ================================================
-- 数据库结构创建完成
-- 共创建了 9 个表：
-- 1. users - 用户表
-- 2. roles - 角色表
-- 3. permissions - 权限表
-- 4. user_roles - 用户角色关联表
-- 5. user_permissions - 用户权限关联表
-- 6. agents - Agent表
-- 7. conversations - 对话表
-- 8. messages - 消息表
-- 9. role_permissions - 角色权限关联表
-- ================================================
