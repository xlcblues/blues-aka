<template>
  <div class="chat-container">
    <!-- 对话信息头部 -->
    <div class="chat-header">
      <div class="header-left">
        <el-button circle @click="backToList">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <div class="conversation-info" v-if="conversation">
          <h3>{{ conversation.title }}</h3>
          <p v-if="conversation.agent">
            <el-icon><Avatar /></el-icon>
            {{ conversation.agent.name }}
          </p>
        </div>
      </div>
      <div class="header-right">
        <el-button @click="showNewConversationDialog">
          <el-icon><Plus /></el-icon>
          新建对话
        </el-button>
        <el-dropdown trigger="click">
          <el-button circle>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="exportChat">
                <el-icon><Download /></el-icon>
                导出对话
              </el-dropdown-item>
              <el-dropdown-item @click="clearChat" divided>
                <el-icon><Delete /></el-icon>
                清空对话
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 聊天消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="messages.length === 0" class="empty-chat">
        <el-empty description="开始新的对话吧！">
          <template #image>
            <div class="empty-icon">💬</div>
          </template>
        </el-empty>
      </div>

      <div v-else class="messages-wrapper">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message-item', message.role]"
        >
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="user-message">
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.created_at) }}</div>
            </div>
            <el-avatar :size="40">{{ username?.charAt(0) || 'U' }}</el-avatar>
          </div>

          <!-- AI消息 -->
          <div v-else class="assistant-message">
            <el-avatar :size="40" :src="conversation?.agent?.avatar">
              {{ conversation?.agent?.name?.charAt(0) || 'AI' }}
            </el-avatar>
            <div class="message-content">
              <div class="message-text markdown-content" v-html="renderMarkdown(message.content)"></div>
              <div class="message-meta">
                <span class="message-time">{{ formatTime(message.created_at) }}</span>
                <span v-if="message.tokens" class="message-tokens">
                  <el-icon><Document /></el-icon>
                  {{ message.tokens }} tokens
                </span>
              </div>
              <div class="message-actions">
                <el-button-group>
                  <el-button size="small" @click="copyMessage(message.content)">
                    <el-icon><CopyDocument /></el-icon>
                    复制
                  </el-button>
                  <el-button size="small" @click="regenerateMessage(message)">
                    <el-icon><RefreshRight /></el-icon>
                    重新生成
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small">
                      <el-icon><Star /></el-icon>
                      评分
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="rateMessage(message, 5)">⭐⭐⭐⭐⭐</el-dropdown-item>
                        <el-dropdown-item @click="rateMessage(message, 4)">⭐⭐⭐⭐</el-dropdown-item>
                        <el-dropdown-item @click="rateMessage(message, 3)">⭐⭐⭐</el-dropdown-item>
                        <el-dropdown-item @click="rateMessage(message, 2)">⭐⭐</el-dropdown-item>
                        <el-dropdown-item @click="rateMessage(message, 1)">⭐</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </el-button-group>
              </div>
            </div>
          </div>
        </div>

        <!-- 正在输入的AI消息 -->
        <div v-if="isStreaming" class="message-item assistant">
          <el-avatar :size="40" :src="conversation?.agent?.avatar">
            {{ conversation?.agent?.name?.charAt(0) || 'AI' }}
          </el-avatar>
          <div class="message-content streaming">
            <div class="message-text markdown-content">{{ streamingContent }}</div>
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-container">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="inputRows"
          placeholder="输入消息... (Shift + Enter 换行，Enter 发送)"
          @keydown="handleKeydown"
          :disabled="isStreaming"
          resize="none"
          maxlength="10000"
          show-word-limit
        />
        <div class="input-actions">
          <div class="input-actions-left">
            <el-button-group>
              <el-tooltip content="清空输入">
                <el-button circle @click="inputMessage = ''">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
          </div>
          <div class="input-actions-right">
            <el-button
              type="primary"
              @click="sendMessage"
              :loading="isStreaming"
              :disabled="!inputMessage.trim()"
            >
              <el-icon v-if="!isStreaming"><Promotion /></el-icon>
              {{ isStreaming ? '发送中...' : '发送' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建对话对话框 -->
    <el-dialog v-model="newChatDialogVisible" title="新建对话" width="600px">
      <el-form :model="newChatForm" :rules="newChatRules" ref="newChatFormRef" label-width="100px">
        <el-form-item label="对话标题" prop="title">
          <el-input v-model="newChatForm.title" placeholder="请输入对话标题" />
        </el-form-item>
        <el-form-item label="选择智能体" prop="agent_id">
          <el-select v-model="newChatForm.agent_id" placeholder="请选择智能体" clearable>
            <el-option
              v-for="agent in availableAgents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="newChatDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createNewChat">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { chatApi, conversationApi, agentApi } from '../api/agent'
import { renderMarkdown } from '../utils/markdown'
import { formatTime } from '../utils/time'

const router = useRouter()
const route = useRoute()

// 数据状态
const loading = ref(false)
const messages = ref([])
const conversation = ref(null)
const conversationId = ref(null)
const isStreaming = ref(false)
const streamingContent = ref('')

// 输入相关
const inputMessage = ref('')
const inputRows = ref(1)

// 对话框
const newChatDialogVisible = ref(false)
const availableAgents = ref([])
const newChatForm = ref({
  title: '',
  agent_id: null
})
const newChatFormRef = ref(null)
const newChatRules = {
  title: [{ required: true, message: '请输入对话标题', trigger: 'blur' }]
}

// 用户信息
const username = computed(() => localStorage.getItem('username'))

// 引用
const messagesContainer = ref(null)

// 获取对话详情
const fetchConversation = async () => {
  if (!conversationId.value) return

  try {
    const response = await conversationApi.getConversation(conversationId.value)
    if (response.code === 200) {
      conversation.value = response.data
    }
  } catch (error) {
    console.error('获取对话详情失败:', error)
  }
}

// 获取消息历史
const fetchMessages = async () => {
  if (!conversationId.value) return

  try {
    loading.value = true
    const response = await chatApi.getMessages(conversationId.value, { page: 1, size: 100 })

    if (response.code === 200) {
      messages.value = response.data.items
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('获取消息历史失败:', error)
    ElMessage.error('获取消息历史失败')
  } finally {
    loading.value = false
  }
}

// 发送消息
const sendMessage = async (useStream = true) => {
  if (!inputMessage.value.trim() || isStreaming.value) return

  const content = inputMessage.value.trim()
  inputMessage.value = ''
  inputRows.value = 1

  // 如果没有对话ID，先创建对话
  if (!conversationId.value) {
    await createConversationFirst(content)
    return
  }

  if (useStream) {
    await sendMessageStream(content)
  } else {
    await sendMessageNormal(content)
  }
}

// 流式发送消息
const sendMessageStream = async (content) => {
  try {
    isStreaming.value = true
    streamingContent.value = ''

    const token = localStorage.getItem('access_token')

    const response = await fetch(`/conversations/${conversationId.value}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content, stream: true })
    })

    if (!response.ok) {
      throw new Error('发送消息失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'start') {
              // 开始流式响应
            } else if (data.type === 'token') {
              streamingContent.value += data.content
              await nextTick()
              scrollToBottom()
            } else if (data.type === 'end') {
              // 结束流式响应，添加到消息列表
              messages.value.push({
                id: data.message_id,
                role: 'assistant',
                content: streamingContent.value,
                created_at: new Date().toISOString()
              })
              streamingContent.value = ''
            } else if (data.type === 'error') {
              ElMessage.error(data.message || '发送消息失败')
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    // 刷新消息列表
    await fetchMessages()
    await fetchConversation()

  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
    streamingContent.value = ''
  } finally {
    isStreaming.value = false
  }
}

// 普通发送消息
const sendMessageNormal = async (content) => {
  try {
    isStreaming.value = true

    const response = await chatApi.chat(conversationId.value, {
      content,
      stream: false
    })

    if (response.code === 200) {
      // 添加AI回复到消息列表
      messages.value.push(response.data.message)
      await nextTick()
      scrollToBottom()

      // 更新对话信息
      conversation.value = response.data.conversation
    } else {
      ElMessage.error(response.message || '发送消息失败')
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
  } finally {
    isStreaming.value = false
  }
}

// 先创建对话再发送消息
const createConversationFirst = async (content) => {
  try {
    const agentId = route.query.agentId
    const response = await conversationApi.createConversation({
      title: `对话 - ${new Date().toLocaleString()}`,
      agent_id: agentId || null
    })

    if (response.code === 200) {
      conversationId.value = response.data.id
      conversation.value = response.data
      await sendMessage()
    }
  } catch (error) {
    console.error('创建对话失败:', error)
    ElMessage.error('创建对话失败')
  }
}

// 重新生成消息
const regenerateMessage = async (message) => {
  if (!conversationId.value) return

  try {
    isStreaming.value = true
    streamingContent.value = ''

    // 删除该消息后的所有消息
    const messageIndex = messages.value.findIndex(m => m.id === message.id)
    if (messageIndex !== -1) {
      messages.value = messages.value.slice(0, messageIndex)
    }

    const token = localStorage.getItem('access_token')

    const response = await fetch(`/conversations/${conversationId.value}/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ stream: true })
    })

    if (!response.ok) {
      throw new Error('重新生成失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'token') {
              streamingContent.value += data.content
              await nextTick()
              scrollToBottom()
            } else if (data.type === 'end') {
              messages.value.push({
                id: data.message_id,
                role: 'assistant',
                content: streamingContent.value,
                created_at: new Date().toISOString()
              })
              streamingContent.value = ''
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    await fetchMessages()

  } catch (error) {
    console.error('重新生成失败:', error)
    ElMessage.error('重新生成失败')
  } finally {
    isStreaming.value = false
  }
}

// 复制消息
const copyMessage = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 给消息评分
const rateMessage = async (message, rating) => {
  try {
    await chatApi.messageFeedback(message.id, { rating })
    ElMessage.success('评分成功')
  } catch (error) {
    console.error('评分失败:', error)
    ElMessage.error('评分失败')
  }
}

// 导出对话
const exportChat = () => {
  const content = messages.value
    .map(m => `${m.role === 'user' ? '用户' : 'AI'}: ${m.content}`)
    .join('\n\n')

  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `对话-${conversation.value?.title || new Date().toLocaleString()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// 清空对话
const clearChat = async () => {
  try {
    await ElMessageBox.confirm('确定要清空当前对话吗？', '确认', {
      type: 'warning'
    })

    messages.value = []
    ElMessage.success('已清空')
  } catch (error) {
    // 取消
  }
}

// 新建对话
const showNewConversationDialog = async () => {
  await fetchAgents()
  newChatDialogVisible.value = true
}

const createNewChat = async () => {
  try {
    await newChatFormRef.value.validate()

    const response = await conversationApi.createConversation({
      title: newChatForm.value.title,
      agent_id: newChatForm.value.agent_id
    })

    if (response.code === 200) {
      ElMessage.success('创建成功')
      newChatDialogVisible.value = false

      // 跳转到新对话
      conversationId.value = response.data.id
      messages.value = []
      await fetchConversation()
    }
  } catch (error) {
    console.error('创建失败:', error)
    ElMessage.error('创建失败')
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

// 返回列表
const backToList = () => {
  router.push({ name: 'ConversationList' })
}

// 处理键盘事件
const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 监听输入框内容变化，动态调整行数
watch(inputMessage, (newValue) => {
  const lines = newValue.split('\n').length
  inputRows.value = Math.min(Math.max(lines, 1), 5)
})

// 初始化
onMounted(async () => {
  conversationId.value = route.query.conversationId || null

  if (conversationId.value) {
    await fetchConversation()
    await fetchMessages()
  } else if (route.query.agentId) {
    // 如果有智能体ID，显示智能体信息
    ElMessage.info('开始新对话')
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  background: #f5f7fa;
  border-radius: 16px;
  overflow: hidden;
  max-width: 1600px;
  margin: 0 auto;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: white;
  border-bottom: 1px solid #ebeef5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.conversation-info h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.conversation-info p {
  margin: 0;
  font-size: 15px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  gap: 16px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}

.loading-container,
.empty-chat {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.empty-icon {
  font-size: 100px;
}

.messages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 1400px;
  margin: 0 auto;
}

.message-item {
  display: flex;
  gap: 20px;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-item.user {
  flex-direction: row-reverse;
}

.user-message {
  display: flex;
  gap: 20px;
  max-width: 80%;
  flex-direction: row-reverse;
  margin-left: auto;
}

.user-message .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 18px 18px 6px 18px;
  padding: 20px 28px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.25);
}

.user-message .message-text {
  color: white;
  word-break: break-word;
  white-space: pre-wrap;
  font-size: 16px;
  line-height: 1.7;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  margin-top: 10px;
}

.assistant-message {
  display: flex;
  gap: 20px;
  max-width: 85%;
}

.assistant-message .message-content {
  background: white;
  border-radius: 18px 18px 18px 6px;
  padding: 20px 28px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.assistant-message .message-text {
  color: #303133;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 16px;
}

.assistant-message .message-meta {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  font-size: 13px;
  color: #909399;
}

.assistant-message .message-actions {
  margin-top: 16px;
}

.streaming {
  position: relative;
}

.typing-indicator {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.typing-indicator span {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #409eff;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.7;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.markdown-content {
  line-height: 1.8;
}

.markdown-content :deep(pre) {
  background: #f5f7fa;
  padding: 18px;
  border-radius: 10px;
  overflow-x: auto;
  margin: 16px 0;
  font-size: 15px;
}

.markdown-content :deep(code) {
  background: #f5f7fa;
  padding: 4px 10px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 0.95em;
}

.markdown-content :deep(p) {
  margin: 12px 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin: 20px 0 12px 0;
  font-weight: 600;
}

.chat-input-container {
  background: white;
  padding: 28px 32px;
  border-top: 1px solid #ebeef5;
}

.input-wrapper {
  max-width: 100%;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.input-actions-left,
.input-actions-right {
  display: flex;
  gap: 12px;
}
</style>
