<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="val => emit('update:visible', val)"
    title="RAG 性能指标仪表板"
    width="1000px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-loading="loading" class="metrics-container">
      <div v-if="!loading && metricsData">
        <!-- 概览卡片 -->
        <div class="overview-cards">
          <div class="metric-card">
            <div class="metric-icon total-queries">
              <el-icon><Search /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ metricsData.metrics?.total_queries || 0 }}</div>
              <div class="metric-label">总查询数</div>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon avg-precision">
              <el-icon><Management /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatPercent(metricsData.summary?.avg_precision || 0) }}</div>
              <div class="metric-label">平均准确率</div>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon avg-recall">
              <el-icon><Reading /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatPercent(metricsData.summary?.avg_recall || 0) }}</div>
              <div class="metric-label">平均召回率</div>
            </div>
          </div>

          <div class="metric-card">
            <div class="metric-icon avg-feedback">
              <el-icon><Star /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatFeedback(metricsData.summary?.avg_feedback || 0) }}</div>
              <div class="metric-label">平均满意度</div>
            </div>
          </div>
        </div>

        <!-- 详细指标 -->
        <div class="metrics-detail">
          <h4 class="section-title">
            <el-icon><InfoFilled /></el-icon>
            详细评估指标
          </h4>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="总评估次数">
              {{ metricsData.summary?.total_evaluations || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="平均F1分数">
              {{ formatPercent(metricsData.summary?.avg_f1 || 0) }}
            </el-descriptions-item>
            <el-descriptions-item label="总反馈次数">
              {{ metricsData.summary?.total_feedback || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="平均反馈分数">
              {{ formatFeedback(metricsData.summary?.avg_feedback || 0) }} / 5.0
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 使用统计 -->
        <div class="usage-stats">
          <h4 class="section-title">
            <el-icon><Timer /></el-icon>
            使用统计
          </h4>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="总检索文档数">
              {{ metricsData.metrics?.total_retrievals || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="总Token使用量">
              {{ formatNumber(metricsData.metrics?.total_tokens_used || 0) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 最近性能 -->
        <div class="recent-performance" v-if="metricsData.summary?.recent_performance?.length > 0">
          <h4 class="section-title">
            <el-icon><Timer /></el-icon>
            最近10次评估
          </h4>

          <el-table :data="metricsData.summary.recent_performance" stripe size="small">
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="precision" label="准确率" width="100">
              <template #default="{ row }">
                {{ formatPercent(row.precision) }}
              </template>
            </el-table-column>
            <el-table-column prop="recall" label="召回率" width="100">
              <template #default="{ row }">
                {{ formatPercent(row.recall) }}
              </template>
            </el-table-column>
            <el-table-column prop="f1" label="F1分数" width="100">
              <template #default="{ row }">
                {{ formatPercent(row.f1) }}
              </template>
            </el-table-column>
            <el-table-column prop="query" label="查询" min-width="200" show-overflow-tooltip />
          </el-table>
        </div>
      </div>

      <el-empty v-else-if="!loading" description="暂无指标数据" />
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button type="primary" @click="fetchMetrics">
        <el-icon><RefreshRight /></el-icon>
        刷新
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Management, Reading, Star, InfoFilled, Timer, RefreshRight } from '@element-plus/icons-vue'
import { ragApi } from '../api/rag'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible'])

const loading = ref(false)
const metricsData = ref(null)

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    fetchMetrics()
  }
})

// 获取指标数据
const fetchMetrics = async () => {
  loading.value = true
  try {
    const response = await ragApi.getMetrics(true)
    if (response.code === 200) {
      metricsData.value = response.data
    } else {
      ElMessage.error(response.message || '获取指标失败')
    }
  } catch (error) {
    console.error('获取RAG指标失败:', error)
    ElMessage.error(error.backendMessage || error.message || '获取指标失败')
  } finally {
    loading.value = false
  }
}

// 格式化百分比
const formatPercent = (value) => {
  return `${(value * 100).toFixed(1)}%`
}

// 格式化反馈分数
const formatFeedback = (value) => {
  return value.toFixed(1)
}

// 格式化数字
const formatNumber = (value) => {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(1)}w`
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k`
  }
  return value.toString()
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return 'N/A'
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}

// 关闭对话框
const handleClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.metrics-container {
  min-height: 400px;
}

/* 概览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
}

.metric-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 28px;
  color: white;
}

.metric-content {
  flex: 1;
  color: white;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  opacity: 0.9;
  font-weight: 500;
}

/* 详细部分 */
.metrics-detail,
.usage-stats,
.recent-performance {
  margin-bottom: 28px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.section-title .el-icon {
  font-size: 18px;
}

:deep(.el-descriptions) {
  margin-top: 0;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  background-color: #f5f7fa !important;
  color: #303133;
  width: 140px;
}

:deep(.el-descriptions__body) {
  background-color: #ffffff;
}

:deep(.el-descriptions__cell) {
  padding: 14px 16px;
  line-height: 1.8;
  font-size: 14px;
}

:deep(.el-descriptions__content) {
  color: #606266;
}

/* 表格样式 */
:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
}

:deep(.el-table tr:hover > td) {
  background-color: #f5f7fa !important;
}
</style>
