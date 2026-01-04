<template>
  <div class="page-container">
    <div class="page-header">
      <h2 class="page-title">
        <el-icon><ChatDotRound /></el-icon>
        对话列表
      </h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建对话
      </el-button>
    </div>

    <!-- 状态过滤 -->
    <div class="filter-bar">
      <el-radio-group v-model="statusFilter" @change="fetchConversations">
        <el-radio-button label="active">进行中</el-radio-button>
        <el-radio-button label="archived">已归档</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 对话表格 -->
    <div class="table-container">
      <el-table
        v-loading="loading"
        :data="conversations"
        stripe
        style="width: 100%"
        class="conversation-table"
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
            <span v-if="row.last_message_at">{{ formatTime(row.last_message_at) }}</span>
            <span v-else class="no-message">暂无消息</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openConversation(row)">
              <el-icon><ChatDotRound /></el-icon>
              进入对话
            </el-button>
            <el-button type="info" size="small" @click="editConversation(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="archiveConversation(row)"
              v-if="row.status === 'active'"
            >
              <el-icon><FolderOpened /></el-icon>
              归档
            </el-button>
            <el-button type="danger" size="small" @click="deleteConversation(row)">
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
        :page-sizes="[20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchConversations"
        @current-change="fetchConversations"
      />
    </div>

    <!-- 创建对话对话框 -->
    <el-dialog v-model="dialogVisible" title="新建对话" width="600px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="对话标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入对话标题" maxlength="200" show-word-limit />
        </el-form-item>

        <el-form-item label="选择智能体" prop="agent_id">
          <el-select v-model="form.agent_id" placeholder="请选择智能体" clearable filterable>
            <el-option
              v-for="agent in availableAgents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            >
              <div style="display: flex; align-items: center; gap: 8px">
                <el-avatar :size="24" :src="agent.avatar">{{ agent.name.charAt(0) }}</el-avatar>
                <span>{{ agent.name }}</span>
              </div>
            </el-option>
          </el-select>
          <div class="form-tip">不选择则使用默认模型</div>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入对话描述（可选）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑对话" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="对话标题" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入对话标题" maxlength="200" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入对话描述"
            maxlength="1000"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { conversationApi, agentApi } from '../api/agent'
import { formatTime } from '../utils/time'

const router = useRouter()

// 数据状态
const loading = ref(false)
const conversations = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const statusFilter = ref('active')

// 可用的智能体列表
const availableAgents = ref([])

// 对话框状态
const dialogVisible = ref(false)
const editDialogVisible = ref(false)
const submitting = ref(false)

// 表单数据
const form = ref({
  title: '',
  agent_id: null,
  description: ''
})

const editForm = ref({
  title: '',
  description: ''
})

const formRef = ref(null)
const editFormRef = ref(null)
const currentConversation = ref(null)

// 验证规则
const rules = {
  title: [{ required: true, message: '请输入对话标题', trigger: 'blur' }]
}

const editRules = {
  title: [{ required: true, message: '请输入对话标题', trigger: 'blur' }]
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

    if (response.code === 200) {
      conversations.value = response.data.items
      total.value = response.data.total
    } else {
      ElMessage.error(response.message || '获取对话列表失败')
    }
  } catch (error) {
    console.error('获取对话列表失败:', error)
    ElMessage.error('获取对话列表失败')
  } finally {
    loading.value = false
  }
}

// 获取智能体列表
const fetchAgents = async () => {
  try {
    const response = await agentApi.getAgents({ page: 1, size: 100 })
    if (response.code === 200) {
      availableAgents.value = response.data.items
    }
  } catch (error) {
    console.error('获取智能体列表失败:', error)
  }
}

// 显示创建对话框
const showCreateDialog = async () => {
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
    await conversationApi.archiveConversation(conversation.id)
    ElMessage.success('归档成功')
    fetchConversations()
  } catch (error) {
    console.error('归档失败:', error)
    ElMessage.error('归档失败')
  }
}

// 编辑对话
const editConversation = (conversation) => {
  currentConversation.value = conversation
  editForm.value = {
    title: conversation.title,
    description: conversation.description || ''
  }
  editDialogVisible.value = true
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
      ElMessage.error('删除失败')
    }
  }
}

// 提交创建表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    submitting.value = true
    const response = await conversationApi.createConversation(form.value)

    if (response.code === 200) {
      ElMessage.success('创建成功')
      dialogVisible.value = false

      // 跳转到聊天界面
      router.push({
        name: 'Chat',
        query: { conversationId: response.data.id }
      })
    } else {
      ElMessage.error(response.message || '创建失败')
    }
  } catch (error) {
    console.error('创建失败:', error)
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

// 提交编辑表单
const handleEditSubmit = async () => {
  try {
    await editFormRef.value.validate()

    submitting.value = true
    const response = await conversationApi.updateConversation(currentConversation.value.id, editForm.value)

    if (response.code === 200) {
      ElMessage.success('保存成功')
      editDialogVisible.value = false
      fetchConversations()
    } else {
      ElMessage.error(response.message || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
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


onMounted(() => {
  fetchConversations()
})
</script>

<style scoped>
.filter-bar {
  margin-bottom: 24px;
}

.table-container {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
  margin-bottom: 24px;
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
}

.conversation-table :deep(.el-table__row:hover) {
  background-color: #f7fafc;
}

.conversation-id {
  color: #909399;
  font-weight: 600;
}

.agent-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-size: 18px;
  font-weight: 600;
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
}

.no-message {
  color: #c0c4cc;
  font-style: italic;
}

.pagination-container {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.form-tip {
  margin-top: 8px;
  font-size: 14px;
  color: #909399;
}
</style>
