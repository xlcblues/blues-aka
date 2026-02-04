<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon class="title-icon"><Avatar /></el-icon>
          智能体管理
        </h2>
      </div>
      <div class="header-right">
        <el-radio-group v-model="viewMode" @change="handleViewModeChange" class="view-mode-selector" size="large">
          <el-radio-button value="all">
            <el-icon><Grid /></el-icon>
            <span>全部智能体</span>
          </el-radio-button>
          <el-radio-button value="mine">
            <el-icon><User /></el-icon>
            <span>我的智能体</span>
          </el-radio-button>
          <el-radio-button value="public">
            <el-icon><Open /></el-icon>
            <span>公开智能体</span>
          </el-radio-button>
        </el-radio-group>
        <el-button type="primary" size="large" @click="showCreateDialog" class="create-btn">
          <el-icon><Plus /></el-icon>
          <span>创建智能体</span>
        </el-button>
      </div>
    </div>

    <!-- 智能体表格 -->
    <div class="table-container">
      <el-table
        v-loading="loading"
        :data="agents"
        stripe
        style="width: 100%"
        class="agent-table"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column prop="id" label="#" width="80" align="center">
          <template #default="{ row }">
            <span class="agent-id">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column label="头像" width="100" align="center">
          <template #default="{ row }">
            <el-avatar :size="60" :src="row.avatar" class="table-avatar">
              {{ row.name.charAt(0) }}
            </el-avatar>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="名称" min-width="180">
          <template #default="{ row }">
            <div class="name-cell">
              <span class="name-text">{{ row.name }}</span>
              <el-tag v-if="!row.is_active" type="danger" size="small">已禁用</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="300">
          <template #default="{ row }">
            <span class="description-text">{{ row.description || '暂无描述' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="model" label="模型" width="150">
          <template #default="{ row }">
            <el-tag type="info">{{ row.model }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_public ? 'success' : 'info'" size="small">
              {{ row.is_public ? '公开' : '私有' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="使用统计" width="150" align="center">
          <template #default="{ row }">
            <div class="stats-cell">
              <span>
                <el-icon><ChatDotRound /></el-icon>
                {{ row.usage_count || 0 }} 次
              </span>
              <span v-if="row.rating">
                <el-icon><Star /></el-icon>
                {{ row.rating }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="startChat(row)" link>
                <el-icon><ChatDotRound /></el-icon>
                对话
              </el-button>
              <el-divider direction="vertical" />
              <el-button type="primary" size="small" @click="viewAgent(row)" link>
                <el-icon><View /></el-icon>
                详情
              </el-button>
              <el-divider direction="vertical" />
              <el-button type="warning" size="small" @click="editAgent(row)" link>
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-divider direction="vertical" />
              <el-button type="danger" size="small" @click="handleDelete(row)" link>
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchAgents"
        @current-change="fetchAgents"
      />
    </div>

    <!-- 创建/编辑智能体对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑智能体' : '创建智能体'"
      width="800px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入智能体名称" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入智能体描述"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="头像" prop="avatar">
          <el-input v-model="form.avatar" placeholder="请输入头像URL" />
        </el-form-item>

        <el-form-item label="模型" prop="model">
          <el-select v-model="form.model" placeholder="请选择模型">
            <el-option label="GLM-4.5 (推荐)" value="glm-4.5" />
            <el-option label="GLM-4.6 (高性能)" value="glm-4.6" />
            <el-option label="GLM-4.5-Air (快速)" value="glm-4.5-air" />
            <el-option label="GLM-4.5V (多模态)" value="glm-4.5v" />
          </el-select>
        </el-form-item>

        <el-form-item label="系统提示词" prop="system_prompt">
          <el-input
            v-model="form.system_prompt"
            type="textarea"
            :rows="5"
            placeholder="请输入系统提示词，定义智能体的角色和行为"
            maxlength="10000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="提示词模式" prop="prompt_mode">
          <el-select v-model="form.prompt_mode" placeholder="请选择模式">
            <el-option label="默认" value="default" />
            <el-option label="编程" value="coding" />
            <el-option label="创意" value="creative" />
          </el-select>
        </el-form-item>

        <el-form-item label="温度" prop="temperature">
          <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>

        <el-form-item label="最大Token" prop="max_tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="32000" :step="100" />
        </el-form-item>

        <el-form-item label="是否公开" prop="is_public">
          <el-switch v-model="form.is_public" />
          <span class="form-tip">公开后其他用户也可以使用此智能体</span>
        </el-form-item>

        <el-divider content-position="left">
          <el-icon><Setting /></el-icon>
          高级配置
        </el-divider>

        <el-form-item label="启用联网搜索" prop="enable_web_search">
          <el-switch v-model="form.enable_web_search" />
          <span class="form-tip">允许智能体使用联网搜索获取最新信息</span>
        </el-form-item>

        <el-form-item label="RAG配置" prop="enable_rag">
          <el-switch v-model="form.enable_rag" />
          <span class="form-tip">启用检索增强生成（RAG）功能</span>
        </el-form-item>

        <el-form-item v-if="form.enable_rag" label="RAG索引名称" prop="rag_index_name">
          <el-input v-model="form.rag_index_name" placeholder="请输入RAG知识库索引名称" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看智能体详情对话框 -->
    <el-dialog v-model="detailVisible" title="智能体详情" width="900px">
      <div v-if="currentAgent" class="agent-detail">
        <div class="detail-header">
          <el-avatar :size="80" :src="currentAgent.avatar">
            {{ currentAgent.name.charAt(0) }}
          </el-avatar>
          <div class="header-info">
            <h2>{{ currentAgent.name }}</h2>
            <p>{{ currentAgent.model }}</p>
          </div>
        </div>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="描述">
            {{ currentAgent.description || '暂无描述' }}
          </el-descriptions-item>
          <el-descriptions-item label="系统提示词">
            <div class="prompt-text">{{ currentAgent.system_prompt || '未设置' }}</div>
          </el-descriptions-item>
          <el-descriptions-item label="温度">{{ currentAgent.temperature }}</el-descriptions-item>
          <el-descriptions-item label="最大Token">{{ currentAgent.max_tokens }}</el-descriptions-item>
          <el-descriptions-item label="使用次数">{{ currentAgent.usage_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="评分">
            <el-rate v-model="currentAgent.rating" disabled show-score />
          </el-descriptions-item>
        </el-descriptions>

        <div class="detail-actions">
          <el-button type="primary" @click="startChat(currentAgent)">
            <el-icon><ChatDotRound /></el-icon>
            开始对话
          </el-button>
          <el-button @click="editAgent(currentAgent)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button type="danger" @click="handleDelete(currentAgent)">
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { agentApi } from '../api/agent'
import { formatTime } from '../utils/time'

const router = useRouter()

// 数据状态
const loading = ref(false)
const agents = ref([])
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const viewMode = ref('all') // 'all' | 'mine' | 'public'

// 对话框状态
const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const currentAgent = ref(null)

// 表单数据
const form = ref({
  name: '',
  description: '',
  avatar: '',
  model: 'glm-4.5',
  system_prompt: '',
  prompt_mode: 'default',
  temperature: 0.7,
  max_tokens: 2000,
  top_p: 1.0,
  is_public: false,
  // 新增字段
  enable_web_search: false,
  enable_rag: false,
  rag_index_name: ''
})

const formRef = ref(null)

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入智能体名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  model: [
    { required: true, message: '请选择模型', trigger: 'change' }
  ]
}

// 获取智能体列表
const fetchAgents = async () => {
  try {
    loading.value = true

    // 根据视图模式构建参数
    let params = {
      page: currentPage.value,
      size: pageSize.value
    }

    // 根据视图模式添加 is_public 参数
    // 注意: 只有明确需要时才添加 is_public 参数
    if (viewMode.value === 'public') {
      params.is_public = 'true'  // 字符串 'true' 表示只要公开的
    } else if (viewMode.value === 'mine') {
      params.is_public = 'false'  // 字符串 'false' 表示只要自己的
    }
    // viewMode === 'all' 时不传 is_public 参数,默认返回公开的+自己的

    const response = await agentApi.getAgents(params)

    if (response.code === 200) {
      agents.value = response.data.items
      total.value = response.data.total
    } else {
      ElMessage.error(response.message || '获取智能体列表失败')
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    ElMessage.error('获取智能体列表失败')
  } finally {
    loading.value = false
  }
}

// 处理视图模式切换
const handleViewModeChange = () => {
  currentPage.value = 1 // 重置到第一页
  fetchAgents()
}

// 显示创建对话框
const showCreateDialog = () => {
  isEdit.value = false
  dialogVisible.value = true
}

// 查看智能体详情
const viewAgent = (agent) => {
  currentAgent.value = agent
  detailVisible.value = true
}

// 编辑智能体
const editAgent = (agent) => {
  currentAgent.value = agent
  form.value = { ...agent }
  isEdit.value = true
  dialogVisible.value = true
  detailVisible.value = false
}

// 删除智能体
const handleDelete = async (agent) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体 "${agent.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await agentApi.deleteAgent(agent.id)
    ElMessage.success('删除成功')
    detailVisible.value = false
    fetchAgents()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    submitting.value = true
    let response

    if (isEdit.value) {
      response = await agentApi.updateAgent(currentAgent.value.id, form.value)
    } else {
      response = await agentApi.createAgent(form.value)
    }

    if (response.code === 200) {
      ElMessage.success(isEdit.value ? '保存成功' : '创建成功')
      dialogVisible.value = false
      fetchAgents()
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('操作失败')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    avatar: '',
    model: 'glm-4.5',
    system_prompt: '',
    prompt_mode: 'default',
    temperature: 0.7,
    max_tokens: 2000,
    top_p: 1.0,
    is_public: false
  }
  formRef.value?.resetFields()
}

// 开始对话
const startChat = (agent) => {
  router.push({
    name: 'Chat',
    query: { agentId: agent.id }
  })
}

onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
/* 页面容器 */
.page-container {
  padding: 24px;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon {
  font-size: 28px;
  color: #409eff;
}

/* 视图模式选择器 */
.view-mode-selector {
  display: flex;
  align-items: center;
}

.view-mode-selector :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.view-mode-selector :deep(.el-radio-button__inner:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.2);
}

.view-mode-selector :deep(.el-icon) {
  font-size: 16px;
}

/* 创建按钮 */
.create-btn {
  font-weight: 500;
  padding: 12px 24px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

/* 表格容器 */
.table-container {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
}

.agent-table {
  border-radius: 8px;
  overflow: hidden;
}

.agent-table :deep(.el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

.agent-table :deep(.el-table__header th) {
  border-bottom: 2px solid #e4e7ed;
  font-size: 14px;
  padding: 16px 0;
}

.agent-table :deep(.el-table__body td) {
  padding: 14px 0;
}

.agent-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}

.agent-table :deep(.el-table__row) {
  transition: background-color 0.25s ease;
}

/* 表格内容样式 */
.agent-id {
  color: #909399;
  font-weight: 600;
  font-size: 13px;
}

.table-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-size: 24px;
  font-weight: 600;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.name-text {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.description-text {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.stats-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #909399;
}

.stats-cell span {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  padding: 4px 8px;
  font-size: 13px;
}

.action-buttons .el-button:hover {
  transform: scale(1.05);
}

.action-buttons .el-divider--vertical {
  height: 16px;
  margin: 0 4px;
}

/* 分页 */
.pagination-container {
  margin-top: 20px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: center;
}

.pagination-container :deep(.el-pagination) {
  justify-content: center;
}

/* 详情对话框样式 */
.agent-detail {
  padding: 24px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 2px solid #e4e7ed;
}

.detail-header .el-avatar {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.header-info h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 26px;
  font-weight: 600;
}

.header-info p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.prompt-text {
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.8;
  font-size: 14px;
  color: #606266;
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
}

.detail-actions {
  margin-top: 32px;
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.form-tip {
  margin-left: 12px;
  font-size: 13px;
  color: #909399;
}

/* 表单对话框优化 */
:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e4e7ed;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px 24px;
  border-top: 1px solid #e4e7ed;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-textarea__inner) {
  border-radius: 6px;
}

:deep(.el-input__inner) {
  border-radius: 6px;
}

/* 标签优化 */
:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
}

/* 头像优化 */
:deep(.el-avatar) {
  border: 2px solid white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
