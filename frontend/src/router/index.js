import { createRouter, createWebHistory } from 'vue-router'
import UserList from '../views/UserList.vue'

const routes = [
  {
    path: '/',
    redirect: '/users'
  },
  {
    path: '/users',
    name: 'UserList',
    component: UserList
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router