import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import UserList from '../views/UserList.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import Settings from '../views/Settings.vue'
import AgentList from '../views/AgentList.vue'
import ConversationList from '../views/ConversationList.vue'
import Chat from '../views/Chat.vue'
import RAGMetrics from '../views/RAGMetrics.vue'
import RAGIndexManagement from '../views/RAGIndexManagement.vue'

const routes = [
  {
    path: '/',
    redirect: '/agents'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false }
  },
  {
    path: '/users',
    name: 'UserList',
    component: UserList,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/rag-metrics',
    name: 'RAGMetrics',
    component: RAGMetrics,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/rag-index',
    name: 'RAGIndexManagement',
    component: RAGIndexManagement,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: '/agents',
    name: 'AgentList',
    component: AgentList,
    meta: { requiresAuth: true }
  },
  {
    path: '/conversations',
    name: 'ConversationList',
    component: ConversationList,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 初始化认证状态
  authStore.initializeAuth()

  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
  const hasToken = localStorage.getItem('access_token')

  // 检查认证状态的有效性
  const isAuthenticated = isLoggedIn && hasToken

  // 如果需要登录验证但用户未认证
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
    return
  }

  // 如果需要认证且token存在，验证token是否有效
  if (to.meta.requiresAuth && isAuthenticated) {
    try {
      // 验证token有效性 - 通过获取当前用户信息来验证
      // 如果token过期，这个请求会失败并抛出401错误
      if (!authStore.userId) {
        await authStore.fetchCurrentUser()
      }
    } catch (error) {
      console.error('Token验证失败:', error)
      // token过期或无效，清除认证状态并跳转到登录页
      authStore.clearAuth()
      next('/login')
      return
    }
  }

  // 如果需要管理员权限但用户不是管理员
  if (to.meta.requiresAdmin && isAuthenticated) {
    console.log('🔍 访问管理员页面:', to.path)
    console.log('🔍 当前状态:', {
      userId: authStore.userId,
      isAdmin: authStore.isAdmin,
      username: authStore.username
    })

    // 如果还没有获取用户ID或需要验证管理员状态，先获取
    if (!authStore.userId) {
      try {
        console.log('📡 正在获取用户信息...')
        const userData = await authStore.fetchCurrentUser()
        console.log('✅ 用户信息获取成功:', userData)
        console.log('✅ 更新后的isAdmin:', authStore.isAdmin)
      } catch (error) {
        console.error('❌ 获取用户信息失败:', error)
        // token过期或无效，清除认证状态并跳转到登录页
        authStore.clearAuth()
        next('/login')
        return
      }
    }

    // 检查是否是管理员
    console.log('🔑 检查管理员权限，isAdmin =', authStore.isAdmin)
    if (!authStore.isAdmin) {
      console.log('⛔ 非管理员用户尝试访问管理员页面，重定向到 /agents')
      next('/agents') // 重定向到智能体列表页
      return
    }

    console.log('✅ 管理员权限验证通过')
  }

  // 如果已登录，访问登录或注册页面则重定向到智能体列表
  if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    next('/agents')
    return
  }

  // 如果访问根路径，根据认证状态重定向
  if (to.path === '/') {
    next(isAuthenticated ? '/agents' : '/login')
    return
  }

  next()
})

export default router