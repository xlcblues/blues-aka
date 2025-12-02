# Blues AKA

一个基于 Flask 的用户管理系统，提供完整的用户认证和数据管理功能。

## 项目简介

Blues AKA 是一个现代化的 Web 应用程序框架，专注于用户管理和数据验证。该项目采用 Flask 框架构建，结合 PostgreSQL 数据库，提供了可扩展的蓝图架构设计。

## 核心特性

### 🔐 用户管理系统
- **用户注册与认证**：安全的用户注册和登录功能
- **密码安全**：使用 Werkzeug 进行密码哈希和验证
- **邮箱验证**：支持不区分大小写的邮箱唯一性验证
- **用户状态管理**：支持 active、inactive、suspended、deleted 等状态

### 🗄️ 数据库设计
- **PostgreSQL 数据库**：高性能的关系型数据库
- **自动化时间戳**：自动管理创建时间和更新时间
- **数据库触发器**：确保数据一致性
- **数据模型验证**：完整的字段验证和约束

### 🏗️ 架构设计
- **蓝图模块化**：基于 Flask Blueprint 的模块化架构
- **扩展系统**：灵活的扩展初始化机制
- **环境配置**：支持开发和生产环境配置
- **数据序列化**：使用 Marshmallow 进行数据验证和序列化

## 技术栈

### 后端框架
- **Flask**：轻量级 Python Web 框架
- **Flask-SQLAlchemy**：数据库 ORM
- **Flask-Marshmallow**：数据序列化和验证
- **SQLAlchemy**：强大的数据库工具包

### 数据库
- **PostgreSQL**：企业级关系型数据库
- **CITEXT**：不区分大小写的文本类型
- **数据库触发器**：自动化的数据完整性保证

### 安全
- **Werkzeug Security**：密码哈希和验证
- **数据验证**：输入数据的安全验证
- **状态管理**：用户状态的完整控制

## 项目结构

```
blues-aka/
├── main.py                 # 应用程序入口
├── blues_aka/              # 主应用包
│   ├── __init__.py         # 应用工厂模式
│   ├── config.py           # 配置管理
│   ├── extensions.py       # 扩展初始化
│   ├── blueprints.py       # 蓝图注册
│   ├── user/               # 用户模块
│   │   ├── __init__.py
│   │   ├── models.py       # 用户数据模型
│   │   ├── routes.py       # 用户路由
│   │   └── schemas.py      # 用户数据模式
│   └── Agent/              # AI Agent 模块
│       ├── __init__.py
│       └── routes.py       # Agent 路由
├── .git/                   # Git 版本控制
├── .idea/                  # IDE 配置
└── .vscode/                # VSCode 配置
```

## 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- pip

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd blues-aka
   ```

2. **安装依赖**
   ```bash
   pip install flask flask-sqlalchemy flask-marshmallow marshmallow-sqlalchemy werkzeug psycopg2-binary
   ```

3. **数据库配置**
   - 创建 PostgreSQL 数据库 `blues`
   - 修改 `blues_aka/config.py` 中的数据库连接信息

4. **初始化数据库**
   ```bash
   python main.py
   ```

5. **运行应用**
   ```bash
   python main.py
   ```

### 环境配置

项目支持多环境配置，通过 `FLASK_CONFIG` 环境变量控制：

- **开发环境**：`FLASK_CONFIG=Dev`
- **生产环境**：`FLASK_CONFIG=Prod`

## 数据模型

### 用户模型 (User)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键，自动递增 |
| username | String(50) | 用户名，唯一 |
| email | CITEXT | 邮箱，不区分大小写唯一 |
| password_hash | String(255) | 密码哈希值 |
| nickname | String(100) | 用户昵称（可选） |
| status | String(20) | 用户状态：active/inactive/suspended/deleted |
| is_verified | Boolean | 是否已验证 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |
| last_login_at | DateTime | 最后登录时间 |

## API 端点

### 用户模块 (/user)
- 前缀：`/user`
- 蓝图：`user_bp`

### Agent 模块
- 蓝图：`agent_bp`

## 开发指南

### 添加新模块

1. 在 `blues_aka/` 下创建新的模块目录
2. 实现 `models.py`、`routes.py`、`schemas.py`
3. 在 `blues_aka/blueprints.py` 中注册新蓝图

### 数据库迁移

项目使用 SQLAlchemy 进行数据库操作，包含自动时间戳管理：

```python
# 创建更新时间触发器
User.create_updated_at_trigger()
```

### 数据验证

使用 Marshmallow 进行数据验证：

```python
# 用户模式验证
user_schema = UserSchema()
users_schema = UserSchema(many=True)
```

## 配置说明

### 开发环境配置 (Dev)
```python
class Dev:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:123456@localhost:5432/blues"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### 生产环境配置 (Prod)
继承开发环境配置，可根据需要添加生产特定设置。

## 安全特性

- **密码安全**：使用 Werkzeug 的安全密码哈希
- **数据验证**：输入数据的完整验证
- **状态管理**：用户状态的严格控制
- **邮箱验证**：支持邮箱唯一性验证

## 扩展性

- **模块化架构**：基于蓝图的模块化设计
- **扩展系统**：灵活的扩展初始化机制
- **配置管理**：支持多环境配置
- **数据模型**：可扩展的数据模型设计

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请通过 Issues 联系我们。

---

**Blues AKA** - 构建现代化用户管理系统的理想选择