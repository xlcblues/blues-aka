<template>
  <div class="error-test-container">
    <el-card class="test-card">
      <template #header>
        <div class="card-header">
          <span>API 错误处理测试</span>
        </div>
      </template>

      <div class="test-content">
        <el-alert
          title="错误处理已优化"
          type="success"
          description="前端现在可以正确显示后端返回的错误信息"
          :closable="false"
          show-icon
        />

        <div class="error-info">
          <h3>当前后端错误 (500)</h3>
          <el-alert
            title="后端数据库模型错误"
            type="error"
            :description="backendError"
            :closable="false"
            show-icon
          />
        </div>

        <div class="test-buttons">
          <el-button type="primary" @click="testLogin" :loading="loading">
            测试登录接口
          </el-button>
          <el-button @click="clearError">
            清除错误
          </el-button>
        </div>

        <div v-if="lastError" class="error-details">
          <h4>错误详情</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="错误消息">
              {{ lastError.message }}
            </el-descriptions-item>
            <el-descriptions-item label="HTTP 状态码">
              {{ lastError.status }}
            </el-descriptions-item>
            <el-descriptions-item label="错误代码">
              {{ lastError.code }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '../api/user'
import { getErrorMessage, handleApiError } from '../utils/errorHandler'

const loading = ref(false)
const lastError = ref(null)

const backendError = 'One or more mappers failed to initialize - Message model not found'

const testLogin = async () => {
  loading.value = true
  try {
    await authApi.login({
      username: 'test',
      password: '123456'
    })
    ElMessage.success('登录成功')
  } catch (error) {
    const errorInfo = handleApiError(error)
    lastError.value = errorInfo

    const message = getErrorMessage(error)
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

const clearError = () => {
  lastError.value = null
}
</script>

<style scoped>
.error-test-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-card {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.test-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-info {
  margin: 10px 0;
}

.error-info h3 {
  margin-bottom: 10px;
  color: #303133;
}

.test-buttons {
  display: flex;
  gap: 10px;
}

.error-details {
  margin-top: 20px;
}

.error-details h4 {
  margin-bottom: 10px;
  color: #606266;
}
</style>
