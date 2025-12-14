import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const userApi = {
  // 获取用户列表
  getUsers(params) {
    return api.get('/user/users', { params })
  },

  // 创建用户
  createUser(data) {
    return api.post('/user/users', data)
  },

  // 更新用户
  updateUser(id, data) {
    return api.put(`/user/users/${id}`, data)
  },

  // 删除用户
  deleteUser(id) {
    return api.delete(`/user/users/${id}`)
  }
}