<template>
  <div class="register-container">
    <div class="register-card">
      <!-- 卡片头部装饰 -->
      <div class="card-header">
        <div class="floating-icons">
          <div class="icon music-note">🎵</div>
          <div class="icon cat">🐱‍👤</div>
          <div class="icon guitar">🎸</div>
        </div>
        <h1 class="register-title">
          <span class="title-icon">🐱‍👤</span>
          加入 Blues AKA
        </h1>
        <p class="register-subtitle">创建您的账户，开始音乐之旅</p>
      </div>

      <!-- 注册表单 -->
      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <div class="input-wrapper">
            <span class="input-icon">🐱</span>
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名"
              size="large"
              clearable
              class="custom-input"
              autocomplete="username"
            />
          </div>
        </el-form-item>

        <el-form-item prop="email">
          <div class="input-wrapper">
            <span class="input-icon">📧</span>
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱地址"
              size="large"
              clearable
              class="custom-input"
              autocomplete="email"
            />
          </div>
        </el-form-item>

        <el-form-item prop="password">
          <div class="input-wrapper">
            <span class="input-icon">🔐</span>
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              clearable
              class="custom-input"
              autocomplete="new-password"
            />
          </div>
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <div class="input-wrapper">
            <span class="input-icon">🔒</span>
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请确认密码"
              size="large"
              show-password
              clearable
              class="custom-input"
              autocomplete="new-password"
              @keyup.enter="handleRegister"
            />
          </div>
        </el-form-item>

        <el-form-item class="button-item">
          <el-button
            type="primary"
            size="large"
            class="register-btn"
            :loading="loading"
            @click="handleRegister"
          >
            <span v-if="!loading" class="btn-content">
              <span class="btn-icon">🎸</span>
              创建账户
            </span>
            <span v-else class="btn-content">
              <span class="loading-icon">⏳</span>
              注册中...
            </span>
          </el-button>
        </el-form-item>

        <!-- 登录链接 -->
        <div class="login-link">
          <span class="login-text">已有账号？</span>
          <router-link to="/login" class="login-btn">
            立即登录 🎵
          </router-link>
        </div>
      </el-form>

      <!-- 卡片底部装饰 -->
      <div class="card-footer">
        <div class="footer-text">
          <span class="music-icon">🎵</span>
          安全可靠的 Blues AKA 系统
          <span class="music-icon">🎵</span>
        </div>
      </div>
    </div>

    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
      <div class="floating-bg-icons">
        <div class="bg-icon bg-music">🎵</div>
        <div class="bg-icon bg-guitar">🎸</div>
        <div class="bg-icon bg-cat">🐱‍👤</div>
        <div class="bg-icon bg-blues">🎺</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

export default {
  name: 'Register',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const registerFormRef = ref(null)
    const loading = ref(false)

    // 注册表单数据
    const registerForm = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })

    // 密码确认验证器
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== registerForm.password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }

    // 邮箱格式验证器
    const validateEmail = (rule, value, callback) => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (value === '') {
        callback(new Error('请输入邮箱地址'))
      } else if (!emailRegex.test(value)) {
        callback(new Error('请输入正确的邮箱格式'))
      } else {
        callback()
      }
    }

    // 表单验证规则
    const registerRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' },
        { pattern: /^[a-zA-Z0-9_\u4e00-\u9fa5]+$/, message: '用户名只能包含字母、数字、下划线和中文', trigger: 'blur' }
      ],
      email: [
        { validator: validateEmail, trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' },
        { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码必须包含至少一个字母和一个数字', trigger: 'blur' }
      ],
      confirmPassword: [
        { validator: validateConfirmPassword, trigger: 'blur' }
      ]
    }

    // 处理注册
    const handleRegister = async () => {
      if (!registerFormRef.value) return

      try {
        await registerFormRef.value.validate()
        loading.value = true

        await authStore.register({
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        })

        ElMessage.success('注册成功！请登录 🎵')
        // 跳转到登录页面
        router.push('/login')
      } catch (error) {
        console.error('注册失败:', error)
        const errorMessage = error.response?.data?.message || error.message || '注册失败，请重试'
        ElMessage.error(errorMessage)
      } finally {
        loading.value = false
      }
    }

    return {
      registerFormRef,
      loading,
      registerForm,
      registerRules,
      handleRegister
    }
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%);
  position: relative;
  overflow: hidden;
  padding: 20px;
}

/* 注册卡片 */
.register-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 10;
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 卡片头部 */
.card-header {
  text-align: center;
  margin-bottom: 32px;
  position: relative;
}

.floating-icons {
  position: absolute;
  top: -20px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.icon {
  font-size: 20px;
  animation: float 3s ease-in-out infinite;
}

.icon.music-note {
  animation-delay: 0s;
}

.icon.cat {
  animation-delay: 1s;
}

.icon.guitar {
  animation-delay: 2s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-10px) rotate(5deg);
  }
}

.register-title {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
  margin: 20px 0 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}

.title-icon {
  font-size: 32px;
  filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.2));
}

.register-subtitle {
  color: #718096;
  font-size: 14px;
  margin: 0;
  font-weight: 500;
}

/* 注册表单 */
.register-form {
  margin-bottom: 24px;
  width: 100%;
}

.register-form :deep(.el-form-item) {
  margin-bottom: 24px;
  width: 100%;
}

.register-form :deep(.el-form-item__content) {
  width: 100%;
}

.button-item :deep(.el-form-item__content) {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 0;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.input-icon {
  position: absolute;
  left: 16px;
  z-index: 10;
  font-size: 18px;
  color: #4299e1;
  pointer-events: none;
}

.custom-input {
  width: 100%;
}

.custom-input :deep(.el-input) {
  width: 100%;
}

.custom-input :deep(.el-input__wrapper) {
  width: 100%;
  height: 48px;
  border-radius: 16px;
  padding-left: 45px;
  padding-right: 16px;
  box-shadow: 0 4px 20px rgba(66, 153, 225, 0.15);
  border: 1px solid rgba(66, 153, 225, 0.3);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
}

.custom-input :deep(.el-input__wrapper:hover) {
  border-color: #4299e1;
  box-shadow: 0 6px 25px rgba(66, 153, 225, 0.25);
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.custom-input :deep(.el-input__inner) {
  font-size: 15px;
  color: #2d3748;
  height: auto;
  line-height: 1.5;
  width: 100%;
  padding: 12px 0;
  border: none;
  background: transparent;
}

.custom-input :deep(.el-input__inner::placeholder) {
  color: #a0aec0;
}

/* 注册按钮 */
.register-btn {
  width: 100%;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  border: none;
  font-size: 16px;
  font-weight: 600;
  color: white;
  box-shadow: 0 8px 25px rgba(72, 187, 120, 0.4);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 35px rgba(72, 187, 120, 0.6);
  background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
}

.register-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
}

.register-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.6s;
}

.register-btn:hover::before {
  left: 100%;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.btn-icon, .loading-icon {
  font-size: 18px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 登录链接 */
.login-link {
  text-align: center;
  margin-top: 20px;
  padding: 16px 0;
  border-top: 1px solid rgba(72, 187, 120, 0.15);
}

.login-text {
  color: #718096;
  font-size: 14px;
  margin-right: 8px;
}

.login-btn {
  color: #48bb78;
  text-decoration: none;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  padding: 4px 12px;
  border-radius: 16px;
  display: inline-block;
}

.login-btn:hover {
  background: rgba(72, 187, 120, 0.1);
  color: #38a169;
  transform: translateY(-1px);
}

/* 卡片底部 */
.card-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid rgba(66, 153, 225, 0.2);
}

.footer-text {
  color: #718096;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.music-icon {
  font-size: 14px;
  opacity: 0.7;
}

/* 背景装饰 */
.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float-bg 20s ease-in-out infinite;
}

.circle-1 {
  width: 200px;
  height: 200px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 10%;
  animation-delay: 7s;
}

.circle-3 {
  width: 100px;
  height: 100px;
  bottom: 20%;
  left: 20%;
  animation-delay: 14s;
}

@keyframes float-bg {
  0%, 100% {
    transform: translateY(0px) scale(1);
    opacity: 0.1;
  }
  50% {
    transform: translateY(-30px) scale(1.1);
    opacity: 0.15;
  }
}

.floating-bg-icons {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.bg-icon {
  position: absolute;
  font-size: 24px;
  opacity: 0.1;
  animation: float-bg-icon 15s ease-in-out infinite;
}

.bg-music {
  top: 20%;
  left: 15%;
  animation-delay: 0s;
}

.bg-guitar {
  top: 30%;
  right: 20%;
  animation-delay: 5s;
}

.bg-cat {
  bottom: 30%;
  right: 15%;
  animation-delay: 10s;
}

.bg-blues {
  bottom: 20%;
  left: 25%;
  animation-delay: 2s;
}

@keyframes float-bg-icon {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.1;
  }
  25% {
    transform: translateY(-20px) rotate(90deg);
    opacity: 0.15;
  }
  50% {
    transform: translateY(-10px) rotate(180deg);
    opacity: 0.08;
  }
  75% {
    transform: translateY(-30px) rotate(270deg);
    opacity: 0.12;
  }
}

/* 响应式优化 */
@media (max-width: 480px) {
  .register-card {
    padding: 30px 20px;
    margin: 10px;
    min-width: auto;
  }

  .register-title {
    font-size: 24px;
  }

  .floating-icons {
    top: -15px;
  }

  .icon {
    font-size: 16px;
  }

  .custom-input :deep(.el-input__wrapper) {
    padding-left: 40px;
    padding-right: 12px;
  }

  .input-icon {
    left: 14px;
    font-size: 16px;
  }
}

/* 无障碍访问优化 */
@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .register-card {
    border: 2px solid #2d3748;
  }

  .custom-input :deep(.el-input__wrapper) {
    border: 2px solid #2d3748;
  }

  .register-btn {
    border: 2px solid #2d3748;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .register-card {
    background: rgba(26, 32, 44, 0.95);
    color: white;
  }

  .register-title {
    color: white;
  }

  .custom-input :deep(.el-input__inner) {
    color: white;
  }

  .footer-text {
    color: #a0aec0;
  }
}
</style>