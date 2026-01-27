import axios from 'axios'

// 创建 axios 实例（使用与 agent.js 相同的配置）
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 60000 // 知识库上传可能需要更长的超时时间
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
    console.error('Knowledge Base API Error:', error)

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

// ==================== 知识库相关API ====================
export const knowledgeBaseApi = {
  // 获取知识库列表
  getKnowledgeBases() {
    return api.get('/conversation/rag/indexes')
  },

  // 获取知识库详情
  getKnowledgeBaseInfo(indexName) {
    return api.get(`/conversation/rag/indexes/${indexName}`)
  },

  // 创建知识库
  createKnowledgeBase(formData) {
    return api.post('/conversation/rag/indexes', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 删除知识库
  deleteKnowledgeBase(indexName) {
    return api.delete(`/conversation/rag/indexes/${indexName}`)
  },

  // 向知识库添加文档
  addDocumentToKnowledgeBase(indexName, formData) {
    return api.post(`/conversation/rag/indexes/${indexName}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 获取支持的文件格式
  getSupportedFormats() {
    return api.get('/conversation/rag/supported-formats')
  },

  // 切换对话的 RAG 模式
  toggleConversationRAG(conversationId, data) {
    return api.patch(`/conversation/conversations/${conversationId}/rag`, data)
  }
}

export default knowledgeBaseApi
