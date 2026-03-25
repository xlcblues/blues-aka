/**
 * RAG索引管理API
 *
 * 提供RAG索引管理的接口调用方法
 */
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 60000 // 索引操作可能需要较长时间
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
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
  (error) => {
    const message = error.response?.data?.message || error.message || '请求失败'

    // 处理特殊错误码
    if (error.response?.status === 401) {
      // 未授权,清除token并跳转登录
      localStorage.removeItem('token')
      window.location.href = '/login'
    }

    return Promise.reject(new Error(message))
  }
)

/**
 * RAG索引管理API
 */
export const ragIndexApi = {
  /**
   * 获取所有索引列表
   * @param {Object} params - 查询参数
   * @param {boolean} params.includeHealth - 是否包含健康检查结果
   * @returns {Promise} 索引列表
   */
  listIndexes(params = {}) {
    return api.get('/rag/index/list', { params })
  },

  /**
   * 获取索引详细信息
   * @param {string} indexName - 索引名称
   * @returns {Promise} 索引详细信息
   */
  getIndexInfo(indexName) {
    return api.get(`/rag/index/${indexName}/info`)
  },

  /**
   * 检查索引健康状态
   * @param {string} indexName - 索引名称
   * @param {Object} params - 查询参数
   * @param {boolean} params.deepCheck - 是否进行深度检查
   * @returns {Promise} 健康检查报告
   */
  checkIndexHealth(indexName, params = {}) {
    return api.get(`/rag/index/${indexName}/health`, { params })
  },

  /**
   * 获取所有索引的健康摘要
   * @returns {Promise} 健康摘要
   */
  getHealthSummary() {
    return api.get('/rag/index/health-summary')
  },

  /**
   * 获取索引版本历史
   * @param {string} indexName - 索引名称
   * @returns {Promise} 版本历史列表
   */
  getIndexVersions(indexName) {
    return api.get(`/rag/index/${indexName}/versions`)
  },

  /**
   * 重建索引
   * @param {string} indexName - 索引名称
   * @param {Object} data - 请求数据
   * @param {string} data.description - 索引描述
   * @param {Array} data.documents - 文档列表
   * @returns {Promise} 操作结果
   */
  rebuildIndex(indexName, data) {
    return api.post(`/rag/index/${indexName}/rebuild`, data)
  },

  /**
   * 增量更新索引
   * @param {string} indexName - 索引名称
   * @param {Object} data - 请求数据
   * @param {Array} data.addDocuments - 要添加的文档列表
   * @param {Array} data.deleteDocumentIds - 要删除的文档ID列表
   * @returns {Promise} 操作结果
   */
  updateIndexIncremental(indexName, data) {
    return api.put(`/rag/index/${indexName}/update`, data)
  },

  /**
   * 删除索引
   * @param {string} indexName - 索引名称
   * @returns {Promise} 操作结果
   */
  deleteIndex(indexName) {
    return api.delete(`/rag/index/${indexName}`)
  }
}

export default ragIndexApi
