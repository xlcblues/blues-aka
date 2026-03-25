<template>
  <div class="rag-metrics-page">
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Management /></el-icon>
        RAG 性能指标仪表板
      </h1>
      <el-button type="primary" @click="fetchMetrics" :loading="loading">
        <el-icon><RefreshRight /></el-icon>
        刷新数据
      </el-button>
    </div>

    <div v-loading="loading" class="metrics-content">
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
            <el-descriptions-item label="使用RAG的对话数">
              {{ metricsData.usage?.rag_conversations || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="活跃用户数">
              {{ metricsData.usage?.active_users || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="平均响应时间">
              {{ formatTime(metricsData.usage?.avg_response_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="总检索文档数">
              {{ metricsData.usage?.total_retrieved_docs || 0 }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 最近评估记录 -->
        <div class="recent-evaluations">
          <h4 class="section-title">
            <el-icon><Document /></el-icon>
            最近 10 条评估记录
          </h4>

          <el-table :data="metricsData.recent_evaluations || []" stripe>
            <el-table-column prop="query" label="查询" show-overflow-tooltip />
            <el-table-column prop="answer" label="回答" show-overflow-tooltip />
            <el-table-column label="准确率" width="120">
              <template #default="{ row }">
                <el-tag :type="getPrecisionType(row.precision)">
                  {{ formatPercent(row.precision || 0) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="召回率" width="120">
              <template #default="{ row }">
                <el-tag :type="getRecallType(row.recall)">
                  {{ formatPercent(row.recall || 0) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="反馈" width="100">
              <template #default="{ row }">
                <span v-if="row.feedback">
                  <el-tag :type="getFeedbackType(row.feedback)">
                    {{ row.feedback }} / 5
                  </el-tag>
                </span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <el-empty v-else-if="!loading" description="暂无数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Management, Search, Reading, Star, InfoFilled, Timer, Document, RefreshRight } from '@element-plus/icons-vue'
import { ragApi } from '../api/rag'

const loading = ref(false)
const metricsData = ref(null)

// 页面加载时获取数据
onMounted(() => {
  fetchMetrics()
})

// 获取指标数据
const fetchMetrics = async () => {
  loading.value = true
  try {
    const response = await ragApi.getMetrics(true)
    if (response.code === 200) {
      metricsData.value = response.data
      ElMessage.success('数据刷新成功')
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

// 获取准确率标签类型
const getPrecisionType = (precision) => {
  if (precision >= 0.8) return 'success'
  if (precision >= 0.6) return ''
  if (precision >= 0.4) return 'warning'
  return 'danger'
}

// 获取召回率标签类型
const getRecallType = (recall) => {
  if (recall >= 0.8) return 'success'
  if (recall >= 0.6) return ''
  if (recall >= 0.4) return 'warning'
  return 'danger'
}

// 获取反馈标签类型
const getFeedbackType = (feedback) => {
  if (feedback >= 4) return 'success'
  if (feedback >= 3) return ''
  if (feedback >= 2) return 'warning'
  return 'danger'
}
</script>

<style scoped>
.rag-metrics-page {
  padding: 24px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.metrics-content {
  min-height: 400px;
}

/* 概览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.metric-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 28px;
  color: white;
}

.metric-icon.total-queries {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.metric-icon.avg-precision {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.metric-icon.avg-recall {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.metric-icon.avg-feedback {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #909399;
}

/* 详细指标、使用统计、最近评估 */
.metrics-detail,
.usage-stats,
.recent-evaluations {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.text-muted {
  color: #909399;
}

/* 表格样式优化 */
:deep(.el-table) {
  border-radius: 4px;
  overflow: hidden;
}

:deep(.el-table th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.el-descriptions) {
  margin-top: 16px;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  background-color: #fafafa !important;
}

/* 响应式 */
@media (max-width: 768px) {
  .rag-metrics-page {
    padding: 16px;
  }

  .overview-cards {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .metrics-detail,
  .usage-stats,
  .recent-evaluations {
    padding: 16px;
  }
}
</style>
