/**
 * 密码强度检测工具
 * 根据后端的密码强度规则进行验证
 */

/**
 * 检查密码强度
 * @param {string} password - 要检查的密码
 * @returns {Object} 返回强度信息对象
 *
 * 密码强度规则（与后端一致）：
 * - 最少 8 个字符
 * - 必须包含以下至少 2 种字符类型：
 *   - 字母（a-z, A-Z）
 *   - 数字（0-9）
 *   - 特殊字符
 */
export function checkPasswordStrength(password) {
  // 空密码
  if (!password) {
    return {
      score: 0,
      level: 'empty',
      text: '请输入密码',
      color: '#909399',
      valid: false,
      checks: {
        length: false,
        hasLetter: false,
        hasDigit: false,
        hasSpecial: false
      }
    }
  }

  // 执行各项检查
  const checks = {
    length: password.length >= 8,
    hasLetter: /[a-zA-Z]/.test(password),
    hasDigit: /[0-9]/.test(password),
    hasSpecial: /[^a-zA-Z0-9]/.test(password)
  }

  // 计算通过的检查项数量
  const passedChecks = Object.values(checks).filter(Boolean).length

  // 判断是否满足最低要求（至少2种字符类型 + 长度要求）
  const isValid = checks.length && passedChecks >= 2

  // 根据通过的检查项数量确定强度等级
  let score, level, text, color

  if (!checks.length) {
    score = 1
    level = 'weak'
    text = '密码强度：弱'
    color = '#F56C6C' // 红色
  } else if (passedChecks === 2 && checks.length && checks.hasLetter && checks.hasDigit) {
    score = 2
    level = 'medium'
    text = '密码强度：中'
    color = '#E6A23C' // 橙色
  } else if (passedChecks === 3) {
    score = 3
    level = 'strong'
    text = '密码强度：强'
    color = '#67C23A' // 绿色
  } else if (passedChecks === 4) {
    score = 4
    level = 'very-strong'
    text = '密码强度：很强'
    color = '#409EFF' // 蓝色
  } else {
    score = 1
    level = 'weak'
    text = '密码强度：弱'
    color = '#F56C6C'
  }

  return {
    score,
    level,
    text,
    color,
    valid: isValid,
    checks
  }
}

/**
 * 获取密码强度提示信息
 * @param {Object} strength - checkPasswordStrength 返回的对象
 * @returns {Array} 返回提示信息数组
 */
export function getPasswordHints(strength) {
  const hints = []

  if (!strength.checks.length) {
    hints.push('密码长度至少为 8 个字符')
  }

  if (!strength.checks.hasLetter) {
    hints.push('密码应包含字母')
  }

  if (!strength.checks.hasDigit) {
    hints.push('密码应包含数字')
  }

  if (!strength.checks.hasSpecial) {
    hints.push('建议包含特殊字符（如 !@#$%^&*）')
  }

  if (strength.valid) {
    hints.unshift('✓ 密码强度满足要求')
  }

  return hints
}

/**
 * 验证密码是否符合要求
 * @param {string} password - 要验证的密码
 * @returns {boolean} 是否符合要求
 */
export function isPasswordValid(password) {
  const strength = checkPasswordStrength(password)
  return strength.valid
}

/**
 * 密码验证规则（用于表单验证）
 * @param {Object} rule - 表单规则对象
 * @param {string} value - 密码值
 * @param {Function} callback - 回调函数
 */
export function validatePassword(rule, value, callback) {
  if (!value) {
    callback(new Error('请输入密码'))
    return
  }

  const strength = checkPasswordStrength(value)

  if (!strength.valid) {
    const hints = getPasswordHints(strength)
    callback(new Error(hints[0]))
  } else {
    callback()
  }
}

/**
 * 确认密码验证规则
 * @param {string} password - 原密码
 * @returns {Function} 验证函数
 */
export function validateConfirmPassword(password) {
  return function (rule, value, callback) {
    if (!value) {
      callback(new Error('请再次输入密码'))
      return
    }

    if (value !== password) {
      callback(new Error('两次输入的密码不一致'))
    } else {
      callback()
    }
  }
}

export default {
  checkPasswordStrength,
  getPasswordHints,
  isPasswordValid,
  validatePassword,
  validateConfirmPassword
}
