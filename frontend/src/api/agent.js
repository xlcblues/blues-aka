import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 30000 // 聊天接口需要更长的超时时间
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
      window.location.href = '/login'
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

// ==================== 智能体相关API ====================
export const agentApi = {
  // 获取智能体列表
  getAgents(params) {
    return api.get('/agent/agents', { params })
  },

  // 获取智能体详情
  getAgent(agentId) {
    return api.get(`/agent/agents/${agentId}`)
  },

  // 创建智能体
  createAgent(data) {
    return api.post('/agent/agents', data)
  },

  // 更新智能体
  updateAgent(agentId, data) {
    return api.put(`/agent/agents/${agentId}`, data)
  },

  // 删除智能体
  deleteAgent(agentId) {
    return api.delete(`/agent/agents/${agentId}`)
  }
}

// ==================== 对话相关API ====================
export const conversationApi = {
  // 获取对话列表
  getConversations(params) {
    return api.get('/conversation/conversations', { params })
  },

  // 获取对话详情
  getConversation(conversationId) {
    return api.get(`/conversation/conversations/${conversationId}`)
  },

  // 创建对话
  createConversation(data) {
    return api.post('/conversation/conversations', data)
  },

  // 更新对话
  updateConversation(conversationId, data) {
    return api.put(`/conversation/conversations/${conversationId}`, data)
  },

  // 删除对话
  deleteConversation(conversationId) {
    return api.delete(`/conversation/conversations/${conversationId}`)
  },

  // 归档对话
  archiveConversation(conversationId) {
    return api.patch(`/conversation/conversations/${conversationId}/archive`)
  }
}

// ==================== 聊天相关API ====================
export const chatApi = {
  // 发送消息
  chat(conversationId, data) {
    return api.post(`/chat/conversations/${conversationId}/chat`, data)
  },

  // 获取消息历史
  getMessages(conversationId, params) {
    return api.get(`/chat/conversations/${conversationId}/messages`, { params })
  },

  // 消息反馈
  messageFeedback(messageId, data) {
    return api.post(`/chat/messages/${messageId}/feedback`, data)
  },

  // 重新生成消息
  regenerateMessage(conversationId, data) {
    return api.post(`/chat/conversations/${conversationId}/regenerate`, data)
  }
}

// ==================== 用户统计API ====================
export const statsApi = {
  // 获取用户统计
  getUserStats() {
    return api.get('/users/me/stats')
  }
}

export default {
  agent: agentApi,
  conversation: conversationApi,
  chat: chatApi,
  stats: statsApi
}
