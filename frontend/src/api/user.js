import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)

    // 如果收到401响应，清除认证状态
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('isLoggedIn')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('username')
    }

    // 提取后端返回的错误信息
    if (error.response && error.response.data) {
      const errorData = error.response.data
      // 将后端错误信息附加到 error 对象上
      error.backendMessage = errorData.message || errorData.error_code || '服务器错误'
      error.backendErrorCode = errorData.code || errorData.error_code
    }

    return Promise.reject(error)
  }
)

export const userApi = {
  // 获取用户列表
  getUsers(params) {
    return api.get('/user/users', { params })
  },

  // 创建用户
  createUser(data) {
    return api.post('/user/users', data)
  },

  // 更新用户
  updateUser(id, data) {
    return api.put(`/user/users/${id}`, data)
  },

  // 删除用户
  deleteUser(id) {
    return api.delete(`/user/users/${id}`)
  },

  // 修改密码
  changePassword(id, data) {
    return api.post(`/user/users/${id}/change-password`, data)
  }
}

export const authApi = {
  // 用户登录
  login(data) {
    return api.post('/auth/login', data)
  },

  // 用户登出
  logout() {
    return api.post('/auth/logout')
  },

  // 用户注册
  register(data) {
    return api.post('/auth/register', data)
  },

  // 获取当前用户信息
  getCurrentUser() {
    return api.get('/auth/me')
  }
}