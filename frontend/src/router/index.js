import { createRouter, createWebHistory } from 'vue-router'
import UserList from '../views/UserList.vue'
import Login from '../views/Login.vue'

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
    path: '/users',
    name: 'UserList',
    component: UserList,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isLoggedIn = localStorage.getItem('isLoggedIn')

  // 如果需要登录验证
  if (to.meta.requiresAuth && isLoggedIn !== 'true') {
    next('/login')
  }
  // 如果已登录，访问登录页面则重定向到用户管理页面
  else if (to.path === '/login' && isLoggedIn === 'true') {
    next('/users')
  }
  else {
    next()
  }
})

export default router