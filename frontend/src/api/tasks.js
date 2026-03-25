/**
 * 定时任务管理API
 *
 * 提供定时任务管理的接口调用方法
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 30000
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    console.error('Tasks API Error:', error)

    const originalRequest = error.config

    // 如果收到401响应且未尝试过刷新token
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // 尝试刷新token
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }

        const refreshApi = axios.create({
          baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
          timeout: 10000
        })

        const response = await refreshApi.post('/auth/refresh', {}, {
          headers: {
            'Authorization': `Bearer ${refreshToken}`
          }
        })

        if (response.data && response.data.access_token) {
          const newAccessToken = response.data.access_token
          localStorage.setItem('access_token', newAccessToken)

          // 更新请求头并重试原始请求
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError)

        // 刷新失败，清除所有认证状态并跳转登录
        localStorage.removeItem('isLoggedIn')
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('username')
        localStorage.removeItem('is_admin')
        localStorage.removeItem('user_id')

        window.location.replace('/login')
        return Promise.reject(refreshError)
      }
    }

    // 提取后端返回的错误信息
    if (error.response && error.response.data) {
      const errorData = error.response.data
      error.backendMessage = errorData.message || errorData.error_code || '服务器错误'
      error.backendErrorCode = errorData.code || errorData.error_code
    }

    return Promise.reject(error)
  }
)

/**
 * 定时任务管理API
 */
export const tasksApi = {
  /**
   * 获取所有定时任务列表
   * @returns {Promise} 任务列表
   */
  getJobs() {
    return api.get('/admin/tasks/jobs')
  },

  /**
   * 手动触发用户状态更新任务
   * @returns {Promise} 执行结果
   */
  triggerUpdateUserStatus() {
    return api.post('/admin/tasks/update-user-status')
  },

  /**
   * 手动触发用户清理任务
   * @returns {Promise} 执行结果
   */
  triggerCleanupUsers() {
    return api.post('/admin/tasks/cleanup-users')
  },

  /**
   * 获取用户活跃度统计信息
   * @returns {Promise} 统计信息
   */
  getUserStats() {
    return api.get('/admin/tasks/user-stats')
  }
}

export default tasksApi
