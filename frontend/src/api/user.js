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

// 定义 authApi，需要在响应拦截器之前
const authApi = {
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
  },

  // 刷新访问令牌
  refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      return Promise.reject(new Error('No refresh token available'))
    }

    // 创建一个不使用拦截器的 axios 实例来避免循环
    const refreshApi = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
      timeout: 10000
    })

    return refreshApi.post('/auth/refresh', {}, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    })
  }
}

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  async error => {
    console.error('API Error:', error)

    const originalRequest = error.config

    // 如果收到401响应且未尝试过刷新token
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // 尝试刷新token
        const response = await authApi.refreshToken()

        // 保存新的token
        const newAccessToken = response.data.access_token
        localStorage.setItem('access_token', newAccessToken)

        // 更新请求头
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`

        // 重试原始请求
        return api(originalRequest)
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError)

        // 刷新失败，清除所有认证状态并跳转登录
        localStorage.removeItem('isLoggedIn')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('username')
        localStorage.removeItem('is_admin')
        localStorage.removeItem('user_id')

        // 使用replace而不是href，避免用户按返回键回到之前的页面
        window.location.replace('/login')

        return Promise.reject(refreshError)
      }
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

export { authApi }
