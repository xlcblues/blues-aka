import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi } from '../api/user'

export const useUserStore = defineStore('user', () => {
  // State
  const users = ref([])
  const currentUser = ref(null)
  const loading = ref(false)
  const totalUsers = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(10)

  // Actions
  const fetchUsers = async (params = {}) => {
    try {
      loading.value = true

      const queryParams = {
        page: params.page || currentPage.value,
        per_page: params.per_page || pageSize.value,
        username: params.username || '',
        email: params.email || '',
        sort_by: params.sort_by || 'id',
        sort_order: params.sort_order || 'desc',
        ...params
      }

      const response = await userApi.getUsers(queryParams)

      if (response.data) {
        users.value = response.data.items || response.data || []
        totalUsers.value = response.data.total || response.data.length
        currentPage.value = queryParams.page
      } else {
        users.value = []
        totalUsers.value = 0
      }

      return { success: true, data: response }
    } catch (error) {
      console.error('Failed to fetch users:', error)
      users.value = []
      totalUsers.value = 0
      throw error
    } finally {
      loading.value = false
    }
  }

  const createUser = async (userData) => {
    try {
      loading.value = true
      const response = await userApi.createUser(userData)

      // 创建成功后刷新用户列表
      await fetchUsers()

      return { success: true, data: response }
    } catch (error) {
      console.error('Failed to create user:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const updateUser = async (userId, userData) => {
    try {
      loading.value = true
      const response = await userApi.updateUser(userId, userData)

      // 更新成功后刷新用户列表
      await fetchUsers()

      return { success: true, data: response }
    } catch (error) {
      console.error('Failed to update user:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const deleteUser = async (userId) => {
    try {
      loading.value = true
      const response = await userApi.deleteUser(userId)

      // 删除成功后刷新用户列表
      await fetchUsers()

      return { success: true, data: response }
    } catch (error) {
      console.error('Failed to delete user:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const searchUsers = async (searchParams) => {
    try {
      const params = {
        ...searchParams,
        page: 1 // 搜索时重置到第一页
      }
      return await fetchUsers(params)
    } catch (error) {
      console.error('Failed to search users:', error)
      throw error
    }
  }

  const resetUsers = () => {
    users.value = []
    currentUser.value = null
    loading.value = false
    totalUsers.value = 0
    currentPage.value = 1
  }

  const setPagination = (page, size) => {
    currentPage.value = page
    pageSize.value = size
  }

  // Getters
  const userCount = computed(() => users.value.length)
  const isLoading = computed(() => loading.value)
  const totalPages = computed(() => Math.ceil(totalUsers.value / pageSize.value))

  return {
    // State
    users,
    currentUser,
    loading,
    totalUsers,
    currentPage,
    pageSize,

    // Getters
    userCount,
    isLoading,
    totalPages,

    // Actions
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    searchUsers,
    resetUsers,
    setPagination
  }
})