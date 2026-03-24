<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">🐱‍👤 用户管理</h1>
      <div class="header-actions">
        <el-button type="success" @click="handleCreate" class="create-btn">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选区域 -->
    <div class="search-section">
      <div class="search-header">🎵 用户搜索</div>
      <el-form :model="searchForm" inline>
        <el-form-item label="🐱 用户名">
          <el-input
            v-model="searchForm.username"
            placeholder="请输入用户名"
            clearable
            style="width: 200px"
            prefix-icon="User"
          />
        </el-form-item>
        <el-form-item label="📧 邮箱">
          <el-input
            v-model="searchForm.email"
            placeholder="请输入邮箱"
            clearable
            style="width: 200px"
            prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item label="🎭 昵称">
          <el-input
            v-model="searchForm.nickname"
            placeholder="请输入昵称"
            clearable
            style="width: 200px"
            prefix-icon="UserFilled"
          />
        </el-form-item>
        <el-form-item label="📱 手机号">
          <el-input
            v-model="searchForm.phone"
            placeholder="请输入手机号"
            clearable
            style="width: 200px"
            prefix-icon="Phone"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch" class="search-btn">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset" class="reset-btn">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 用户列表表格 -->
    <div class="table-container">
      <div class="table-header">
        <span>🎸 用户列表</span>
        <div class="table-actions">
          <el-tooltip content="刷新数据 (F5)" placement="top">
            <el-button circle @click="fetchUsers" :loading="loading" class="refresh-btn">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
      <el-table
        v-loading="loading"
        :data="userList"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
        class="user-table"
        :empty-text="getEmptyText()"
        :row-class-name="getRowClassName"
      >
      <el-table-column prop="id" label="#" width="80" sortable="custom" align="center">
        <template #default="{ row }">
          <span class="user-id">#{{ row.id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="🐱 用户名" min-width="140" sortable="custom">
        <template #default="{ row }">
          <div class="username-cell">
            <span class="username-text">{{ row.username }}</span>
            <el-tag v-if="row.is_admin" size="small" type="warning" class="admin-badge">管理员</el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="📧 邮箱" min-width="200" sortable="custom" />
      <el-table-column prop="nickname" label="🎭 昵称" min-width="120" />
      <el-table-column prop="phone" label="📱 手机号" min-width="140" />

      <el-table-column prop="status" label="🎵 状态" width="110">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)" class="status-tag">
            <span class="status-icon">{{ getStatusIcon(row.status) }}</span>
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="is_verified" label="✅ 验证" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_verified ? 'success' : 'info'" class="verification-tag">
            {{ row.is_verified ? '✅' : '❌' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="created_at" label="🕐 创建时间" width="170" sortable="custom">
        <template #default="{ row }">
          <div class="time-cell">
            <span class="time-icon">🕐</span>
            {{ formatDateTime(row.created_at) }}
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="last_login_at" label="🎸 最后登录" width="170">
        <template #default="{ row }">
          <div class="time-cell">
            <span class="time-icon">{{ row.last_login_at ? '🎸' : '😴' }}</span>
            {{ row.last_login_at ? formatDateTime(row.last_login_at) : '从未登录' }}
          </div>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <!-- 已删除用户显示恢复按钮 -->
          <template v-if="row.is_deleted">
            <el-button
              type="success"
              size="small"
              @click="handleRestore(row)"
              class="restore-btn"
            >
              <el-icon><RefreshLeft /></el-icon>
              恢复
            </el-button>
            <span class="deleted-tag">已删除</span>
          </template>

          <!-- 正常用户显示编辑和删除按钮 -->
          <template v-else>
            <el-button type="primary" size="small" @click="handleEdit(row)" class="edit-btn">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)" class="delete-btn">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 用户表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
      class="user-dialog"
      center
      :modal="true"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      align-center
      destroy-on-close
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="userForm.phone" placeholder="请输入手机号" />
        </el-form-item>

        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="userForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '../api/user'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'UserList',
  setup() {
    const router = useRouter()

    // 响应式数据
    const loading = ref(false)
    const submitting = ref(false)
    const userList = ref([])
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const userFormRef = ref(null)

    // 搜索表单
    const searchForm = reactive({
      username: '',
      email: '',
      nickname: '',
      phone: ''
    })

    // 分页信息
    const pagination = reactive({
      page: 1,
      per_page: 10,
      total: 0,
      pages: 0
    })

    // 排序信息
    const sortInfo = reactive({
      sort_by: '',
      order_by: ''
    })

    // 用户表单
    const userForm = reactive({
      id: null,
      username: '',
      email: '',
      password: '',
      phone: '',
      nickname: ''
    })

    // 表单验证规则
    const userFormRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' }
      ]
    }

    // 计算属性
    const dialogTitle = computed(() => {
      return isEdit.value ? '编辑用户' : '新增用户'
    })

    // 获取用户列表
    const fetchUsers = async () => {
      loading.value = true
      try {
        // 构建参数对象，过滤掉空字符串的排序参数
        const params = {
          ...searchForm,
          page: pagination.page,
          per_page: pagination.per_page
        }

        // 只有当排序参数不为空时才添加
        if (sortInfo.sort_by) {
          params.sort_by = sortInfo.sort_by
        }
        if (sortInfo.order_by) {
          params.order_by = sortInfo.order_by
        }

        const response = await userApi.getUsers(params)

        if (response.code === 200) {
          userList.value = response.data.users || []
          pagination.total = response.data.pagination?.total || 0
          pagination.pages = response.data.pagination?.pages || 0

          // 如果没有数据且不在第一页，跳转到第一页
          if (userList.value.length === 0 && pagination.page > 1) {
            pagination.page = 1
            fetchUsers()
          }
        } else {
          ElMessage({
            message: `❌ ${response.message || '获取用户列表失败'}`,
            type: 'error',
            duration: 5000,
            showClose: true
          })
        }
      } catch (error) {
        console.error('获取用户列表失败:', error)
        let errorMessage = '获取用户列表失败'

        if (error.response) {
          const status = error.response.status
          if (status === 401) {
            errorMessage = '未授权访问，请重新登录'
            // 调用 authStore 的 logout 方法，会调用后端登出API
            const authStore = useAuthStore()
            await authStore.logout()
            setTimeout(() => {
              router.push('/login')
            }, 2000)
          } else if (status === 403) {
            errorMessage = '权限不足，无法访问用户列表'
          } else if (status === 500) {
            errorMessage = '服务器内部错误，请稍后重试'
          } else if (status === 503) {
            errorMessage = '服务暂时不可用，请稍后重试'
          }
        } else if (error.code === 'ECONNABORTED') {
          errorMessage = '请求超时，请检查网络连接'
        } else if (error.message.includes('Network Error')) {
          errorMessage = '网络连接失败，请检查网络设置'
        } else {
          errorMessage = '未知错误，请联系系统管理员'
        }

        ElMessage({
          message: `❌ ${errorMessage}`,
          type: 'error',
          duration: 5000,
          showClose: true
        })

        // 清空数据，防止显示过期数据
        userList.value = []
        pagination.total = 0
        pagination.pages = 0
      } finally {
        loading.value = false
      }
    }

    // 搜索
    const handleSearch = () => {
      pagination.page = 1
      fetchUsers()
    }

    // 重置搜索
    const handleReset = () => {
      Object.assign(searchForm, {
        username: '',
        email: '',
        nickname: '',
        phone: ''
      })
      handleSearch()
    }

    // 分页大小改变
    const handleSizeChange = (val) => {
      pagination.per_page = val
      pagination.page = 1
      fetchUsers()
    }

    // 当前页改变
    const handleCurrentChange = (val) => {
      pagination.page = val
      fetchUsers()
    }

    // 排序改变
    const handleSortChange = ({ prop, order }) => {
      sortInfo.sort_by = prop
      sortInfo.order_by = order === 'descending' ? 'desc' : 'asc'
      fetchUsers()
    }

    // 新增用户
    const handleCreate = () => {
      isEdit.value = false
      dialogVisible.value = true
      resetForm()
    }

    // 编辑用户
    const handleEdit = (row) => {
      isEdit.value = true
      dialogVisible.value = true
      Object.assign(userForm, {
        id: row.id,
        username: row.username,
        email: row.email,
        password: '',
        phone: row.phone,
        nickname: row.nickname
      })
    }

    // 删除用户
    const handleDelete = async (row) => {
      try {
        await ElMessageBox.confirm(
          `🚨 确定要删除用户 "${row.username}" 吗？\n\n⚠️ 此操作不可恢复，请谨慎操作！`,
          '删除用户确认',
          {
            confirmButtonText: '🗑️ 确认删除',
            cancelButtonText: '❌ 取消操作',
            type: 'error',
            dangerouslyUseHTMLString: false,
            center: true
          }
        )

        // 添加删除前的二次确认
        await ElMessageBox.prompt(
          `请输入用户名 "${row.username}" 以确认删除操作`,
          '🔐 安全验证',
          {
            confirmButtonText: '确认',
            cancelButtonText: '取消',
            inputType: 'text',
            inputValidator: (value) => {
              if (value !== row.username) {
                return '输入的用户名不匹配，请重新输入'
              }
              return true
            }
          }
        )

        const response = await userApi.deleteUser(row.id)
        if (response.code === 200) {
          ElMessage({
            message: `✅ 用户 "${row.username}" 删除成功！`,
            type: 'success',
            duration: 3000,
            showClose: true
          })
          fetchUsers()
        } else {
          ElMessage({
            message: `❌ ${response.message || '删除失败'}`,
            type: 'error',
            duration: 5000,
            showClose: true
          })
        }
      } catch (error) {
        if (error === 'cancel' || error === 'close') {
          ElMessage({
            message: '🚫 删除操作已取消',
            type: 'info',
            duration: 2000
          })
        } else {
          console.error('删除用户失败:', error)
          let errorMessage = '删除失败'
          let errorDetails = []

          // 处理后端返回的详细错误信息
          if (error.backendMessage) {
            errorMessage = error.backendMessage
            errorDetails.push(errorMessage)
          }

          if (error.response) {
            const status = error.response.status
            const data = error.response.data

            // 根据错误码显示具体错误
            if (data && data.error_code) {
              switch (data.error_code) {
                case 'USER_NOT_FOUND':
                  errorMessage = '用户不存在'
                  errorDetails.push('该用户可能已被删除')
                  break

                case 'USER_DELETE_FAILED':
                  errorMessage = '删除用户失败'
                  errorDetails.push('服务器处理删除请求时发生错误')
                  break

                case 'DATABASE_INTEGRITY_ERROR':
                  errorMessage = '数据库约束错误'
                  errorDetails.push('该用户存在关联数据，无法删除')
                  errorDetails.push('请先删除该用户的关联数据（如会话、消息等）')
                  break

                case 'FORBIDDEN':
                  errorMessage = '权限不足'
                  errorDetails.push('您没有权限删除该用户')
                  break

                default:
                  if (data.message) {
                    errorDetails.push(data.message)
                  }
              }
            }

            // 根据 HTTP 状态码显示通用错误
            if (errorDetails.length === 0) {
              switch (status) {
                case 404:
                  errorMessage = '用户不存在'
                  errorDetails.push('该用户可能已被其他用户删除')
                  break

                case 403:
                  errorMessage = '权限不足'
                  errorDetails.push('您没有权限删除该用户')
                  errorDetails.push('• 可能需要管理员权限')
                  errorDetails.push('• 该用户可能是系统管理员')
                  break

                case 409:
                  errorMessage = '数据冲突'
                  errorDetails.push('该用户存在关联数据，无法直接删除')
                  errorDetails.push('建议先将用户状态设置为"已暂停"')
                  break

                case 500:
                  errorMessage = '服务器内部错误'
                  errorDetails.push('服务器处理请求时发生错误，请稍后重试')
                  if (data.message) {
                    errorDetails.push(`错误详情: ${data.message}`)
                  }
                  break

                default:
                  errorDetails.push(data.message || `HTTP ${status} 错误`)
              }
            }
          } else if (error.code === 'ECONNABORTED') {
            errorMessage = '请求超时'
            errorDetails.push('请检查网络连接')
            errorDetails.push('服务器响应时间过长，请稍后重试')
          } else if (error.message && error.message.includes('Network Error')) {
            errorMessage = '网络连接失败'
            errorDetails.push('无法连接到服务器')
            errorDetails.push('请检查后端服务是否正常运行')
          } else if (error.message) {
            errorDetails.push(error.message)
          } else {
            errorDetails.push('未知错误，请联系系统管理员')
          }

          // 显示错误详情
          if (errorDetails.length > 1) {
            ElMessage({
              message: `❌ ${errorMessage}`,
              type: 'error',
              duration: 5000,
              showClose: true
            })

            ElMessageBox.alert(
              `<div style="text-align: left; line-height: 1.8;">
                <strong style="color: #f56c6c; font-size: 16px;">错误详情:</strong><br/><br/>
                ${errorDetails.map(detail => `<div style="margin-bottom: 8px; padding-left: 12px;">• ${detail}</div>`).join('')}
              </div>`,
              '删除失败',
              {
                dangerouslyUseHTMLString: true,
                confirmButtonText: '我知道了',
                customClass: 'error-details-box'
              }
            ).catch(() => {})
          } else {
            ElMessage({
              message: `❌ ${errorMessage}`,
              type: 'error',
              duration: 5000,
              showClose: true
            })
          }
        }
      }
    }

    // 恢复用户
    const handleRestore = async (row) => {
      try {
        await ElMessageBox.confirm(
          `✨ 确定要恢复用户 "${row.username}" 吗？\n\n📌 恢复后，该用户将可以正常登录和使用系统功能。`,
          '恢复用户确认',
          {
            confirmButtonText: '✅ 确认恢复',
            cancelButtonText: '❌ 取消操作',
            type: 'success',
            dangerouslyUseHTMLString: false,
            center: true
          }
        )

        const response = await userApi.restoreUser(row.id)
        if (response.code === 200) {
          ElMessage({
            message: `✅ 用户 "${row.username}" 恢复成功！`,
            type: 'success',
            duration: 3000,
            showClose: true
          })
          fetchUsers()
        } else {
          ElMessage({
            message: `❌ ${response.message || '恢复失败'}`,
            type: 'error',
            duration: 5000,
            showClose: true
          })
        }
      } catch (error) {
        if (error === 'cancel' || error === 'close') {
          ElMessage({
            message: '🚫 恢复操作已取消',
            type: 'info',
            duration: 2000
          })
        } else {
          console.error('恢复用户失败:', error)
          ElMessage({
            message: `❌ 恢复失败: ${error.backendMessage || error.message || '未知错误'}`,
            type: 'error',
            duration: 5000,
            showClose: true
          })
        }
      }
    }

    // 提交表单
    const handleSubmit = async () => {
      if (!userFormRef.value) return

      try {
        await userFormRef.value.validate()
        submitting.value = true

        let response
        if (isEdit.value) {
          // 编辑时也只提交后端接受的字段
          const updateData = {
            username: userForm.username,
            email: userForm.email,
            phone: userForm.phone
          }
          // 如果有密码也提交密码
          if (userForm.password) {
            updateData.password = userForm.password
          }
          // 添加可选字段 nickname
          if (userForm.nickname) {
            updateData.nickname = userForm.nickname
          }
          response = await userApi.updateUser(userForm.id, updateData)
        } else {
          // 创建时只提交后端接受的字段
          const createData = {
            username: userForm.username,
            email: userForm.email,
            password: userForm.password,
            phone: userForm.phone || null  // 处理空字符串
          }
          // 添加可选字段
          if (userForm.nickname) {
            createData.nickname = userForm.nickname
          }
          response = await userApi.createUser(createData)
        }

        if (response.code === 200) {
          ElMessage({
            message: isEdit.value ? '✅ 用户信息更新成功！' : '🎉 用户创建成功！',
            type: 'success',
            duration: 3000,
            showClose: true
          })
          dialogVisible.value = false
          fetchUsers()
        } else {
          ElMessage({
            message: `❌ ${response.message || '操作失败'}`,
            type: 'error',
            duration: 5000,
            showClose: true
          })
        }
      } catch (error) {
        console.error('提交失败:', error)
        let errorMessage = '操作失败'
        let errorDetails = []

        // 处理后端返回的详细错误信息
        if (error.backendMessage) {
          errorMessage = error.backendMessage
          errorDetails.push(errorMessage)
        }

        if (error.response) {
          const status = error.response.status
          const data = error.response.data

          // 根据不同的错误码显示具体的错误信息
          if (data && data.error_code) {
            switch (data.error_code) {
              case 'INVALID_PARAMS':
                errorMessage = '参数验证失败'
                if (data.message) {
                  errorDetails.push(`详细信息: ${data.message}`)
                }
                break

              case 'DUPLICATE_USER':
              case 'DUPLICATE_USERNAME':
                errorMessage = '用户名已被使用'
                errorDetails.push('❌ 用户名已存在，请使用其他用户名')
                // 高亮显示用户名输入框
                setTimeout(() => {
                  if (userFormRef.value) {
                    userFormRef.value.validateField('username')
                  }
                }, 100)
                break

              case 'DUPLICATE_EMAIL':
                errorMessage = '邮箱已被使用'
                errorDetails.push('❌ 邮箱已被注册，请使用其他邮箱')
                // 高亮显示邮箱输入框
                setTimeout(() => {
                  if (userFormRef.value) {
                    userFormRef.value.validateField('email')
                  }
                }, 100)
                break

              case 'DATABASE_INTEGRITY_ERROR':
                errorMessage = '数据库冲突错误'
                errorDetails.push('数据可能已存在或违反约束条件')
                break

              case 'USER_CREATION_FAILED':
                errorMessage = '用户创建失败'
                errorDetails.push('服务器处理请求时发生错误')
                break

              case 'USER_UPDATE_FAILED':
                errorMessage = '用户更新失败'
                errorDetails.push('服务器处理请求时发生错误')
                break

              case 'USER_NOT_FOUND':
                errorMessage = '用户不存在'
                errorDetails.push('该用户可能已被删除')
                break

              case 'EMPTY_REQUEST_BODY':
                errorMessage = '请求数据为空'
                errorDetails.push('请填写所有必填字段')
                break

              default:
                if (data.message) {
                  errorDetails.push(data.message)
                }
            }
          }

          // 根据 HTTP 状态码显示通用错误
          if (errorDetails.length === 0) {
            switch (status) {
              case 400:
                errorMessage = '请求数据格式错误'
                errorDetails.push('请检查输入的字段是否符合要求')
                errorDetails.push('• 用户名: 3-50个字符')
                errorDetails.push('• 邮箱: 必须是有效的邮箱地址')
                errorDetails.push('• 密码: 至少6个字符')
                break

              case 409:
                errorMessage = '数据冲突'
                errorDetails.push('用户名或邮箱已被使用')
                break

              case 500:
                errorMessage = '服务器内部错误'
                errorDetails.push('服务器处理请求时发生错误，请稍后重试')
                if (data.message) {
                  errorDetails.push(`错误详情: ${data.message}`)
                }
                break

              default:
                errorDetails.push(data.message || `HTTP ${status} 错误`)
            }
          }
        } else if (error.code === 'ECONNABORTED') {
          errorMessage = '请求超时'
          errorDetails.push('请检查网络连接')
          errorDetails.push('服务器响应时间过长，请稍后重试')
        } else if (error.message && error.message.includes('Network Error')) {
          errorMessage = '网络连接失败'
          errorDetails.push('无法连接到服务器')
          errorDetails.push('请检查:')
          errorDetails.push('• 后端服务是否正常运行')
          errorDetails.push('• 网络连接是否正常')
          errorDetails.push('• API 地址配置是否正确')
        } else if (error.message) {
          errorDetails.push(error.message)
        } else {
          errorDetails.push('未知错误，请联系系统管理员')
        }

        // 显示错误消息，如果有详细信息则使用通知框
        if (errorDetails.length > 1) {
          ElMessage({
            message: `❌ ${errorMessage}`,
            type: 'error',
            duration: 5000,
            showClose: true
          })

          // 使用 ElMessageBox 显示详细错误
          ElMessageBox.alert(
            `<div style="text-align: left; line-height: 1.8;">
              <strong style="color: #f56c6c; font-size: 16px;">错误详情:</strong><br/><br/>
              ${errorDetails.map(detail => `<div style="margin-bottom: 8px; padding-left: 12px;">• ${detail}</div>`).join('')}
            </div>`,
            '操作失败',
            {
              dangerouslyUseHTMLString: true,
              confirmButtonText: '我知道了',
              customClass: 'error-details-box'
            }
          ).catch(() => {})
        } else {
          ElMessage({
            message: `❌ ${errorMessage}`,
            type: 'error',
            duration: 5000,
            showClose: true
          })
        }
      } finally {
        submitting.value = false
      }
    }

    // 对话框关闭
    const handleDialogClose = () => {
      resetForm()
      if (userFormRef.value) {
        userFormRef.value.resetFields()
      }
    }

    // 重置表单
    const resetForm = () => {
      Object.assign(userForm, {
        id: null,
        username: '',
        email: '',
        password: '',
        phone: '',
        nickname: ''
      })
    }

    // 获取状态类型
    const getStatusType = (status) => {
      const statusMap = {
        active: 'success',
        inactive: 'info',
        suspended: 'warning',
        deleted: 'danger'
      }
      return statusMap[status] || 'info'
    }

    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        active: '活跃',
        inactive: '非活跃',
        suspended: '已暂停',
        deleted: '已删除'
      }
      return statusMap[status] || status
    }

    // 获取状态图标
    const getStatusIcon = (status) => {
      const statusIconMap = {
        active: '🎵',
        inactive: '😴',
        suspended: '⏸️',
        deleted: '🚫'
      }
      return statusIconMap[status] || '❓'
    }

    // 格式化日期时间
    const formatDateTime = (dateTime) => {
      if (!dateTime) return ''
      return new Date(dateTime).toLocaleString('zh-CN')
    }

    // 获取空状态文本
    const getEmptyText = () => {
      const hasSearch = searchForm.username || searchForm.email || searchForm.nickname || searchForm.phone
      if (hasSearch) {
        return '🔍 没有找到匹配的用户，请尝试其他搜索条件'
      }
      return '🐱‍👤 暂无用户数据，点击上方"新增用户"按钮创建第一个用户'
    }

    // 获取表格行类名（用于已删除用户的样式）
    const getRowClassName = ({ row }) => {
      return row.is_deleted ? 'is_deleted' : ''
    }

    // 处理键盘快捷键
    const handleKeydown = (event) => {
      // Ctrl/Cmd + N: 新增用户
      if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
        event.preventDefault()
        handleCreate()
      }
      // F5: 刷新数据
      else if (event.key === 'F5') {
        event.preventDefault()
        fetchUsers()
      }
      // Ctrl/Cmd + F: 聚焦搜索框
      else if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
        event.preventDefault()
        // 聚焦到用户名搜索框
        const usernameInput = document.querySelector('input[placeholder="请输入用户名"]')
        if (usernameInput) {
          usernameInput.focus()
        }
      }
    }

    // 组件挂载时获取数据和绑定事件
    onMounted(() => {
      fetchUsers()
      // 绑定键盘事件
      document.addEventListener('keydown', handleKeydown)
    })

    // 组件卸载时清理事件
    const cleanup = () => {
      document.removeEventListener('keydown', handleKeydown)
    }

    // 导出清理函数
    window.addEventListener('beforeunload', cleanup)

    return {
      // 响应式数据
      loading,
      submitting,
      userList,
      dialogVisible,
      isEdit,
      userFormRef,
      searchForm,
      pagination,
      userForm,
      userFormRules,
      dialogTitle,

      // 方法
      fetchUsers,
      handleSearch,
      handleReset,
      handleSizeChange,
      handleCurrentChange,
      handleSortChange,
      handleCreate,
      handleEdit,
      handleDelete,
      handleRestore,
      handleSubmit,
      handleDialogClose,
      getStatusType,
      getStatusText,
      getStatusIcon,
      formatDateTime,
      getEmptyText,
      getRowClassName
    }
  }
}
</script>

<style scoped>
/* 页面头部样式 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 30px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  letter-spacing: 0.5px;
  text-shadow: none;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.user-menu-btn {
  background: linear-gradient(135deg, #5a67d8 0%, #4c51bf 100%);
  border: none;
  color: white;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-menu-btn:hover {
  background: linear-gradient(135deg, #4c51bf 0%, #44337a 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(90, 103, 216, 0.4);
}

.create-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 25px;
  padding: 12px 28px;
  font-weight: 600;
  color: white;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.create-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  transition: left 0.5s;
}

.create-btn:hover::before {
  left: 100%;
}

.create-btn:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.6);
}

/* 搜索区域样式 */
.search-section {
  margin-bottom: 24px;
  padding: 28px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
}

.search-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.search-section::before {
  content: '🎵';
  position: absolute;
  top: 8px;
  right: 15px;
  font-size: 16px;
  opacity: 0.3;
  animation: float 4s ease-in-out infinite;
}

.search-header {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.2);
  letter-spacing: 0.5px;
}

.search-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 20px;
  padding: 10px 24px;
  color: white;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
  background: linear-gradient(135deg, #764ba2 0%, #f093fb 100%);
}

.reset-btn {
  background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
  border: none;
  border-radius: 20px;
  padding: 10px 24px;
  color: white;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(160, 174, 192, 0.3);
}

.reset-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(160, 174, 192, 0.5);
}

/* 表格容器样式 */
.table-container {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 10px 40px rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}

.table-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.table-container::before {
  content: '🎸';
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 20px;
  opacity: 0.15;
  filter: grayscale(30%);
}

.table-container::after {
  content: '🐱‍👤';
  position: absolute;
  top: 10px;
  right: 45px;
  font-size: 16px;
  opacity: 0.1;
  filter: grayscale(50%);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.table-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.refresh-btn {
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
  border: none;
  color: white;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(56, 161, 105, 0.4);
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
}

/* 快捷键提示 */
.search-section::after {
  content: '提示: Ctrl+F 搜索 | Ctrl+N 新增 | F5 刷新';
  position: absolute;
  bottom: 8px;
  right: 15px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.user-table {
  border-radius: 12px;
  overflow: hidden;
}

.user-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
}

.user-table :deep(.el-table__header th) {
  background: transparent;
  border-bottom: 2px solid #4299e1;
  font-weight: 600;
  color: #2d3748;
}

.user-table :deep(.el-table__row:hover) {
  background-color: #f7fafc;
}

.edit-btn {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  border: none;
  border-radius: 15px;
  transition: all 0.3s ease;
}

.edit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
}

.delete-btn {
  background: linear-gradient(135deg, #fc8181 0%, #f56565 100%);
  border: none;
  border-radius: 15px;
  transition: all 0.3s ease;
}

.delete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(245, 101, 101, 0.4);
}

/* 分页样式 */
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.pagination :deep(.el-pagination) {
  --el-pagination-button-bg-color: #f7fafc;
  --el-pagination-hover-color: #4299e1;
}

.pagination :deep(.el-pagination .el-pager li.is-active) {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  color: white;
}

/* 对话框样式 */
.user-dialog :deep(.el-dialog) {
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  margin: auto;
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  max-height: 90vh;
  overflow-y: auto;
}

.user-dialog :deep(.el-overlay) {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #2c5282 0%, #3182ce 100%);
  color: white;
  padding: 24px;
  border-bottom: none;
}

.user-dialog :deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.user-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 20px;
}

.user-dialog :deep(.el-dialog__body) {
  padding: 32px 24px;
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 50%, #90cdf4 100%);
  position: relative;
  overflow: hidden;
}

.user-dialog :deep(.el-dialog__body)::before {
  content: '🐱‍👤';
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 16px;
  opacity: 0.1;
  filter: grayscale(60%);
}

.user-dialog :deep(.el-form-item__label) {
  font-weight: 600;
  color: #2d3748;
}

.user-dialog :deep(.el-input__wrapper) {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(49, 130, 206, 0.1);
  border: 1px solid rgba(66, 153, 225, 0.3);
}

.user-dialog :deep(.el-select .el-input .el-input__wrapper) {
  border-radius: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 24px 24px;
}

.dialog-footer .el-button {
  border-radius: 20px;
  padding: 12px 24px;
  font-weight: 600;
  border: none;
}

.dialog-footer .el-button--primary {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  box-shadow: 0 4px 15px rgba(66, 153, 225, 0.4);
}

.dialog-footer .el-button--default {
  background: linear-gradient(135deg, #718096 0%, #4a5568 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(113, 128, 150, 0.4);
}

/* 状态标签样式 */
:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 600;
  border: none;
}

:deep(.el-tag--success) {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
}

:deep(.el-tag--info) {
  background: linear-gradient(135deg, #90cdf4 0%, #63b3ed 100%);
  color: white;
}

:deep(.el-tag--warning) {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  color: white;
}

:deep(.el-tag--danger) {
  background: linear-gradient(135deg, #fc8181 0%, #f56565 100%);
  color: white;
}

/* 动画效果 */
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-8px);
    opacity: 0.5;
  }
}

/* 高冷猫咪风格的全局调整 */
* {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 优雅的阴影效果 */
.page-container:hover,
.table-container:hover,
.search-section:hover {
  box-shadow: 0 12px 40px rgba(49, 130, 206, 0.25);
}

/* 表格单元格优化 */
.user-id {
  font-family: 'Monaco', 'Menlo', monospace;
  font-weight: 600;
  color: #4a5568;
  background: linear-gradient(135deg, #edf2f7, #e2e8f0);
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 12px;
}

.username-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username-text {
  font-weight: 600;
  color: #2d3748;
}

.admin-badge {
  font-size: 10px;
  font-weight: 600;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-icon {
  font-size: 12px;
}

.verification-tag {
  font-size: 16px;
  padding: 4px 8px;
  min-width: 32px;
  text-align: center;
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.time-icon {
  font-size: 14px;
  opacity: 0.8;
}

/* 表格行悬停效果 */
.user-table :deep(.el-table__row) {
  transition: all 0.2s ease;
}

.user-table :deep(.el-table__row:hover) {
  background-color: #f7fafc;
  transform: translateX(2px);
}

/* 表格加载状态优化 */
.user-table :deep(.el-loading-mask) {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(2px);
}

.user-table :deep(.el-loading-spinner) {
  margin-top: -40px;
}

.user-table :deep(.el-loading-spinner .path) {
  stroke: #4299e1;
}

/* 空状态优化 */
.user-table :deep(.el-table__empty-block) {
  min-height: 300px;
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-radius: 8px;
  margin: 16px;
}

.user-table :deep(.el-table__empty-text) {
  color: #4a5568;
  font-size: 16px;
  font-weight: 500;
  line-height: 1.6;
}

/* 搜索区域优化 */
.search-section :deep(.el-form-item__label) {
  font-weight: 600;
  color: #2d3748;
}

.search-section :deep(.el-input__wrapper) {
  border-radius: 12px;
  border: 1px solid rgba(66, 153, 225, 0.3);
  box-shadow: 0 2px 8px rgba(49, 130, 206, 0.1);
  transition: all 0.3s ease;
}

.search-section :deep(.el-input__wrapper:hover) {
  border-color: #4299e1;
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.2);
}

.search-section :deep(.el-input__wrapper.is-focus) {
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

/* 分页组件优化 */
.pagination :deep(.el-pager li) {
  border-radius: 8px;
  margin: 0 2px;
  font-weight: 500;
}

.pagination :deep(.el-pagination__sizes) {
  margin-right: 16px;
}

.pagination :deep(.el-pagination__total) {
  font-weight: 600;
  color: #4a5568;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .search-section :deep(.el-form--inline) .el-form-item {
    display: block;
    margin-bottom: 16px;
  }

  .search-section :deep(.el-input) {
    width: 100% !important;
  }

  .search-section :deep(.el-form-item__label) {
    display: block;
    margin-bottom: 8px;
  }

  .search-header {
    margin-bottom: 20px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .create-btn {
    width: 100%;
    justify-content: center;
  }
}

/* 平板设备优化 */
@media (min-width: 769px) and (max-width: 1024px) {
  .search-section :deep(.el-input) {
    width: 180px !important;
  }
}

/* 无障碍访问优化 */
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
    animation: none !important;
  }
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .page-container {
    border: 2px solid #2d3748;
  }

  .search-btn,
  .reset-btn,
  .create-btn,
  .edit-btn,
  .delete-btn {
    border: 2px solid currentColor;
  }
}

/* 错误详情弹窗样式 */
:deep(.error-details-box) {
  border-radius: 12px;
}

:deep(.error-details-box .el-message-box__content) {
  padding: 20px;
}

:deep(.error-details-box .el-message-box__message) {
  font-size: 14px;
  color: #606266;
}

:deep(.error-details-box .el-message-box__header) {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  border-radius: 12px 12px 0 0;
  padding: 20px;
}

:deep(.error-details-box .el-message-box__title) {
  color: #dc2626;
  font-weight: 600;
}

:deep(.error-details-box .el-message-box__btns) {
  padding: 15px 20px 20px;
}

:deep(.error-details-box .el-button--primary) {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
  border-radius: 8px;
  padding: 10px 24px;
  font-weight: 600;
}

:deep(.error-details-box .el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}
/* 恢复按钮样式 */
.restore-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
}

.restore-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

/* 已删除标签样式 */
.deleted-tag {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 8px;
}

/* 已删除行的样式 */
:deep(.el-table__row.is_deleted) {
  background: rgba(239, 68, 68, 0.03);
  opacity: 0.7;
}

:deep(.el-table__row.is_deleted:hover) {
  background: rgba(239, 68, 68, 0.06) !important;
}
</style>