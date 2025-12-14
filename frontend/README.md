# Blues AKA 前端项目

基于 Vue 3 + Element Plus 构建的现代化用户管理系统前端界面。

## 项目特性

- 🚀 **Vue 3 + Vite** - 使用最新的 Vue 3 组合式 API 和 Vite 构建工具
- 🎨 **Element Plus** - 基于 Vue 3 的企业级 UI 组件库
- 📱 **响应式设计** - 适配不同屏幕尺寸
- 🔍 **高级搜索** - 支持多条件搜索和排序
- 📄 **分页功能** - 支持自定义分页大小
- ✨ **优雅界面** - 现代化的设计风格和交互体验

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 UI 组件库
- **Vue Router** - 官方路由管理器
- **Axios** - HTTP 请求库
- **Vite** - 新一代前端构建工具

## 项目结构

```
frontend/
├── index.html              # HTML 模板
├── package.json            # 项目依赖配置
├── vite.config.js          # Vite 配置文件
├── src/
│   ├── main.js             # 应用入口文件
│   ├── App.vue             # 根组件
│   ├── router/
│   │   └── index.js        # 路由配置
│   ├── api/
│   │   └── user.js         # 用户 API 接口
│   ├── views/
│   │   └── UserList.vue    # 用户列表页面
│   ├── components/         # 公共组件
│   ├── utils/              # 工具函数
│   └── assets/             # 静态资源
└── README.md               # 项目说明文档
```

## 功能特性

### 用户管理
- ✅ 用户列表展示
- ✅ 用户搜索和筛选
- ✅ 用户创建
- ✅ 用户编辑
- ✅ 用户删除
- ✅ 分页功能
- ✅ 排序功能

### 界面特性
- 🎨 现代化设计风格
- 📱 响应式布局
- 🔍 实时搜索
- 📊 表格排序
- 🎯 状态标签显示
- ⏰ 时间格式化显示

## 快速开始

### 安装依赖
```bash
cd frontend
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 预览构建结果
```bash
npm run preview
```

## API 接口

前端通过代理的方式与后端 Flask API 通信，所有请求都会被代理到 `http://localhost:5000`。

### 用户相关接口
- `GET /user/users` - 获取用户列表
- `POST /user/users` - 创建用户
- `PUT /user/users/:id` - 更新用户
- `DELETE /user/users/:id` - 删除用户

## 配置说明

### 代理配置
在 `vite.config.js` 中配置了代理，将 `/api` 开头的请求代理到后端服务器：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

### 环境要求
- Node.js 16+
- npm 7+

## 浏览器支持
- Chrome
- Firefox
- Safari
- Edge

## 开发说明

### 组件结构
- 使用 Vue 3 组合式 API (Composition API)
- 采用 `<script setup>` 语法
- 使用 Element Plus 组件库

### 状态管理
当前项目较为简单，使用组件内的响应式状态进行管理。如项目复杂度增加，可考虑引入 Pinia 进行状态管理。

### 样式规范
- 使用 Element Plus 的设计规范
- 组件级样式使用 scoped
- 全局样式在 App.vue 中定义

## 后端集成

确保后端 Flask 服务运行在 `http://localhost:5000`，并且已配置正确的 CORS 策略允许前端访问。

## 许可证

MIT License