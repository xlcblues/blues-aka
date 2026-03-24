/**
 * 增强的错误处理工具函数
 */

/**
 * 错误类型枚举
 */
export const ErrorTypes = {
  NETWORK: 'NETWORK_ERROR',           // 网络错误
  SERVER: 'SERVER_ERROR',             // 服务器错误
  AUTH: 'AUTH_ERROR',                 // 认证错误
  PERMISSION: 'PERMISSION_ERROR',     // 权限错误
  VALIDATION: 'VALIDATION_ERROR',     // 参数验证错误
  NOT_FOUND: 'NOT_FOUND_ERROR',       // 资源不存在
  TIMEOUT: 'TIMEOUT_ERROR',           // 超时错误
  RATE_LIMIT: 'RATE_LIMIT_ERROR',     // 限流错误
  UNKNOWN: 'UNKNOWN_ERROR'            // 未知错误
}

/**
 * 从错误对象中提取错误类型
 * @param {Error} error - 错误对象
 * @returns {string} 错误类型
 */
export function getErrorType(error) {
  // 网络错误
  if (!error.response && !error.request) {
    return ErrorTypes.NETWORK
  }

  // 请求已发出但未收到响应
  if (error.request && !error.response) {
    return ErrorTypes.NETWORK
  }

  // 有响应但状态码错误
  if (error.response) {
    const status = error.response.status

    switch (status) {
      case 401:
        return ErrorTypes.AUTH
      case 403:
        return ErrorTypes.PERMISSION
      case 404:
        return ErrorTypes.NOT_FOUND
      case 429:
        return ErrorTypes.RATE_LIMIT
      case 500:
      case 502:
      case 503:
        return ErrorTypes.SERVER
      default:
        if (status >= 400 && status < 500) {
          return ErrorTypes.VALIDATION
        }
        return ErrorTypes.UNKNOWN
    }
  }

  // 超时错误
  if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
    return ErrorTypes.TIMEOUT
  }

  return ErrorTypes.UNKNOWN
}

/**
 * 从错误对象中提取友好的错误消息
 * @param {Error} error - 错误对象
 * @returns {string} 友好的错误消息
 */
export function getErrorMessage(error) {
  const errorType = getErrorType(error)

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

  // 根据错误类型返回友好消息
  const errorMessages = {
    [ErrorTypes.NETWORK]: '网络连接失败，请检查网络设置',
    [ErrorTypes.SERVER]: '服务器错误，请稍后重试',
    [ErrorTypes.AUTH]: '登录已过期，请重新登录',
    [ErrorTypes.PERMISSION]: '没有权限执行此操作',
    [ErrorTypes.VALIDATION]: '请求参数错误，请检查输入',
    [ErrorTypes.NOT_FOUND]: '请求的资源不存在',
    [ErrorTypes.TIMEOUT]: '请求超时，请稍后重试',
    [ErrorTypes.RATE_LIMIT]: '操作过于频繁，请稍后再试',
    [ErrorTypes.UNKNOWN]: '操作失败，请稍后重试'
  }

  // 检查 HTTP 状态码对应的默认消息
  if (error.response?.status) {
    const status = error.response.status
    if (errorMessages[errorType]) {
      return errorMessages[errorType]
    }
  }

  // 使用错误对象的 message 属性
  if (error.message) {
    return error.message
  }

  // 默认错误消息
  return errorMessages[ErrorTypes.UNKNOWN]
}

/**
 * 判断错误是否可重试
 * @param {Error} error - 错误对象
 * @returns {boolean} 是否可重试
 */
export function isRetryableError(error) {
  const errorType = getErrorType(error)

  // 以下类型的错误可以重试
  const retryableTypes = [
    ErrorTypes.NETWORK,      // 网络错误
    ErrorTypes.TIMEOUT,      // 超时
    ErrorTypes.SERVER,       // 服务器错误（5xx）
    ErrorTypes.RATE_LIMIT    // 限流错误
  ]

  return retryableTypes.includes(errorType)
}

/**
 * 获取错误对应的操作建议
 * @param {Error} error - 错误对象
 * @returns {string} 操作建议
 */
export function getErrorAction(error) {
  const errorType = getErrorType(error)

  const actions = {
    [ErrorTypes.NETWORK]: '请检查网络连接后重试',
    [ErrorTypes.SERVER]: '请稍后重试或联系管理员',
    [ErrorTypes.AUTH]: '请重新登录',
    [ErrorTypes.PERMISSION]: '请联系管理员开通权限',
    [ErrorTypes.VALIDATION]: '请检查输入内容后重试',
    [ErrorTypes.NOT_FOUND]: '请确认资源是否存在',
    [ErrorTypes.TIMEOUT]: '请稍后重试或检查网络',
    [ErrorTypes.RATE_LIMIT]: '请等待片刻后再试',
    [ErrorTypes.UNKNOWN]: '请稍后重试或联系管理员'
  }

  return actions[errorType] || actions[ErrorTypes.UNKNOWN]
}

/**
 * 显示错误消息
 * @param {Error} error - 错误对象
 * @param {Object} options - 选项
 * @param {number} options.duration - 显示时长(毫秒)
 * @param {boolean} options.showConsole - 是否在控制台显示详细错误
 * @param {boolean} options.showAction - 是否显示操作建议
 * @returns {string} 错误消息
 */
export function showError(error, options = {}) {
  const {
    duration = 3000,
    showConsole = true,
    showAction = false
  } = options

  const message = getErrorMessage(error)
  const action = getErrorAction(error)

  if (showConsole) {
    console.error('❌ Error Type:', getErrorType(error))
    console.error('❌ Error:', error)
    console.error('❌ Error Message:', message)
    console.error('💡 Suggested Action:', action)
  }

  if (showAction) {
    return `${message}\n${action}`
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
    type: getErrorType(error),
    code: null,
    status: null,
    action: getErrorAction(error),
    retryable: isRetryableError(error),
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

/**
 * 显示错误提示（用于UI组件）
 * @param {Error} error - 错误对象
 * @param {Function} messageFn - 消息显示函数（如 ElMessage.error）
 * @param {Object} options - 选项
 */
export function showErrorNotification(error, messageFn = console.error, options = {}) {
  const errorInfo = handleApiError(error)
  const { message, type, retryable, action } = errorInfo

  // 构建完整的错误消息
  let fullMessage = message

  // 如果可重试，添加提示
  if (retryable) {
    fullMessage += '（可重试）'
  }

  // 根据错误类型选择不同的提示样式
  const notificationType = {
    [ErrorTypes.NETWORK]: 'error',
    [ErrorTypes.SERVER]: 'error',
    [ErrorTypes.AUTH]: 'warning',
    [ErrorTypes.PERMISSION]: 'warning',
    [ErrorTypes.VALIDATION]: 'warning',
    [ErrorTypes.NOT_FOUND]: 'info',
    [ErrorTypes.TIMEOUT]: 'warning',
    [ErrorTypes.RATE_LIMIT]: 'warning',
    [ErrorTypes.UNKNOWN]: 'error'
  }[type] || 'error'

  // 显示消息
  if (messageFn) {
    messageFn({
      message: fullMessage,
      type: notificationType,
      duration: options.duration || 5000,
      showClose: true
    })
  }

  console.error(`❌ [${type}]`, message)
  console.error('💡 建议:', action)
  if (retryable) {
    console.error('🔄 此错误可重试')
  }

  return errorInfo
}

/**
 * 创建重试包装器
 * @param {Function} fn - 需要重试的异步函数
 * @param {Object} options - 重试选项
 * @param {number} options.maxRetries - 最大重试次数（默认3）
 * @param {number} options.retryDelay - 重试延迟（毫秒，默认1000）
 * @returns {Function} 包装后的函数
 */
export function withRetry(fn, options = {}) {
  const {
    maxRetries = 3,
    retryDelay = 1000
  } = options

  return async function(...args) {
    let lastError

    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await fn(...args)
      } catch (error) {
        lastError = error

        // 检查是否可重试
        if (!isRetryableError(error)) {
          throw error
        }

        // 最后一次尝试失败，不再重试
        if (i === maxRetries) {
          throw error
        }

        // 等待后重试
        console.warn(`⚠️ 请求失败，${retryDelay}ms后进行第${i + 1}次重试...`)
        await new Promise(resolve => setTimeout(resolve, retryDelay))
      }
    }

    throw lastError
  }
}
