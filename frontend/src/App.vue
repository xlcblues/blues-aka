<template>
  <div id="app">
    <!-- 登录页面不需要头部导航 -->
    <div v-if="$route.name === 'Login'">
      <router-view />
    </div>

    <!-- 主应用布局 -->
    <el-container v-else>
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-content">
          <h1 class="logo">
            <span class="logo-icon">🐱‍👤</span>
            <span class="logo-text">Blues AKA 用户管理系统</span>
            <span class="logo-music">🎵</span>
          </h1>
          <div class="header-nav">
            <el-button
              type="primary"
              @click="$router.push('/users')"
              :class="{ 'active-btn': $route.name === 'UserList' }"
            >
              <el-icon><UserFilled /></el-icon>
              用户管理
            </el-button>
            <el-dropdown @command="handleUserAction" class="user-dropdown">
              <el-button class="user-info-btn">
                <el-icon><Avatar /></el-icon>
                {{ username }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="settings">
                    <el-icon><Setting /></el-icon>
                    系统设置
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <!-- 主要内容区域 -->
      <el-main class="main-content">
        <div class="content-wrapper">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authApi } from './api/user'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const username = ref('')

    // 获取用户名
    const getUsername = () => {
      const savedUsername = localStorage.getItem('username')
      username.value = savedUsername || '用户'
    }

    // 处理用户操作
    const handleUserAction = async (command) => {
      switch (command) {
        case 'profile':
          ElMessage.info('个人信息功能开发中...')
          break
        case 'settings':
          ElMessage.info('系统设置功能开发中...')
          break
        case 'logout':
          await handleLogout()
          break
      }
    }

    // 处理登出
    const handleLogout = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        try {
          // 调用后端登出接口
          await authApi.logout()
          ElMessage.success('退出登录成功！')
        } catch (error) {
          console.error('后端登出失败:', error)
          ElMessage.warning('网络错误，但已本地登出')
        }

        // 清除本地登录状态
        localStorage.removeItem('isLoggedIn')
        localStorage.removeItem('username')

        // 跳转到登录页面
        router.push('/login')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('登出操作失败:', error)
        }
      }
    }

    // 检查登录状态
    const checkAuth = () => {
      const isLoggedIn = localStorage.getItem('isLoggedIn')
      if (isLoggedIn !== 'true' && router.currentRoute.value.name !== 'Login') {
        router.push('/login')
      }
    }

    // 组件挂载时执行
    onMounted(() => {
      getUsername()
      checkAuth()
    })

    return {
      username,
      handleUserAction,
      handleLogout
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e8ba3 100%);
  min-height: 100vh;
}

#app {
  min-height: 100vh;
}

.header {
  background: linear-gradient(135deg, #2c5282 0%, #3182ce 50%, #4299e1 100%);
  color: white;
  padding: 0;
  box-shadow: 0 4px 20px 0 rgba(49, 130, 206, 0.4);
  position: relative;
  overflow: hidden;
}

.header::before {
  content: '🎵';
  position: absolute;
  top: 10px;
  right: 80px;
  font-size: 24px;
  opacity: 0.3;
  animation: float 3s ease-in-out infinite;
}

.header::after {
  content: '🐱‍👤';
  position: absolute;
  top: 0;
  right: 20px;
  font-size: 48px;
  opacity: 0.15;
  filter: grayscale(30%);
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  position: relative;
  z-index: 2;
}

.logo {
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  color: white;
  margin: 0;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 15px;
}

.main-content {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.content-wrapper {
  animation: fadeInUp 0.4s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 头部导航样式增强 */
.logo {
  font-size: 24px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  margin: 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.8px;
  position: relative;
}

.logo-icon {
  font-size: 28px;
  filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.4));
  animation: bounce 2s ease-in-out infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-8px);
  }
  60% {
    transform: translateY(-4px);
  }
}

.logo-text {
  position: relative;
  z-index: 2;
}

.logo-music {
  font-size: 20px;
  opacity: 0.8;
  animation: float 3s ease-in-out infinite;
  margin-left: 4px;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-6px) rotate(10deg);
  }
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 16px;
}

.active-btn {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
  box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4) !important;
  transform: translateY(-1px);
}

/* 用户下拉菜单 */
.user-dropdown {
  margin-left: 8px;
}

.user-info-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
  font-weight: 500;
  padding: 10px 16px;
  border-radius: 20px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-info-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
}

/* 下拉菜单样式 */
:deep(.el-dropdown-menu) {
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(0, 0, 0, 0.08);
  padding: 8px;
}

:deep(.el-dropdown-menu__item) {
  border-radius: 8px;
  padding: 10px 16px;
  margin: 2px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  font-weight: 500;
}

:deep(.el-dropdown-menu__item:hover) {
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  color: #2d3748;
  transform: translateX(2px);
}

:deep(.el-dropdown-menu__item.is-divided) {
  border-top: 1px solid #e2e8f0;
  margin-top: 8px;
  padding-top: 12px;
}

:deep(.el-dropdown-menu__item.is-divided:hover) {
  background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
  color: #e53e3e;
}

/* 全局样式 */
.page-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(49, 130, 206, 0.15);
  border: 1px solid rgba(66, 153, 225, 0.3);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}

.page-container::before {
  content: '🐱‍👤';
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 20px;
  opacity: 0.15;
  filter: grayscale(40%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}
</style>