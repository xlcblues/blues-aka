<template>
  <div class="page-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon class="title-icon"><ChatLineRound /></el-icon>
          对话管理
        </h2>
      </div>
      <div class="header-right">
        <el-radio-group v-model="statusFilter" @change="fetchConversations" class="status-selector" size="default">
          <el-radio-button label="active">
            <el-icon><ChatDotRound /></el-icon>
            <span>进行中</span>
          </el-radio-button>
          <el-radio-button label="archived">
            <el-icon><FolderOpened /></el-icon>
            <span>已归档</span>
          </el-radio-button>
        </el-radio-group>
        <el-button type="primary" size="default" @click="showCreateDialog" class="create-btn">
          <el-icon><Plus /></el-icon>
          <span>新建对话</span>
        </el-button>
      </div>
    </div>

    <!-- 对话列表表格 -->
    <div class="table-container">
      <el-table
        v-loading="loading"
        :data="conversations"
        stripe
        style="width: 100%"
        class="conversation-table"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
        :empty-text="getEmptyText()"
        :row-class-name="getRowClassName"
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
            <span class="title-text" :class="{ 'archived-text': row.status === 'archived' }">{{ row.title }}</span>
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

        <el-table-column label="操作" width="350" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                type="primary"
                size="small"
                @click="openConversation(row)"
                link
                :disabled="row.status === 'archived'"
              >
                <el-icon><ChatDotRound /></el-icon>
                {{ row.status === 'archived' ? '已归档' : '进入对话' }}
              </el-button>
              <el-divider direction="vertical" />
              <el-button type="primary" size="small" @click="editConversation(row)" link>
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-divider direction="vertical" />
              <el-button
                type="warning"
                size="small"
                @click="toggleArchive(row)"
                link
              >
                <el-icon><FolderOpened /></el-icon>
                {{ row.status === 'active' ? '归档' : '取消归档' }}
              </el-button>
              <el-divider direction="vertical" />
              <el-button type="danger" size="small" @click="deleteConversation(row)" link>
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
            popper-class="agent-select-dropdown"
            style="width: 100%"
          >
            <el-option
              v-for="agent in availableAgents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            >
              <div class="agent-option">
                <el-avatar :size="40" :src="agent.avatar">{{ agent.name.charAt(0) }}</el-avatar>
                <div class="agent-option-info">
                  <div class="agent-option-name">{{ agent.name }}</div>
                  <div class="agent-option-desc">{{ agent.description || '暂无描述' }}</div>
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
  // 如果对话已归档，提示用户先取消归档
  if (conversation.status === 'archived') {
    ElMessage({
      message: '🚫 该对话已归档，请先取消归档后再进行对话',
      type: 'warning',
      duration: 3000,
      showClose: true
    })
    return
  }

  router.push({
    name: 'Chat',
    query: { conversationId: conversation.id }
  })
}

// 切换对话归档状态
const toggleArchive = async (conversation) => {
  const isArchiving = conversation.status === 'active'

  try {
    await ElMessageBox.confirm(
      isArchiving
        ? `📦 确定要归档对话 "${conversation.title}" 吗？\n\n⚠️ 归档后将不会出现在"进行中"列表中，但可以随时恢复。`
        : `✨ 确定要取消归档对话 "${conversation.title}" 吗？\n\n📌 取消归档后，该对话将重新出现在"进行中"列表中。`,
      isArchiving ? '归档对话确认' : '取消归档对话确认',
      {
        confirmButtonText: isArchiving ? '📦 确认归档' : '✅ 确认恢复',
        cancelButtonText: '❌ 取消操作',
        type: isArchiving ? 'warning' : 'success',
        dangerouslyUseHTMLString: false,
        center: true
      }
    )

    await conversationApi.archiveConversation(conversation.id)
    ElMessage({
      message: isArchiving
        ? `📦 对话 "${conversation.title}" 归档成功！`
        : `✅ 对话 "${conversation.title}" 已恢复到"进行中"列表！`,
      type: 'success',
      duration: 3000,
      showClose: true
    })
    fetchConversations()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      ElMessage({
        message: '🚫 操作已取消',
        type: 'info',
        duration: 2000
      })
    } else {
      console.error('操作失败:', error)
      ElMessage({
        message: `❌ 操作失败: ${error.backendMessage || error.message || '未知错误'}`,
        type: 'error',
        duration: 5000,
        showClose: true
      })
    }
  }
}

// 编辑对话
const editConversation = async (conversation) => {
  isEdit.value = true
  currentConversation.value = conversation
  await fetchAgents()
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
      `🚨 确定要删除对话 "${conversation.title}" 吗？\n\n⚠️ 此操作不可恢复，请谨慎操作！`,
      '删除对话确认',
      {
        confirmButtonText: '🗑️ 确认删除',
        cancelButtonText: '❌ 取消操作',
        type: 'error',
        dangerouslyUseHTMLString: false,
        center: true
      }
    )

    await conversationApi.deleteConversation(conversation.id)
    ElMessage({
      message: `🗑️ 对话 "${conversation.title}" 删除成功！`,
      type: 'success',
      duration: 3000,
      showClose: true
    })
    fetchConversations()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      ElMessage({
        message: '🚫 删除操作已取消',
        type: 'info',
        duration: 2000
      })
    } else {
      console.error('删除失败:', error)
      ElMessage({
        message: `❌ 删除失败: ${error.backendMessage || error.message || '未知错误'}`,
        type: 'error',
        duration: 5000,
        showClose: true
      })
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
        agent_id: form.value.agent_id,
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

// 获取行的类名
const getRowClassName = ({ row }) => {
  return row.status === 'archived' ? 'archived-row' : ''
}

onMounted(() => {
  fetchConversations()
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

/* 状态选择器 */
.status-selector {
  display: flex;
  align-items: center;
}

.status-selector :deep(.el-radio-button__inner) {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.status-selector :deep(.el-radio-button__inner:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(64, 158, 255, 0.2);
}

.status-selector :deep(.el-icon) {
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

.conversation-table {
  border-radius: 8px;
  overflow: hidden;
}

.conversation-table :deep(.el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

.conversation-table :deep(.el-table__header th) {
  border-bottom: 2px solid #e4e7ed;
  font-size: 14px;
  padding: 16px 0;
}

.conversation-table :deep(.el-table__body td) {
  padding: 14px 0;
}

.conversation-table :deep(.el-table__row:hover) {
  background-color: #f5f7fa !important;
}

.conversation-table :deep(.el-table__row) {
  transition: background-color 0.25s ease;
}

/* 已归档对话行样式 */
.conversation-table :deep(.el-table__row.archived-row) {
  background-color: #fafafa;
  opacity: 0.7;
}

.conversation-table :deep(.el-table__row.archived-row:hover) {
  background-color: #f0f0f0 !important;
}

/* 表格内容样式 */
.conversation-id {
  color: #909399;
  font-weight: 600;
  font-size: 13px;
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
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
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
  font-size: 15px;
  color: #303133;
}

.archived-text {
  color: #909399;
  font-style: italic;
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
  font-size: 13px;
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

.action-buttons .el-button:hover:not(.is-disabled) {
  transform: scale(1.05);
}

.action-buttons .el-button.is-disabled {
  cursor: not-allowed;
  opacity: 0.6;
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

/* 表单对话框样式 */
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

/* 下拉选择器中的头像样式修复 */
:deep(.el-select-dropdown) {
  border: none !important;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1) !important;
}

:deep(.el-select-dropdown__wrap) {
  max-height: 274px !important;
  overflow: auto !important;
}

:deep(.el-select-dropdown__list) {
  padding: 4px 0 !important;
}

:deep(.el-select-dropdown__item) {
  padding: 12px 16px !important;
  height: auto !important;
  min-height: 64px !important;
  line-height: normal !important;
  display: flex !important;
  align-items: center !important;
  box-sizing: border-box !important;
}

:deep(.el-select-dropdown__item.selected) {
  background-color: #ecf5ff;
}

:deep(.el-select-dropdown__item .el-avatar) {
  flex-shrink: 0 !important;
  border: none !important;
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3) !important;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: #f5f7fa;
}

/* 智能体选项样式 */
.agent-option {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  line-height: 1.5;
}

.agent-option :deep(.el-avatar) {
  flex-shrink: 0;
  width: 40px !important;
  height: 40px !important;
  line-height: 40px !important;
}

.agent-option-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.agent-option-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  line-height: 1.5;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-option-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
  max-height: 36px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  text-overflow: ellipsis;
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
    font-size: 20px;
  }

  .table-container {
    padding: 16px;
    overflow-x: auto;
  }

  .conversation-table {
    min-width: 800px;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .status-selector {
    flex: 1;
  }

  .status-selector :deep(.el-radio-button__inner) {
    padding: 10px 14px;
    font-size: 13px;
  }

  .create-btn {
    padding: 10px 16px;
  }
}
</style>

<!-- 全局样式：修复智能体下拉框显示问题 -->
<style>
.agent-select-dropdown {
  max-height: none !important;
}

.agent-select-dropdown .el-select-dropdown__wrap {
  max-height: 300px !important;
  overflow-y: auto !important;
}

.agent-select-dropdown .el-select-dropdown__list {
  padding: 6px 0 !important;
}

.agent-select-dropdown .el-select-dropdown__item {
  height: auto !important;
  min-height: 65px !important;
  padding: 12px 16px !important;
  line-height: normal !important;
  display: flex !important;
  align-items: center !important;
}

.agent-select-dropdown .el-select-dropdown__item.is-selected {
  background-color: #ecf5ff !important;
}

.agent-select-dropdown .el-select-dropdown__item:hover {
  background-color: #f5f7fa !important;
}

.agent-select-dropdown .el-select-dropdown__item .el-avatar {
  flex-shrink: 0 !important;
  width: 40px !important;
  height: 40px !important;
  line-height: 40px !important;
  font-size: 18px !important;
  border: none !important;
}
</style>
