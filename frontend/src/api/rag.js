import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 30000
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
    console.error('RAG API Error:', error)

    // 如果收到401响应，清除认证状态
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('isLoggedIn')
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('username')
      window.location.href = '/login'
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

// ==================== RAG评估相关API ====================
export const ragApi = {
  // 提交RAG回答反馈
  submitFeedback(data) {
    return api.post('/conversation/rag/feedback', data)
  },

  // 获取RAG性能指标（管理员）
  getMetrics(summary = true) {
    return api.get('/conversation/rag/metrics', {
      params: { summary }
    })
  },

  // 获取支持的文件格式
  getSupportedFormats() {
    return api.get('/conversation/rag/supported-formats')
  }
}

export default ragApi
