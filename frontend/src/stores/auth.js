import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api/user'

export const useAuthStore = defineStore('auth', () => {
  // State
  const access_token = ref(localStorage.getItem('access_token') || '')
  const refresh_token = ref(localStorage.getItem('refresh_token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const isLoggedIn = ref(!!localStorage.getItem('access_token'))
  const isAdmin = ref(localStorage.getItem('is_admin') === 'true')
  const userId = ref(localStorage.getItem('user_id') || '')

  // Getters
  const isAuthenticated = computed(() => {
    return !!access_token.value && isLoggedIn.value
  })

  const currentUser = computed(() => {
    return {
      id: userId.value,
      username: username.value,
      isLoggedIn: isAuthenticated.value,
      isAdmin: isAdmin.value
    }
  })

  // Actions
  const setTokens = (tokens) => {
    access_token.value = tokens.access_token
    refresh_token.value = tokens.refresh_token
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  }

  const setUser = (userData) => {
    username.value = userData.username
    userId.value = userData.id || ''
    isAdmin.value = userData.is_admin || false
    localStorage.setItem('username', userData.username)
    if (userData.id) {
      localStorage.setItem('user_id', userData.id)
    }
    localStorage.setItem('is_admin', userData.is_admin ? 'true' : 'false')
  }

  const login = async (credentials) => {
    try {
      const response = await authApi.login(credentials)

      // 检查响应是否成功且包含tokens (支持多种响应格式)
      const isSuccess = response.status === 'success' || response.code === 200
      const data = response.data || response

      if (isSuccess && data && data.access_token && data.refresh_token) {
        setTokens(data)
        setUser({ username: credentials.username })
        isLoggedIn.value = true
        localStorage.setItem('isLoggedIn', 'true')

        // 登录成功后获取完整的用户信息
        await fetchCurrentUser()

        return { success: true, data: data }
      } else {
        throw new Error(response.message || 'Login failed')
      }
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (userData) => {
    try {
      const response = await authApi.register(userData)
      return { success: true, data: response.data || response }
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      // 调用后端登出接口
      await authApi.logout()
    } catch (error) {
      console.error('Backend logout failed:', error)
      // 即使后端登出失败，也要清除本地状态
    } finally {
      // 清除本地状态
      clearAuth()
    }
  }

  const clearAuth = () => {
    access_token.value = ''
    refresh_token.value = ''
    username.value = ''
    userId.value = ''
    isAdmin.value = false
    isLoggedIn.value = false

    // 清除localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    localStorage.removeItem('isLoggedIn')
    localStorage.removeItem('is_admin')
    localStorage.removeItem('user_id')
  }

  const refreshAccessToken = async () => {
    try {
      const response = await authApi.refreshTokens()
      if (response.access_token) {
        access_token.value = response.access_token
        localStorage.setItem('access_token', response.access_token)

        if (response.refresh_token) {
          refresh_token.value = response.refresh_token
          localStorage.setItem('refresh_token', response.refresh_token)
        }

        return true
      }
      return false
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuth()
      return false
    }
  }

  const initializeAuth = () => {
    const token = localStorage.getItem('access_token')
    const loggedIn = localStorage.getItem('isLoggedIn')
    const user = localStorage.getItem('username')

    if (token && loggedIn === 'true') {
      access_token.value = token
      refresh_token.value = localStorage.getItem('refresh_token') || ''
      username.value = user || ''
      userId.value = localStorage.getItem('user_id') || ''
      isAdmin.value = localStorage.getItem('is_admin') === 'true'
      isLoggedIn.value = true
    } else {
      clearAuth()
    }
  }

  // 获取当前用户信息
  const fetchCurrentUser = async () => {
    try {
      const response = await authApi.getCurrentUser()
      if (response.code === 200 || response.status === 'success') {
        const userData = response.data
        setUser({
          id: userData.id,
          username: userData.username,
          is_admin: userData.is_admin
        })
        return userData
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取失败，可能token已过期，清除认证状态
      if (error.response && error.response.status === 401) {
        clearAuth()
        throw error // 重新抛出错误，让调用方知道token验证失败
      }
      throw error // 其他错误也抛出
    }
  }

  return {
    // State
    access_token,
    refresh_token,
    username,
    isLoggedIn,
    isAdmin,
    userId,

    // Getters
    isAuthenticated,
    currentUser,

    // Actions
    login,
    register,
    logout,
    clearAuth,
    refreshAccessToken,
    initializeAuth,
    setTokens,
    setUser,
    fetchCurrentUser
  }
})