<template>
  <div class="profile-container">
    <div class="page-header">
      <h1 class="page-title">🐱‍👤 个人信息</h1>
      <el-button @click="goBack" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
    </div>

    <div class="profile-content">
      <!-- 用户信息卡片 -->
      <el-card class="profile-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">🎵 基本信息</span>
            <el-button
              type="primary"
              size="small"
              @click="editMode = !editMode"
              :icon="editMode ? 'Close' : 'Edit'"
            >
              {{ editMode ? '取消编辑' : '编辑资料' }}
            </el-button>
          </div>
        </template>

        <div class="profile-info">
          <!-- 头像区域 -->
          <div class="avatar-section">
            <el-avatar :size="100" :src="userAvatar" class="user-avatar">
              <span class="avatar-text">{{ currentUser?.username?.charAt(0)?.toUpperCase() || 'U' }}</span>
            </el-avatar>
            <div class="avatar-info">
              <h3 class="username">{{ currentUser?.username || '未知用户' }}</h3>
              <p class="user-status">
                <el-tag :type="getStatusType(userStatus)" size="small">
                  {{ getStatusText(userStatus) }}
                </el-tag>
              </p>
            </div>
          </div>

          <!-- 用户信息表单 -->
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="🐱 用户名" prop="username">
              <el-input
                v-model="profileForm.username"
                :disabled="!editMode"
                placeholder="请输入用户名"
              />
            </el-form-item>

            <el-form-item label="📧 邮箱地址" prop="email">
              <el-input
                v-model="profileForm.email"
                :disabled="!editMode"
                placeholder="请输入邮箱地址"
              />
            </el-form-item>

            <el-form-item label="📞 手机号码" prop="phone">
              <el-input
                v-model="profileForm.phone"
                :disabled="!editMode"
                placeholder="请输入手机号码"
              />
            </el-form-item>

            <el-form-item label="🎭 昵称" prop="nickname">
              <el-input
                v-model="profileForm.nickname"
                :disabled="!editMode"
                placeholder="请输入昵称"
              />
            </el-form-item>

            <el-form-item label="📅 注册时间">
              <el-input :value="formatDate(createdAt)" disabled />
            </el-form-item>

            <el-form-item label="⏰ 最后登录">
              <el-input :value="formatDate(lastLoginAt)" disabled />
            </el-form-item>

            <el-form-item v-if="editMode" class="form-actions">
              <el-button type="primary" @click="saveProfile" :loading="saving">
                <el-icon><Check /></el-icon>
                保存修改
              </el-button>
              <el-button @click="cancelEdit">
                <el-icon><Close /></el-icon>
                取消
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>

      <!-- 密码修改卡片 -->
      <el-card class="password-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">🔐 修改密码</span>
          </div>
        </template>

        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="120px"
          class="password-form"
        >
          <el-form-item label="🔒 当前密码" prop="currentPassword">
            <el-input
              v-model="passwordForm.currentPassword"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>

          <el-form-item label="🔑 新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>

          <el-form-item label="🔐 确认密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="请确认新密码"
              show-password
              @keyup.enter="changePassword"
            />
          </el-form-item>

          <el-form-item class="form-actions">
            <el-button type="primary" @click="changePassword" :loading="changingPassword">
              <el-icon><Key /></el-icon>
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'Profile',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    // 响应式数据
    const editMode = ref(false)
    const saving = ref(false)
    const changingPassword = ref(false)
    const profileFormRef = ref(null)
    const passwordFormRef = ref(null)

    // 用户信息
    const currentUser = computed(() => authStore.currentUser)
    const userAvatar = ref('')
    const userStatus = ref('active')
    const createdAt = ref('')
    const lastLoginAt = ref('')

    // 个人资料表单
    const profileForm = reactive({
      username: '',
      email: '',
      phone: '',
      nickname: ''
    })

    // 密码修改表单
    const passwordForm = reactive({
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    // 表单验证规则
    const profileRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱地址', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
      ],
      phone: [
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
      ]
    }

    // 密码确认验证器
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== passwordForm.newPassword) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }

    const passwordRules = {
      currentPassword: [
        { required: true, message: '请输入当前密码', trigger: 'blur' }
      ],
      newPassword: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' },
        { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含至少一个字母和一个数字', trigger: 'blur' }
      ],
      confirmPassword: [
        { validator: validateConfirmPassword, trigger: 'blur' }
      ]
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
        inactive: '未激活',
        suspended: '已暂停',
        deleted: '已删除'
      }
      return statusMap[status] || '未知'
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }

    // 加载用户资料
    const loadUserProfile = async () => {
      try {
        // 模拟用户数据，实际应该从API获取
        const userData = {
          username: authStore.username,
          email: 'user@example.com',
          phone: '13800138000',
          nickname: '音乐爱好者',
          status: 'active',
          created_at: '2024-01-01T00:00:00Z',
          last_login_at: new Date().toISOString()
        }

        Object.assign(profileForm, {
          username: userData.username,
          email: userData.email,
          phone: userData.phone,
          nickname: userData.nickname
        })

        userStatus.value = userData.status
        createdAt.value = userData.created_at
        lastLoginAt.value = userData.last_login_at
      } catch (error) {
        console.error('加载用户资料失败:', error)
        ElMessage.error('加载用户资料失败')
      }
    }

    // 保存个人资料
    const saveProfile = async () => {
      if (!profileFormRef.value) return

      try {
        await profileFormRef.value.validate()
        saving.value = true

        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000))

        ElMessage.success('个人资料保存成功！')
        editMode.value = false
      } catch (error) {
        console.error('保存个人资料失败:', error)
        ElMessage.error('保存失败，请重试')
      } finally {
        saving.value = false
      }
    }

    // 取消编辑
    const cancelEdit = () => {
      editMode.value = false
      loadUserProfile() // 重新加载数据
    }

    // 修改密码
    const changePassword = async () => {
      if (!passwordFormRef.value) return

      try {
        await passwordFormRef.value.validate()
        changingPassword.value = true

        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000))

        ElMessage.success('密码修改成功！请重新登录')

        // 清空表单
        Object.assign(passwordForm, {
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        })

        // 退出登录
        await authStore.logout()
        router.push('/login')
      } catch (error) {
        console.error('修改密码失败:', error)
        ElMessage.error('修改失败，请检查当前密码是否正确')
      } finally {
        changingPassword.value = false
      }
    }

    // 返回上一页
    const goBack = () => {
      router.go(-1)
    }

    // 组件挂载时加载数据
    onMounted(() => {
      loadUserProfile()
    })

    return {
      // 数据
      currentUser,
      userAvatar,
      userStatus,
      createdAt,
      lastLoginAt,
      editMode,
      saving,
      changingPassword,
      profileForm,
      passwordForm,
      profileFormRef,
      passwordFormRef,

      // 方法
      getStatusType,
      getStatusText,
      formatDate,
      saveProfile,
      cancelEdit,
      changePassword,
      goBack
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #4299e1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

.back-btn {
  color: #4299e1;
  border-color: #4299e1;
}

.back-btn:hover {
  background: rgba(66, 153, 225, 0.1);
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-card, .password-card {
  border-radius: 12px;
  border: 1px solid rgba(66, 153, 225, 0.2);
  transition: all 0.3s ease;
}

.profile-card:hover, .password-card:hover {
  box-shadow: 0 8px 30px rgba(66, 153, 225, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
}

.profile-info {
  padding: 20px 0;
}

.avatar-section {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.user-avatar {
  margin-right: 20px;
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: 3px solid #fff;
  box-shadow: 0 4px 20px rgba(66, 153, 225, 0.3);
}

.avatar-text {
  font-size: 36px;
  font-weight: 600;
  color: white;
}

.avatar-info {
  flex: 1;
}

.username {
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 8px 0;
}

.user-status {
  margin: 0;
}

.profile-form, .password-form {
  max-width: 500px;
}

.form-actions {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.form-actions :deep(.el-form-item__content) {
  display: flex;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-container {
    padding: 10px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .avatar-section {
    flex-direction: column;
    text-align: center;
  }

  .user-avatar {
    margin-right: 0;
    margin-bottom: 16px;
  }

  .profile-form, .password-form {
    max-width: 100%;
  }
}

/* 表单样式增强 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  border-color: #4299e1;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #3182ce;
  box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #3182ce 0%, #2c5282 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(66, 153, 225, 0.4);
}
</style>