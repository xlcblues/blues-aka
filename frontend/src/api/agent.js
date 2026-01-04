import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '',
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

    return Promise.reject(error)
  }
)

// ==================== 智能体相关API ====================
export const agentApi = {
  // 获取智能体列表
  getAgents(params) {
    return api.get('/api/v1/agents', { params })
  },

  // 获取智能体详情
  getAgent(agentId) {
    return api.get(`/api/v1/agents/${agentId}`)
  },

  // 创建智能体
  createAgent(data) {
    return api.post('/api/v1/agents', data)
  },

  // 更新智能体
  updateAgent(agentId, data) {
    return api.put(`/api/v1/agents/${agentId}`, data)
  },

  // 删除智能体
  deleteAgent(agentId) {
    return api.delete(`/api/v1/agents/${agentId}`)
  }
}

// ==================== 对话相关API ====================
export const conversationApi = {
  // 获取对话列表
  getConversations(params) {
    return api.get('/api/v1/conversations', { params })
  },

  // 获取对话详情
  getConversation(conversationId) {
    return api.get(`/api/v1/conversations/${conversationId}`)
  },

  // 创建对话
  createConversation(data) {
    return api.post('/api/v1/conversations', data)
  },

  // 更新对话
  updateConversation(conversationId, data) {
    return api.put(`/api/v1/conversations/${conversationId}`, data)
  },

  // 删除对话
  deleteConversation(conversationId) {
    return api.delete(`/api/v1/conversations/${conversationId}`)
  },

  // 归档对话
  archiveConversation(conversationId) {
    return api.patch(`/api/v1/conversations/${conversationId}/archive`)
  }
}

// ==================== 聊天相关API ====================
export const chatApi = {
  // 发送消息
  chat(conversationId, data) {
    return api.post(`/api/v1/conversations/${conversationId}/chat`, data)
  },

  // 获取消息历史
  getMessages(conversationId, params) {
    return api.get(`/api/v1/conversations/${conversationId}/messages`, { params })
  },

  // 消息反馈
  messageFeedback(messageId, data) {
    return api.post(`/api/v1/messages/${messageId}/feedback`, data)
  },

  // 重新生成消息
  regenerateMessage(conversationId, data) {
    return api.post(`/api/v1/conversations/${conversationId}/regenerate`, data)
  }
}

// ==================== 用户统计API ====================
export const statsApi = {
  // 获取用户统计
  getUserStats() {
    return api.get('/api/v1/users/me/stats')
  }
}

export default {
  agent: agentApi,
  conversation: conversationApi,
  chat: chatApi,
  stats: statsApi
}
