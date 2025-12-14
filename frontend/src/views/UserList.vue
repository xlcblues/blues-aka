<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">🐱‍👤 用户管理</h1>
      <el-button type="primary" @click="handleCreate" class="create-btn">
        <el-icon><Plus /></el-icon>
        新增用户
      </el-button>
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
      <div class="table-header">🎸 用户列表</div>
      <el-table
        v-loading="loading"
        :data="userList"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
        class="user-table"
        :empty-text="'🐱‍👤 暂无用户数据，点击上方按钮新增用户'"
      >
      <el-table-column prop="id" label="#" width="60" sortable="custom" align="center">
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

      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)" class="edit-btn">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)" class="delete-btn">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
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

        <el-form-item label="状态" prop="status">
          <el-select v-model="userForm.status" placeholder="请选择状态">
            <el-option label="活跃" value="active" />
            <el-option label="非活跃" value="inactive" />
            <el-option label="已暂停" value="suspended" />
          </el-select>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi } from '../api/user'

export default {
  name: 'UserList',
  setup() {
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
      email: ''
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
      nickname: '',
      status: 'inactive'
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
          userList.value = response.data.users
          pagination.total = response.data.pagination.total
          pagination.pages = response.data.pagination.pages
        } else {
          ElMessage.error(response.message || '获取用户列表失败')
        }
      } catch (error) {
        console.error('获取用户列表失败:', error)
        ElMessage.error('获取用户列表失败')
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
        email: ''
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
        nickname: row.nickname,
        status: row.status
      })
    }

    // 删除用户
    const handleDelete = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除用户 "${row.username}" 吗？此操作不可恢复！`,
          '警告',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        const response = await userApi.deleteUser(row.id)
        if (response.code === 200) {
          ElMessage.success('删除成功')
          fetchUsers()
        } else {
          ElMessage.error(response.message || '删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除用户失败:', error)
          ElMessage.error('删除失败')
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
          response = await userApi.updateUser(userForm.id, updateData)
        } else {
          // 创建时只提交后端接受的字段
          const createData = {
            username: userForm.username,
            email: userForm.email,
            password: userForm.password,
            phone: userForm.phone
          }
          response = await userApi.createUser(createData)
        }

        if (response.code === 200) {
          ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
          dialogVisible.value = false
          fetchUsers()
        } else {
          ElMessage.error(response.message || '操作失败')
        }
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error('操作失败')
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
        nickname: '',
        status: 'inactive'
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

    // 组件挂载时获取数据
    onMounted(() => {
      fetchUsers()
    })

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
      handleSubmit,
      handleDialogClose,
      getStatusType,
      getStatusText,
      getStatusIcon,
      formatDateTime
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
  padding-bottom: 16px;
  border-bottom: 2px solid #4299e1;
  position: relative;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
  margin: 0;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
  letter-spacing: 0.5px;
}

.create-btn {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  border-radius: 25px;
  padding: 12px 24px;
  font-weight: 600;
  color: white;
  box-shadow: 0 4px 15px rgba(66, 153, 225, 0.4);
  transition: all 0.3s ease;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(66, 153, 225, 0.6);
}

/* 搜索区域样式 */
.search-section {
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 30%, #90cdf4 60%, #63b3ed 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(66, 153, 225, 0.15);
  border: 1px solid rgba(66, 153, 225, 0.3);
  position: relative;
  overflow: hidden;
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
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.6);
  letter-spacing: 0.3px;
}

.search-btn {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  color: white;
  font-weight: 600;
  transition: all 0.3s ease;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(66, 153, 225, 0.4);
}

.reset-btn {
  background: linear-gradient(135deg, #718096 0%, #4a5568 100%);
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  color: white;
  font-weight: 600;
  transition: all 0.3s ease;
}

.reset-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(113, 128, 150, 0.4);
}

/* 表格容器样式 */
.table-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  margin-bottom: 24px;
  position: relative;
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
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
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
</style>