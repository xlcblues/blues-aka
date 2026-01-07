/**
 * 错误处理工具函数
 */

/**
 * 从错误对象中提取友好的错误消息
 * @param {Error} error - 错误对象
 * @returns {string} 友好的错误消息
 */
export function getErrorMessage(error) {
  // 优先使用后端返回的错误信息
  if (error.backendMessage) {
    return error.backendMessage
  }

  // 检查 response.data.message
  if (error.response?.data?.message) {
    return error.response.data.message
  }

  // 检查 response.data 中的其他错误字段
  if (error.response?.data?.error) {
    return error.response.data.error
  }

  // 检查 HTTP 状态码对应的默认消息
  if (error.response?.status) {
    const statusMessages = {
      400: '请求参数错误',
      401: '未授权，请重新登录',
      403: '没有权限访问',
      404: '请求的资源不存在',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务暂时不可用',
      504: '请求超时'
    }
    const message = statusMessages[error.response.status]
    if (message) {
      return message
    }
  }

  // 使用错误对象的 message 属性
  if (error.message) {
    return error.message
  }

  // 默认错误消息
  return '操作失败，请稍后重试'
}

/**
 * 显示错误消息
 * @param {Error} error - 错误对象
 * @param {Object} options - 选项
 * @param {number} options.duration - 显示时长(毫秒)
 * @param {boolean} options.showConsole - 是否在控制台显示详细错误
 */
export function showError(error, options = {}) {
  const {
    duration = 3000,
    showConsole = true
  } = options

  const message = getErrorMessage(error)

  if (showConsole) {
    console.error('Error:', error)
    console.error('Error Message:', message)
  }

  return message
}

/**
 * 处理 API 错误并返回用户友好的消息
 * @param {Error} error - 错误对象
 * @returns {Object} 包含错误信息的对象
 */
export function handleApiError(error) {
  const result = {
    message: getErrorMessage(error),
    code: null,
    status: null,
    originalError: error
  }

  if (error.backendErrorCode) {
    result.code = error.backendErrorCode
  }

  if (error.response?.status) {
    result.status = error.response.status
  }

  return result
}
