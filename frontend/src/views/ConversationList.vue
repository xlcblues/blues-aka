<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">💬 对话管理</h1>
      <div class="header-actions">
        <el-button type="success" @click="showCreateDialog" class="create-btn">
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选区域 -->
    <div class="search-section">
      <div class="search-header">🎵 对话筛选</div>
      <el-form :model="searchForm" inline>
        <el-form-item label="状态">
          <el-radio-group v-model="statusFilter" @change="fetchConversations">
            <el-radio-button label="active">进行中</el-radio-button>
            <el-radio-button label="archived">已归档</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </div>

    <!-- 对话列表表格 -->
    <div class="table-container">
      <div class="table-header">
        <span>🎸 对话列表</span>
        <div class="table-actions">
          <el-tooltip content="刷新数据 (F5)" placement="top">
            <el-button circle @click="fetchConversations" :loading="loading" class="refresh-btn">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
      <el-table
        v-loading="loading"
        :data="conversations"
        stripe
        style="width: 100%"
        class="conversation-table"
        :empty-text="getEmptyText()"
      >
        <el-table-column prop="id" label="#" width="80" align="center">
          <template #default="{ row }">
            <span class="conversation-id">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column label="智能体" width="200">
          <template #default="{ row }">
            <div class="agent-cell" v-if="row.agent">
              <el-avatar :size="40" :src="row.agent.avatar" class="table-avatar">
                {{ row.agent.name.charAt(0) }}
              </el-avatar>
              <span class="agent-name">{{ row.agent.name }}</span>
            </div>
            <span v-else class="no-agent">默认模型</span>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="对话标题" min-width="250">
          <template #default="{ row }">
            <span class="title-text">{{ row.title }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="300">
          <template #default="{ row }">
            <span class="description-text">{{ row.description || '暂无描述' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="消息统计" width="150" align="center">
          <template #default="{ row }">
            <div class="stats-cell">
              <el-icon><ChatLineRound /></el-icon>
              <span>{{ row.message_count || 0 }} 条</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="last_message_at" label="最后消息" width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <span class="time-icon">{{ row.last_message_at ? '🎸' : '😴' }}</span>
              <span v-if="row.last_message_at">{{ formatTime(row.last_message_at) }}</span>
              <span v-else class="no-message">暂无消息</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            <div class="time-cell">
              <span class="time-icon">🕐</span>
              {{ formatTime(row.created_at) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openConversation(row)" class="chat-btn">
              <el-icon><ChatDotRound /></el-icon>
              进入对话
            </el-button>
            <el-button type="info" size="small" @click="editConversation(row)" class="edit-btn">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="archiveConversation(row)"
              v-if="row.status === 'active'"
              class="archive-btn"
            >
              <el-icon><FolderOpened /></el-icon>
              归档
            </el-button>
            <el-button type="danger" size="small" @click="deleteConversation(row)" class="delete-btn">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
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
        @size-change="fetchConversations"
        @current-change="fetchConversations"
        background
      />
    </div>

    <!-- 创建对话对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑对话' : '新建对话'"
      width="700px"
      @close="resetForm"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="对话标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请输入对话标题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="选择智能体" prop="agent_id">
          <el-select
            v-model="form.agent_id"
            placeholder="请选择智能体（可选）"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="agent in availableAgents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            >
              <div style="display: flex; align-items: center; gap: 12px">
                <el-avatar :size="40" :src="agent.avatar">{{ agent.name.charAt(0) }}</el-avatar>
                <div style="flex: 1">
                  <div style="font-weight: 600; font-size: 15px">{{ agent.name }}</div>
                  <div style="font-size: 13px; color: #909399">{{ agent.description || '暂无描述' }}</div>
                </div>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">不选择智能体则使用默认模型</div>
        </el-form-item>

        <el-form-item label="对话描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            placeholder="请输入对话描述（可选）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { conversationApi, agentApi } from '../api/agent'
import { formatTime } from '../utils/time'
import { getErrorMessage } from '../utils/errorHandler'

const router = useRouter()

// 数据状态
const loading = ref(false)
const conversations = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const statusFilter = ref('active')

// 可用的智能体列表
const availableAgents = ref([])

// 对话框状态
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)

// 搜索表单
const searchForm = reactive({
  keyword: ''
})

// 表单数据
const form = ref({
  title: '',
  agent_id: null,
  description: ''
})

const formRef = ref(null)
const currentConversation = ref(null)

// 验证规则
const rules = {
  title: [
    { required: true, message: '请输入对话标题', trigger: 'blur' },
    { min: 2, max: 200, message: '标题长度在 2 到 200 个字符', trigger: 'blur' }
  ]
}

// 获取对话列表
const fetchConversations = async () => {
  try {
    loading.value = true
    const response = await conversationApi.getConversations({
      page: currentPage.value,
      size: pageSize.value,
      status: statusFilter.value
    })

    if (response.code === 200 || response.status === 'success') {
      conversations.value = response.data.items || []
      total.value = response.data.total || 0
    } else {
      ElMessage.error(response.message || '获取对话列表失败')
    }
  } catch (error) {
    console.error('获取对话列表失败:', error)
    ElMessage.error(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

// 获取智能体列表
const fetchAgents = async () => {
  try {
    const response = await agentApi.getAgents({ page: 1, size: 100 })
    if (response.code === 200 || response.status === 'success') {
      availableAgents.value = response.data.items || []
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
  }
}

// 显示创建对话框
const showCreateDialog = async () => {
  isEdit.value = false
  await fetchAgents()
  dialogVisible.value = true
}

// 打开对话
const openConversation = (conversation) => {
  router.push({
    name: 'Chat',
    query: { conversationId: conversation.id }
  })
}

// 归档对话
const archiveConversation = async (conversation) => {
  try {
    await ElMessageBox.confirm(
      `确定要归档对话 "${conversation.title}" 吗？`,
      '确认归档',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    await conversationApi.archiveConversation(conversation.id)
    ElMessage.success('归档成功')
    fetchConversations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('归档失败:', error)
      ElMessage.error(getErrorMessage(error))
    }
  }
}

// 编辑对话
const editConversation = (conversation) => {
  isEdit.value = true
  currentConversation.value = conversation
  form.value = {
    title: conversation.title,
    agent_id: conversation.agent_id,
    description: conversation.description || ''
  }
  dialogVisible.value = true
}

// 删除对话
const deleteConversation = async (conversation) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除对话 "${conversation.title}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await conversationApi.deleteConversation(conversation.id)
    ElMessage.success('删除成功')
    fetchConversations()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(getErrorMessage(error))
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
      response = await conversationApi.updateConversation(currentConversation.value.id, {
        title: form.value.title,
        description: form.value.description
      })
    } else {
      response = await conversationApi.createConversation(form.value)
    }

    if (response.code === 200 || response.status === 'success') {
      ElMessage.success(isEdit.value ? '保存成功' : '创建成功')
      dialogVisible.value = false

      if (!isEdit.value) {
        // 跳转到聊天界面
        const conversationId = response.data.id
        router.push({
          name: 'Chat',
          query: { conversationId }
        })
      } else {
        fetchConversations()
      }
    } else {
      ElMessage.error(response.message || '操作失败')
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error(getErrorMessage(error))
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  form.value = {
    title: '',
    agent_id: null,
    description: ''
  }
  formRef.value?.resetFields()
}

// 获取空状态文本
const getEmptyText = () => {
  if (statusFilter.value === 'archived') {
    return '暂无归档对话 💾'
  }
  return '暂无对话 🎵'
}

onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.page-container {
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  position: relative;
}

.page-header::before {
  content: '💬';
  position: absolute;
  top: 8px;
  right: 15px;
  font-size: 24px;
  opacity: 0.3;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: white;
  margin: 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.create-btn {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 600;
  background: white;
  color: #667eea;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-section {
  margin-bottom: 24px;
  padding: 24px;
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 30%, #90cdf4 60%, #63b3ed 100%);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(66, 153, 225, 0.15);
  position: relative;
}

.search-section::before {
  content: '🎵';
  position: absolute;
  top: 8px;
  right: 15px;
  font-size: 16px;
  opacity: 0.5;
}

.search-section::after {
  content: '提示: 选择状态筛选对话';
  position: absolute;
  bottom: 8px;
  right: 15px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.search-header {
  font-size: 18px;
  font-weight: 700;
  color: #2c5282;
  margin-bottom: 16px;
}

.search-section :deep(.el-form-item__label) {
  font-weight: 600;
  color: #2c5282;
}

.search-section :deep(.el-radio-button__inner) {
  font-weight: 600;
}

.table-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  position: relative;
  margin-bottom: 24px;
}

.table-container::before {
  content: '🎸';
  position: absolute;
  top: 10px;
  right: 15px;
  font-size: 20px;
  opacity: 0.5;
}

.table-container::after {
  content: '💬';
  position: absolute;
  top: 10px;
  right: 45px;
  font-size: 16px;
  opacity: 0.5;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 700;
  color: #2d3748;
}

.table-actions {
  display: flex;
  gap: 8px;
}

.conversation-table {
  border-radius: 12px;
  overflow: hidden;
}

.conversation-table :deep(.el-table__header) {
  background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
}

.conversation-table :deep(.el-table__header th) {
  background: transparent;
  border-bottom: 2px solid #4299e1;
  font-weight: 600;
  color: #2d3748;
  font-size: 15px;
  padding: 16px 0;
}

.conversation-table :deep(.el-table__row:hover) {
  background-color: #f7fafc;
}

.conversation-table :deep(.el-table__row td) {
  padding: 16px 0;
}

.conversation-id {
  color: #909399;
  font-weight: 600;
}

.agent-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-size: 18px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.agent-name {
  font-size: 15px;
  color: #303133;
  font-weight: 500;
}

.no-agent {
  color: #909399;
  font-style: italic;
}

.title-text {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.description-text {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.stats-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.time-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.time-icon {
  font-size: 16px;
}

.no-message {
  color: #c0c4cc;
  font-style: italic;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.form-tip {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}

.page-container:hover,
.table-container:hover,
.search-section:hover {
  box-shadow: 0 12px 40px rgba(49, 130, 206, 0.25);
}

/* 按钮样式 */
.chat-btn {
  background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(66, 153, 225, 0.4);
}

.edit-btn {
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
}

.edit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(72, 187, 120, 0.4);
}

.archive-btn {
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(237, 137, 54, 0.3);
}

.archive-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(237, 137, 54, 0.4);
}

.delete-btn {
  background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(245, 101, 101, 0.3);
}

.delete-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(245, 101, 101, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 20px;
  }

  .page-title {
    font-size: 24px;
  }

  .search-section {
    padding: 20px;
  }

  .search-section :deep(.el-form--inline) .el-form-item {
    display: block;
    margin-bottom: 16px;
  }

  .search-header {
    font-size: 16px;
  }

  .table-container {
    padding: 16px;
    overflow-x: auto;
  }

  .conversation-table {
    min-width: 800px;
  }
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .page-container {
    border: 2px solid #2d3748;
  }

  .table-container {
    border: 2px solid #2d3748;
  }

  .search-section {
    border: 2px solid #2d3748;
  }
}
</style>
