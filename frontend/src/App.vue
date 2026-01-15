<template>
  <div id="app">
    <!-- 登录页面不需要侧边栏 -->
    <div v-if="$route.name === 'Login' || $route.name === 'Register'">
      <router-view />
    </div>

    <!-- 主应用布局 -->
    <el-container v-else class="main-layout" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
      <!-- 侧边栏 -->
      <Sidebar @collapse-change="handleSidebarCollapse" />

      <!-- 右侧内容区域 -->
      <el-container class="content-container">
        <!-- 顶部导航栏 -->
        <el-header class="header">
          <div class="header-content">
            <div class="header-left">
              <h1 class="page-title">
                <span class="title-icon">{{ currentPageIcon }}</span>
                <span class="title-text">{{ currentPageTitle }}</span>
              </h1>
            </div>
            <div class="header-right">
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
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { authApi } from './api/user'
import { useAuthStore } from './stores/auth'
import Sidebar from './components/Sidebar.vue'

export default {
  name: 'App',
  components: {
    Sidebar
  },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const authStore = useAuthStore()
    const username = ref('')
    const isSidebarCollapsed = ref(false)

    // 获取用户名
    const getUsername = () => {
      const savedUsername = localStorage.getItem('username')
      username.value = savedUsername || '用户'
    }

    // 当前页面标题和图标
    const currentPageTitle = computed(() => {
      const titleMap = {
        'AgentList': '智能体管理',
        'UserList': '用户管理',
        'ConversationList': '对话列表',
        'Chat': '对话聊天',
        'Profile': '个人信息',
        'Settings': '系统设置'
      }
      return titleMap[route.name] || 'Blues AKA'
    })

    const currentPageIcon = computed(() => {
      const iconMap = {
        'AgentList': '🤖',
        'UserList': '👥',
        'ConversationList': '💬',
        'Chat': '💭',
        'Profile': '👤',
        'Settings': '⚙️'
      }
      return iconMap[route.name] || '🎵'
    })

    // 处理用户操作
    const handleUserAction = async (command) => {
      switch (command) {
        case 'profile':
          router.push('/profile')
          break
        case 'settings':
          router.push('/settings')
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
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')

        // 跳转到登录页面
        router.push('/login')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('登出操作失败:', error)
        }
      }
    }

    // 处理侧边栏折叠状态变化
    const handleSidebarCollapse = (collapsed) => {
      isSidebarCollapsed.value = collapsed
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
      // 初始化认证状态
      authStore.initializeAuth()
      getUsername()
      checkAuth()
    })

    return {
      username,
      currentPageTitle,
      currentPageIcon,
      handleUserAction,
      handleLogout,
      isSidebarCollapsed,
      handleSidebarCollapse
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

/* 添加动态背景效果 */
body::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(99, 102, 241, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 40% 20%, rgba(168, 85, 247, 0.3) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
  animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

#app {
  min-height: 100vh;
}

/* 主布局 */
.main-layout {
  min-height: 100vh;
  display: flex;
}

.content-container {
  margin-left: 240px;
  transition: margin-left 0.3s ease;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  width: calc(100% - 240px);
}

/* 侧边栏折叠时的样式调整 - 内容区域占满全屏 */
.main-layout.sidebar-collapsed .content-container {
  margin-left: 0;
  width: 100%;
}

/* 顶部导航栏 */
.header {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.95) 0%, rgba(168, 85, 247, 0.95) 100%);
  backdrop-filter: blur(20px);
  color: white;
  padding: 0 30px;
  box-shadow: 0 4px 30px rgba(99, 102, 241, 0.3);
  position: relative;
  overflow: hidden;
  height: 60px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
  pointer-events: none;
  opacity: 0.6;
}

/* 添加动态光效 */
.header::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  animation: headerShine 8s linear infinite;
  pointer-events: none;
}

@keyframes headerShine {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(50%, 50%);
  }
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  position: relative;
  z-index: 2;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: white;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);
}

.title-icon {
  font-size: 24px;
  filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.3));
}

.title-text {
  letter-spacing: 0.5px;
}

/* 主要内容区域 */
.main-content {
  padding: 30px;
  flex: 1;
  overflow-y: auto;
  background: transparent;
  position: relative;
  z-index: 1;
}

.content-wrapper {
  animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  max-width: 1400px;
  margin: 0 auto;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 用户下拉菜单 */
.user-dropdown {
  margin-left: 8px;
}

.user-info-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(15px);
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 25px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.user-info-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 8px 25px rgba(255, 255, 255, 0.3);
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

/* 响应式设计 */
@media (max-width: 768px) {
  .content-container {
    margin-left: 64px;
  }

  .header {
    padding: 0 15px;
  }

  .page-title {
    font-size: 18px;
  }

  .title-icon {
    font-size: 20px;
  }

  .main-content {
    padding: 20px 15px;
  }
}
</style>