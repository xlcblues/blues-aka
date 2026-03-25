<template>
  <div class="rag-index-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><FolderOpened /></el-icon>
        RAG 索引管理
      </h1>
      <div class="header-actions">
        <el-button @click="fetchIndexes" :loading="loading">
          <el-icon><RefreshRight /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 健康摘要卡片 -->
    <div class="health-summary-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="summary-card total">
            <div class="card-icon">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ healthSummary.total_indexes || 0 }}</div>
              <div class="card-label">总索引数</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="summary-card healthy">
            <div class="card-icon">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ healthSummary.healthy_indexes || 0 }}</div>
              <div class="card-label">健康索引</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="summary-card unhealthy">
            <div class="card-icon">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ healthSummary.unhealthy_indexes || 0 }}</div>
              <div class="card-label">异常索引</div>
            </div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="summary-card info">
            <div class="card-icon">
              <el-icon><InfoFilled /></el-icon>
            </div>
            <div class="card-content">
              <div class="card-value">{{ totalWarnings || 0 }}</div>
              <div class="card-label">警告数量</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 索引列表 -->
    <div class="indexes-section">
      <el-card class="indexes-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span>索引列表</span>
            <el-tag type="info" size="small">{{ indexes.length }} 个索引</el-tag>
          </div>
        </template>

        <el-table
          :data="indexes"
          v-loading="loading"
          stripe
          style="width: 100%"
          @row-click="showIndexDetail"
        >
          <el-table-column prop="name" label="索引名称" min-width="180">
            <template #default="{ row }">
              <div class="index-name">
                <el-icon><Folder /></el-icon>
                <span>{{ row.name }}</span>
                <el-tag
                  v-if="row.health !== undefined"
                  :type="row.health ? 'success' : 'danger'"
                  size="small"
                  round
                >
                  {{ row.health ? '健康' : '异常' }}
                </el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

          <el-table-column prop="num_documents" label="文档数" width="100" align="center">
            <template #default="{ row }">
              <el-tag type="info" size="small">{{ row.num_documents || 0 }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column prop="updated_at" label="更新时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.updated_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button
                text
                type="primary"
                size="small"
                @click.stop="showIndexDetail(row)"
              >
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-button
                text
                type="success"
                size="small"
                @click.stop="showVersions(row)"
              >
                <el-icon><Clock /></el-icon>
                版本
              </el-button>
              <el-dropdown @command="(cmd) => handleRowCommand(cmd, row)" trigger="click" @click.stop>
                <el-button text size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="health">
                      <el-icon><Monitor /></el-icon>
                      健康检查
                    </el-dropdown-item>
                    <el-dropdown-item command="update">
                      <el-icon><Edit /></el-icon>
                      增量更新
                    </el-dropdown-item>
                    <el-dropdown-item command="rebuild" divided>
                      <el-icon><RefreshRight /></el-icon>
                      重建索引
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" style="color: #f56c6c">
                      <el-icon><Delete /></el-icon>
                      删除索引
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 索引详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`索引详情 - ${currentIndex?.name}`"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-descriptions :column="2" border v-if="currentIndex">
        <el-descriptions-item label="索引名称">
          {{ currentIndex.name }}
        </el-descriptions-item>
        <el-descriptions-item label="文档数量">
          <el-tag type="info">{{ currentIndex.num_documents || 0 }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="存储类型">
          {{ currentIndex.store_type || 'N/A' }}
        </el-descriptions-item>
        <el-descriptions-item label="嵌入模型">
          <el-tag type="success">{{ currentIndex.embedding_model || 'N/A' }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ formatDate(currentIndex.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="2">
          {{ formatDate(currentIndex.updated_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="索引路径" :span="2">
          {{ currentIndex.path || 'N/A' }}
        </el-descriptions-item>
        <el-descriptions-item label="索引大小" :span="2">
          <template v-if="currentIndex.size_mb !== undefined">
            {{ currentIndex.size_mb }} MB ({{ formatBytes(currentIndex.size) }} 字节)
          </template>
          <template v-else>N/A</template>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ currentIndex.description || '无描述' }}
        </el-descriptions-item>
      </el-descriptions>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="showVersions(currentIndex)">查看版本历史</el-button>
      </template>
    </el-dialog>

    <!-- 健康检查对话框 -->
    <el-dialog
      v-model="healthDialogVisible"
      title="索引健康检查报告"
      width="700px"
      :close-on-click-modal="false"
    >
      <div v-if="currentHealth">
        <!-- 总体状态 -->
        <el-alert
          :type="currentHealth.healthy ? 'success' : 'error'"
          :title="currentHealth.healthy ? '索引状态健康' : '发现健康问题'"
          :closable="false"
          show-icon
          style="margin-bottom: 20px"
        />

        <!-- 问题列表 -->
        <div v-if="currentHealth.issues && currentHealth.issues.length > 0" class="health-section">
          <h4>
            <el-icon><CircleClose /></el-icon>
            发现的问题 ({{ currentHealth.issues.length }})
          </h4>
          <ul class="issue-list">
            <li v-for="(issue, index) in currentHealth.issues" :key="index" class="issue-item error">
              {{ issue }}
            </li>
          </ul>
        </div>

        <!-- 警告列表 -->
        <div v-if="currentHealth.warnings && currentHealth.warnings.length > 0" class="health-section">
          <h4>
            <el-icon><Warning /></el-icon>
            警告信息 ({{ currentHealth.warnings.length }})
          </h4>
          <ul class="issue-list">
            <li v-for="(warning, index) in currentHealth.warnings" :key="index" class="issue-item warning">
              {{ warning }}
            </li>
          </ul>
        </div>

        <!-- 基本信息 -->
        <div v-if="currentHealth.info" class="health-section">
          <h4>
            <el-icon><InfoFilled /></el-icon>
            索引信息
          </h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item
              v-for="(value, key) in currentHealth.info"
              :key="key"
              :label="formatInfoKey(key)"
            >
              {{ formatInfoValue(value, key) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 修复建议 -->
        <div v-if="currentHealth.recommendations && currentHealth.recommendations.length > 0" class="health-section">
          <h4>
            <el-icon><MagicStick /></el-icon>
            修复建议
          </h4>
          <ul class="recommendation-list">
            <li v-for="(rec, index) in currentHealth.recommendations" :key="index" class="recommendation-item">
              <el-icon><Check /></el-icon>
              {{ rec }}
            </li>
          </ul>
        </div>
      </div>

      <template #footer>
        <el-button @click="healthDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="runDeepHealthCheck">深度检查</el-button>
      </template>
    </el-dialog>

    <!-- 版本历史对话框 -->
    <el-dialog
      v-model="versionsDialogVisible"
      :title="`版本历史 - ${currentVersions?.index_name}`"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-timeline v-if="currentVersions && currentVersions.versions">
        <el-timeline-item
          v-for="(version, index) in reversed(currentVersions.versions)"
          :key="index"
          :timestamp="formatDate(version.timestamp)"
          placement="top"
          :type="getVersionType(version.change_type)"
        >
          <el-card>
            <div class="version-header">
              <el-tag :type="getVersionTagType(version.change_type)" size="small">
                {{ version.change_type }}
              </el-tag>
              <span class="version-number">{{ version.version }}</span>
            </div>
            <p class="version-description">{{ version.description }}</p>
            <div class="version-meta">
              <el-icon><Document /></el-icon>
              文档数: {{ version.num_documents }}
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-if="!currentVersions?.versions || currentVersions.versions.length === 0" description="暂无版本历史" />

      <template #footer>
        <el-button @click="versionsDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened,
  RefreshRight,
  Collection,
  CircleCheck,
  CircleClose,
  InfoFilled,
  Folder,
  View,
  Clock,
  MoreFilled,
  Monitor,
  Edit,
  Delete,
  Warning,
  MagicStick,
  Check,
  Document
} from '@element-plus/icons-vue'
import { ragIndexApi } from '../api/ragIndex'

// 数据
const loading = ref(false)
const indexes = ref([])
const healthSummary = ref({})
const currentIndex = ref(null)
const currentHealth = ref(null)
const currentVersions = ref(null)

// 对话框状态
const detailDialogVisible = ref(false)
const healthDialogVisible = ref(false)
const versionsDialogVisible = ref(false)

// 计算属性
const totalWarnings = computed(() => {
  return healthSummary.value.indexes?.reduce((sum, idx) => sum + (idx.warnings || 0), 0) || 0
})

// 方法
const fetchIndexes = async () => {
  loading.value = true
  try {
    const response = await ragIndexApi.listIndexes({ includeHealth: true })
    if (response.code === 200) {
      indexes.value = response.data.indexes || []

      // 获取健康摘要
      await fetchHealthSummary()
    }
  } catch (error) {
    ElMessage.error(error.message || '获取索引列表失败')
  } finally {
    loading.value = false
  }
}

const fetchHealthSummary = async () => {
  try {
    const response = await ragIndexApi.getHealthSummary()
    if (response.code === 200) {
      healthSummary.value = response.data
    }
  } catch (error) {
    console.error('获取健康摘要失败:', error)
  }
}

const showIndexDetail = async (row) => {
  try {
    const response = await ragIndexApi.getIndexInfo(row.name)
    if (response.code === 200) {
      currentIndex.value = response.data
      detailDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error(error.message || '获取索引详情失败')
  }
}

const checkIndexHealth = async (row, deepCheck = false) => {
  try {
    const response = await ragIndexApi.checkIndexHealth(row.name, { deepCheck })
    if (response.code === 200) {
      currentHealth.value = response.data
      healthDialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error(error.message || '健康检查失败')
  }
}

const showVersions = async (row) => {
  try {
    const response = await ragIndexApi.getIndexVersions(row.name)
    if (response.code === 200) {
      currentVersions.value = response.data
      versionsDialogVisible.value = true
      detailDialogVisible.value = false
    }
  } catch (error) {
    ElMessage.error(error.message || '获取版本历史失败')
  }
}

const handleRowCommand = (command, row) => {
  switch (command) {
    case 'health':
      checkIndexHealth(row)
      break
    case 'update':
      ElMessage.info('增量更新功能开发中...')
      break
    case 'rebuild':
      ElMessage.info('重建索引功能开发中...')
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除索引 "${row.name}" 吗?此操作不可恢复!`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await ragIndexApi.deleteIndex(row.name)
    if (response.code === 200) {
      ElMessage.success('索引删除成功')
      await fetchIndexes()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除索引失败')
    }
  }
}

const runDeepHealthCheck = () => {
  if (currentIndex.value) {
    checkIndexHealth(currentIndex.value, true)
  }
}

// 工具方法
const formatDate = (dateStr) => {
  if (!dateStr || dateStr === 'N/A') return 'N/A'
  try {
    return new Date(dateStr).toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

const formatBytes = (bytes) => {
  if (!bytes) return 0
  return bytes.toLocaleString()
}

const formatInfoKey = (key) => {
  const keyMap = {
    name: '索引名称',
    num_documents: '文档数量',
    days_since_update: '未更新天数',
    size_bytes: '大小(字节)',
    size_mb: '大小(MB)',
    search_test: '搜索测试',
    num_versions: '版本数量',
    last_version: '最新版本'
  }
  return keyMap[key] || key
}

const formatInfoValue = (value, key) => {
  if (key === 'days_since_update' && typeof value === 'number') {
    return `${value} 天`
  }
  if (key === 'size_mb' && typeof value === 'number') {
    return `${value.toFixed(2)} MB`
  }
  if (key === 'search_test') {
    return value === 'passed' ? '通过' : value
  }
  return value || 'N/A'
}

const getVersionType = (changeType) => {
  const typeMap = {
    created: 'primary',
    updated: 'success',
    rebuilt: 'warning'
  }
  return typeMap[changeType] || 'info'
}

const getVersionTagType = (changeType) => {
  const typeMap = {
    created: 'primary',
    updated: 'success',
    rebuilt: 'warning'
  }
  return typeMap[changeType] || 'info'
}

// 生命周期
onMounted(() => {
  fetchIndexes()
})
</script>

<style scoped>
.rag-index-management {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 健康摘要卡片 */
.health-summary-section {
  margin-bottom: 24px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  margin-bottom: 20px;
}

.summary-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.summary-card.total .card-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.summary-card.healthy .card-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.summary-card.unhealthy .card-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.summary-card.info .card-icon {
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28px;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
  margin-bottom: 8px;
}

.card-label {
  font-size: 14px;
  color: #909399;
}

/* 索引列表 */
.indexes-section {
  margin-bottom: 24px;
}

.indexes-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.index-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 健康检查对话框 */
.health-section {
  margin-bottom: 24px;
}

.health-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.issue-list,
.recommendation-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.issue-item {
  padding: 10px 16px;
  margin-bottom: 8px;
  border-radius: 6px;
  border-left: 4px solid;
}

.issue-item.error {
  background-color: #fef0f0;
  border-left-color: #f56c6c;
  color: #f56c6c;
}

.issue-item.warning {
  background-color: #fdf6ec;
  border-left-color: #e6a23c;
  color: #e6a23c;
}

.recommendation-item {
  padding: 10px 16px;
  margin-bottom: 8px;
  background-color: #f0f9ff;
  border-radius: 6px;
  border-left: 4px solid #409eff;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 版本历史 */
.version-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.version-number {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #606266;
}

.version-description {
  margin: 8px 0;
  color: #606266;
}

.version-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #909399;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .rag-index-management {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .summary-card {
    padding: 16px;
  }

  .card-value {
    font-size: 24px;
  }
}
</style>
