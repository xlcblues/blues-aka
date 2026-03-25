<template>
  <div class="scheduled-tasks">
    <div class="page-header">
      <h1>定时任务管理</h1>
      <p class="subtitle">管理和监控系统定时任务</p>
    </div>

    <!-- 任务列表卡片 -->
    <el-card class="tasks-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>定时任务列表</span>
          <el-button
            type="primary"
            size="small"
            @click="fetchTasks"
            :loading="loading"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <div v-if="loading && tasks.length === 0" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>

      <div v-else-if="tasks.length === 0" class="empty-container">
        <el-empty description="暂无定时任务" />
      </div>

      <el-table
        v-else
        :data="tasks"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="任务名称" width="200">
          <template #default="{ row }">
            <div class="task-name">
              <el-icon><Clock /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="id" label="任务ID" width="220">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.id }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="trigger" label="执行计划" min-width="250" />

        <el-table-column prop="next_run_time" label="下次执行时间" width="180">
          <template #default="{ row }">
            <div v-if="row.next_run_time" class="next-run-time">
              <el-icon><Calendar /></el-icon>
              <span>{{ formatNextRunTime(row.next_run_time) }}</span>
            </div>
            <el-tag v-else size="small" type="warning">未计划</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.id === 'update_inactive_users'"
              type="primary"
              size="small"
              @click="triggerUpdateStatus"
              :loading="triggering === 'update'"
            >
              <el-icon><VideoPlay /></el-icon>
              立即执行
            </el-button>
            <el-button
              v-if="row.id === 'cleanup_inactive_users'"
              type="danger"
              size="small"
              @click="triggerCleanup"
              :loading="triggering === 'cleanup'"
            >
              <el-icon><VideoPlay /></el-icon>
              立即执行
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户统计卡片 -->
    <el-card class="stats-card" shadow="hover" v-if="userStats">
      <template #header>
        <div class="card-header">
          <span>用户活跃度统计</span>
          <el-button
            type="primary"
            size="small"
            @click="fetchUserStats"
            :loading="statsLoading"
          >
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.total_users || 0 }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value active">{{ userStats.active_users || 0 }}</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value inactive">{{ userStats.inactive_users || 0 }}</div>
            <div class="stat-label">不活跃用户</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value deleted">{{ userStats.deleted_users || 0 }}</div>
            <div class="stat-label">已删除用户</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 任务说明 -->
    <el-card class="info-card" shadow="hover">
      <template #header>
        <span>任务说明</span>
      </template>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="更新不活跃用户状态">
          每天凌晨2:00执行，将30天未登录的用户状态设置为inactive
        </el-descriptions-item>
        <el-descriptions-item label="用户活跃度统计">
          每周一凌晨3:00执行，统计和记录用户活跃度相关数据
        </el-descriptions-item>
        <el-descriptions-item label="清理不活跃用户">
          每月1号凌晨4:00执行，清理180天未登录的用户（软删除）
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Clock,
  Calendar,
  Refresh,
  VideoPlay
} from '@element-plus/icons-vue'
import { tasksApi } from '../api/tasks'

// 响应式数据
const loading = ref(false)
const tasks = ref([])
const triggering = ref(null)
const userStats = ref(null)
const statsLoading = ref(false)

// 获取定时任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await tasksApi.getJobs()
    if (response.code === 200 && response.data) {
      tasks.value = response.data || []
      ElMessage.success('获取定时任务列表成功')
    } else {
      throw new Error(response.message || '获取失败')
    }
  } catch (error) {
    console.error('获取定时任务列表失败:', error)
    ElMessage.error(error.message || '获取定时任务列表失败')
  } finally {
    loading.value = false
  }
}

// 获取用户统计信息
const fetchUserStats = async () => {
  statsLoading.value = true
  try {
    const response = await tasksApi.getUserStats()
    if (response.code === 200 && response.data) {
      userStats.value = response.data
      ElMessage.success('获取用户统计信息成功')
    } else {
      throw new Error(response.message || '获取失败')
    }
  } catch (error) {
    console.error('获取用户统计信息失败:', error)
    ElMessage.error(error.message || '获取用户统计信息失败')
  } finally {
    statsLoading.value = false
  }
}

// 触发用户状态更新任务
const triggerUpdateStatus = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要立即执行"更新不活跃用户状态"任务吗？',
      '确认执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    triggering.value = 'update'
    try {
      const response = await tasksApi.triggerUpdateUserStatus()
      if (response.code === 200) {
        const data = response.data || {}
        ElMessage.success(
          `任务执行成功！更新了 ${data.updated_count || 0} 个用户`
        )
        // 刷新统计数据
        fetchUserStats()
      } else {
        throw new Error(response.message || '执行失败')
      }
    } catch (error) {
      console.error('执行任务失败:', error)
      ElMessage.error(error.message || '执行任务失败')
    } finally {
      triggering.value = null
    }
  } catch {
    // 用户取消
  }
}

// 触发用户清理任务
const triggerCleanup = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要立即执行"清理不活跃用户"任务吗？此操作将软删除180天未登录的用户。',
      '确认执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    triggering.value = 'cleanup'
    try {
      const response = await tasksApi.triggerCleanupUsers()
      if (response.code === 200) {
        const data = response.data || {}
        ElMessage.success(
          `任务执行成功！清理了 ${data.cleaned_count || 0} 个用户`
        )
        // 刷新统计数据
        fetchUserStats()
      } else {
        throw new Error(response.message || '执行失败')
      }
    } catch (error) {
      console.error('执行任务失败:', error)
      ElMessage.error(error.message || '执行任务失败')
    } finally {
      triggering.value = null
    }
  } catch {
    // 用户取消
  }
}

// 格式化下次执行时间
const formatNextRunTime = (isoString) => {
  if (!isoString) return '-'

  try {
    const date = new Date(isoString)
    const now = new Date()
    const diff = date - now

    // 计算剩余时间
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

    let relativeTime = ''
    if (days > 0) {
      relativeTime = `${days}天${hours}小时后`
    } else if (hours > 0) {
      relativeTime = `${hours}小时${minutes}分钟后`
    } else if (minutes > 0) {
      relativeTime = `${minutes}分钟后`
    } else {
      relativeTime = '即将执行'
    }

    // 格式化日期时间
    const dateStr = date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })

    return `${dateStr} (${relativeTime})`
  } catch (error) {
    console.error('格式化时间失败:', error)
    return isoString
  }
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTasks()
  fetchUserStats()
})
</script>

<style scoped>
.scheduled-tasks {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #303133;
}

.subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.tasks-card,
.stats-card,
.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container,
.empty-container {
  padding: 40px 0;
  text-align: center;
}

.task-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.next-run-time {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #409eff;
}

.stat-value.active {
  color: #67c23a;
}

.stat-value.inactive {
  color: #e6a23c;
}

.stat-value.deleted {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}
</style>
