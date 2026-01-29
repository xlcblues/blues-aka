<div align="center">

# Blues AKA

# 🤖 智能助手平台

一个基于 AI 的智能对话助手平台，支持自定义 Agent、多轮对话、知识库检索等功能。

**[Flask]** + **[Vue 3]** + **[智谱 AI GLM]** + **[RAG]** = 现代化 AI 助手平台

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4%2B-brightgreen)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📖 项目简介

**Blues AKA** 是一个功能强大的 AI 智能助手平台，基于智谱 AI GLM 大语言模型构建。平台提供了完整的用户管理、自定义 Agent 创建、多轮对话、知识库管理等功能，适用于构建各种场景的智能助手应用。

### 🎯 核心功能

- **🤖 自定义 Agent 管理** - 创建、配置和管理多个 AI 智能体
- **💬 智能对话系统** - 支持流式输出的多轮对话
- **📚 知识库集成** - 基于 RAG 的文档检索增强生成
- **👥 用户权限管理** - 完整的用户认证和权限控制
- **🎨 现代化界面** - 基于 Vue 3 + Element Plus 的响应式 UI
- **🔒 JWT 认证** - 安全的 token 认证机制

---

## ✨ 核心特性

### 🤖 Agent 智能体系统

- **自定义 Agent** - 支持创建具有不同角色和能力的智能体
- **灵活配置** - 可调整模型参数、提示词、工具等
- **公开/私有** - 支持 Agent 的公开共享和私有使用
- **版本管理** - Agent 配置的更新和版本控制

**Agent 配置选项：**
- 模型选择（GLM-4.5、GLM-4 等）
- 温度参数控制
- 系统提示词定制
- 工具调用能力
- 最大 token 数限制

### 💬 对话管理系统

- **多轮对话** - 完整的对话历史管理
- **流式输出** - 实时流式响应，提升用户体验
- **消息重生成** - 支持重新生成 AI 响应
- **对话分支** - 支持多个独立对话会话
- **上下文保持** - 自动维护对话上下文

**对话功能：**
- 实时流式响应
- 消息历史记录
- 对话标题自动生成
- 消息重新生成
- 对话归档管理

### 📚 RAG 知识库

- **文档上传** - 支持多种格式的文档导入
- **向量化存储** - 自动文档向量化处理
- **智能检索** - 基于语义相似度的文档检索
- **知识增强** - 检索增强生成提升回答准确性

**知识库功能：**
- 文档批量导入
- 文本分块处理
- 向量索引管理
- 相似度检索
- 检索结果优化

### 👥 用户管理系统

- **用户认证** - JWT token 认证机制
- **权限管理** - 普通用户和管理员权限
- **用户状态** - 支持多种用户状态管理
- **安全登录** - 密码加密存储

**用户功能：**
- 用户注册/登录
- 密码加密存储
- Token 自动刷新
- 权限分级管理
- 用户状态控制

---

## 🛠️ 技术栈

### 后端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **Flask** | 2.0+ | Python Web 框架 |
| **SQLAlchemy** | - | ORM 数据库操作 |
| **PostgreSQL** | 12+ | 关系型数据库 |
| **JWT** | - | 身份认证 |
| **智谱 AI** | GLM-4.5 | 大语言模型 API |
| **LangChain** | - | LLM 应用框架 |
| **FAISS** | - | 向量数据库 |

### 前端技术

| 技术 | 版本 | 说明 |
|------|------|------|
| **Vue** | 3.4+ | 渐进式 JavaScript 框架 |
| **Vite** | 5.0+ | 前端构建工具 |
| **Element Plus** | 2.4+ | Vue 3 UI 组件库 |
| **Pinia** | 2.1+ | 状态管理 |
| **Vue Router** | 4.2+ | 路由管理 |
| **Axios** | 1.6+ | HTTP 客户端 |

### AI & 工具

- **智谱 AI GLM** - 大语言模型
- **Embedding** - 文本向量化
- **FAISS** - 向量相似度搜索
- **Marshmallow** - 数据序列化验证
- **APScheduler** - 定时任务调度

---

## 📁 项目结构

```
blues-aka/
├── main.py                      # 应用程序入口
├── .env                         # 环境配置文件
├── requirements.txt             # Python 依赖
│
├── blues_aka/                   # 后端主应用
│   ├── __init__.py             # 应用工厂
│   ├── config/                 # 配置管理
│   │   └── config.py           # 配置类定义
│   ├── extensions.py           # 扩展初始化
│   ├── blueprints.py           # 蓝图注册
│   ├── jwt.py                  # JWT 配置
│   ├── logger.py               # 日志配置
│   │
│   ├── user/                   # 用户模块
│   │   ├── models.py           # 用户数据模型
│   │   ├── routes/             # 用户路由
│   │   │   ├── auth.py         # 认证接口
│   │   │   └── user.py         # 用户管理
│   │   └── schemas.py          # 数据验证模式
│   │
│   ├── Agent/                  # Agent 模块
│   │   ├── BaseAgent.py        # Agent 基类
│   │   ├── models/             # 数据模型
│   │   │   ├── agent.py        # Agent 模型
│   │   │   ├── conversation.py # 对话模型
│   │   │   └── message.py      # 消息模型
│   │   ├── routes/             # 路由接口
│   │   │   ├── agent.py        # Agent 接口
│   │   │   ├── conversation.py # 对话接口
│   │   │   └── chat.py         # 聊天接口
│   │   └── schemas/            # 数据模式
│   │
│   ├── rag/                    # RAG 模块
│   │   ├── models.py           # 知识库模型
│   │   └── routes.py           # 知识库接口
│   │
│   ├── common/                 # 公共模块
│   │   ├── error_codes.py      # 异常码定义
│   │   ├── exception.py        # 异常处理
│   │   ├── response.py         # 响应封装
│   │   └── responseapi.py      # API 响应处理
│   │
│   └── tasks/                  # 定时任务
│       ├── scheduler.py        # 任务调度器
│       └── routes.py           # 任务接口
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── Login.vue      # 登录页
│   │   │   ├── AgentList.vue  # Agent 列表
│   │   │   ├── ConversationList.vue  # 对话列表
│   │   │   ├── Chat.vue       # 聊天界面
│   │   │   └── UserList.vue   # 用户管理
│   │   ├── components/        # 公共组件
│   │   ├── stores/            # Pinia 状态管理
│   │   │   ├── auth.js        # 认证状态
│   │   │   └── user.js        # 用户状态
│   │   ├── router/            # 路由配置
│   │   ├── api/               # API 请求
│   │   └── App.vue            # 根组件
│   ├── package.json           # 前端依赖
│   └── vite.config.js         # Vite 配置
│
└── docs/                       # 文档目录
    ├── 前端路由刷新问题解决方案.md
    └── Agent路由异常码更新记录.md
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **PostgreSQL**: 12+
- **智谱 AI API Key**

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/blues-aka.git
cd blues-aka
```

#### 2. 配置环境变量

创建 `.env` 文件并配置以下环境变量：

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/blues_aka

# JWT 密钥（至少32位）
JWT_SECRET_KEY=your-super-secret-jwt-key-at-least-32-chars

# 智谱 AI API
ZHIPU_API_KEY=your-zhipu-ai-api-key
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4

# Flask 配置
FLASK_CONFIG=Dev
SECRET_KEY=your-flask-secret-key

# 日志配置
LOG_LEVEL=INFO
```

#### 3. 安装后端依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install flask flask-sqlalchemy flask-jwt-extended
pip install psycopg2-binary marshmallow pydantic
pip install langchain langchain-community
pip install zhipuai faiss-cpu
pip install apscheduler python-dotenv
```

#### 4. 初始化数据库

```bash
# 创建数据库
createdb blues_aka

# 初始化表结构
python -c "from blues_aka import create_app; from blues_aka.extensions import db; app = create_app('Dev'); app.app_context().push(); db.create_all()"
```

#### 5. 启动后端服务

```bash
python main.py
```

后端服务将运行在 `http://localhost:5000`

#### 6. 安装前端依赖

```bash
cd frontend
npm install
```

#### 7. 启动前端开发服务器

```bash
npm run dev
```

前端服务将运行在 `http://localhost:3001`

---

## 📊 数据模型

### Agent 智能体

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| user_id | BigInteger | 创建用户ID |
| name | String(100) | Agent 名称 |
| description | Text | 描述信息 |
| avatar | String(50) | 头像（emoji） |
| model | String(50) | 使用的模型（glm-4.5等） |
| system_prompt | Text | 系统提示词 |
| temperature | Float | 温度参数（0.0-2.0） |
| max_tokens | Integer | 最大 token 数 |
| is_public | Boolean | 是否公开 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### Conversation 对话

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| user_id | BigInteger | 用户ID |
| agent_id | BigInteger | 关联的Agent ID |
| title | String(200) | 对话标题 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### Message 消息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| conversation_id | BigInteger | 对话ID |
| role | String(20) | 角色（user/assistant/system） |
| content | Text | 消息内容 |
| created_at | DateTime | 创建时间 |

### User 用户

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| username | String(50) | 用户名 |
| email | String(100) | 邮箱 |
| password_hash | String(255) | 密码哈希 |
| is_admin | Boolean | 是否管理员 |
| status | String(20) | 状态 |
| created_at | DateTime | 创建时间 |

---

## 🔌 API 接口

### 认证接口 `/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/logout` | 用户登出 |
| POST | `/auth/refresh` | 刷新 Token |
| GET | `/auth/me` | 获取当前用户 |

### Agent 接口 `/agent`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/agent/agents` | 创建 Agent |
| GET | `/agent/agents` | 获取 Agent 列表 |
| GET | `/agent/agents/<id>` | 获取 Agent 详情 |
| PUT | `/agent/agents/<id>` | 更新 Agent |
| DELETE | `/agent/agents/<id>` | 删除 Agent |

### 对话接口 `/conversation`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/conversation/conversations` | 创建对话 |
| GET | `/conversation/conversations` | 获取对话列表 |
| GET | `/conversation/conversations/<id>` | 获取对话详情 |
| DELETE | `/conversation/conversations/<id>` | 删除对话 |

### 聊天接口 `/chat`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat/messages` | 发送消息（流式） |
| POST | `/chat/regenerate` | 重新生成 |
| GET | `/chat/messages/<id>` | 获取消息历史 |

---

## 🎨 功能截图

### Agent 管理
- ✅ 创建自定义 Agent
- ✅ Agent 列表展示
- ✅ Agent 配置编辑
- ✅ 公开/私有设置

### 对话功能
- ✅ 多轮对话
- ✅ 流式输出
- ✅ 消息重新生成
- ✅ 对话历史管理

### 用户管理
- ✅ 用户列表
- ✅ 权限管理
- ✅ 状态控制
- ✅ 用户信息编辑

---

## 🔧 配置说明

### 开发环境配置

```python
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"
```

### 生产环境配置

```python
class ProductionConfig(BaseConfig):
    DEBUG = False
    LOG_LEVEL = "INFO"
```

### Agent 模型配置

```python
default_model = "glm-4.5"          # 默认模型
default_temperature = 0.7          # 默认温度
default_max_token = 20000          # 默认最大token
default_streaming = True           # 流式输出
```

### RAG 配置

```python
embedding_model = "embedding-3"    # Embedding模型
chunk_size = 1000                  # 文本分块大小
chunk_overlap = 200                # 分块重叠
retriever_k = 4                    # 检索数量
vector_store_type = "faiss"        # 向量库类型
```

---

## 🔒 安全特性

- **JWT Token 认证** - 安全的身份验证机制
- **Token 自动刷新** - 无缝的用户体验
- **密码加密存储** - 使用 Werkzeug 安全哈希
- **CORS 跨域保护** - 配置允许的跨域来源
- **SQL 注入防护** - ORM 参数化查询
- **XSS 防护** - 前端数据转义处理
- **输入验证** - Marshmallow 数据验证

---

## 📝 开发指南

### 添加新的 Agent

1. 在数据库中创建 Agent 记录
2. 配置 Agent 参数（模型、提示词等）
3. 在对话中使用该 Agent

### 自定义知识库

1. 准备文档数据（PDF、TXT、MD等）
2. 通过 API 上传文档
3. 系统自动处理和向量化
4. 在对话中自动检索相关知识

### 扩展 API 接口

1. 在相应模块的 `routes/` 目录添加路由
2. 创建对应的 Schema 进行数据验证
3. 在 `blueprints.py` 中注册蓝图
4. 更新前端 API 调用

---

## 🐛 常见问题

### 1. 数据库连接失败

检查 `DATABASE_URL` 是否正确配置，确保 PostgreSQL 服务正在运行。

### 2. 智谱 AI 调用失败

确认 `ZHIPU_API_KEY` 已正确设置，并检查 API 余额是否充足。

### 3. 前端路由刷新 404

开发环境使用 Vite 的 history fallback，生产环境参考 [前端路由刷新问题解决方案](docs/前端路由刷新问题解决方案.md)。

### 4. Token 过期问题

系统实现了自动 token 刷新机制，如果仍有问题，检查 `JWT_SECRET_KEY` 配置。

---

## 📚 文档

- [前端路由刷新问题解决方案](docs/前端路由刷新问题解决方案.md)
- [Agent路由异常码更新记录](docs/Agent路由异常码更新记录.md)
- [后端代码异常处理问题分析报告](后端代码异常处理问题分析报告.md)
- [异构代码体系文档](异构代码体系文档.md)

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 👥 作者

Blues AKA Team

---

## 🙏 致谢

- [智谱 AI](https://open.bigmodel.cn/) - 提供强大的 GLM 大语言模型
- [Flask](https://flask.palletsprojects.com/) - 优秀的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - 优秀的 Vue 3 组件库
- [LangChain](https://langchain.com/) - 强大的 LLM 应用开发框架

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ by Blues AKA Team

</div>