import { createRouter, createWebHistory } from 'vue-router'
import UserList from '../views/UserList.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Profile from '../views/Profile.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
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
    meta: { requiresAuth: true }
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true'
  const hasToken = localStorage.getItem('access_token')

  // 检查认证状态的有效性
  const isAuthenticated = isLoggedIn && hasToken

  // 如果需要登录验证但用户未认证
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  }
  // 如果已登录，访问登录或注册页面则重定向到用户管理页面
  else if ((to.path === '/login' || to.path === '/register') && isAuthenticated) {
    next('/users')
  }
  // 如果访问根路径，根据认证状态重定向
  else if (to.path === '/') {
    next(isAuthenticated ? '/users' : '/login')
  }
  else {
    next()
  }
})

export default router