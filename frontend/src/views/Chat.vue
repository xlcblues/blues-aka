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
            <div class="user-message-content">{{ message.content }}</div>
          </div>

          <!-- AI消息 -->
          <div v-else class="assistant-message">
            <!-- 推理过程显示(已保存的消息) -->
            <div v-if="message.reasoning && message.reasoning.content" class="reasoning-container">
              <div class="reasoning-header">
                <el-icon class="reasoning-icon"><MagicStick /></el-icon>
                <span class="reasoning-title">深度思考过程</span>
                <el-tag size="small" type="success">已完成</el-tag>
              </div>
              <div class="reasoning-content markdown-content" v-html="renderMarkdown(message.reasoning.content)"></div>
            </div>

            <div class="assistant-message-text markdown-content" v-html="renderMarkdown(message.content)"></div>
            <div class="message-actions">
              <el-button text size="small" @click="copyMessage(message.content)">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
              <el-button text size="small" @click="regenerateMessage(message)">
                <el-icon><RefreshRight /></el-icon>
                重新生成
              </el-button>
              <el-dropdown trigger="click" v-if="!message.rating">
                <el-button text size="small">
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
              <el-button text size="small" v-else disabled class="rated-btn">
                <el-icon><Star /></el-icon>
                {{ message.rating }}⭐
              </el-button>
            </div>
          </div>
        </div>

        <!-- 正在输入的AI消息 -->
        <div v-if="isStreaming && (streamingContent || streamingReasoning)" class="message-item assistant streaming-message">
          <!-- 推理过程显示 -->
          <div v-if="streamingReasoning" class="reasoning-container">
            <div class="reasoning-header">
              <el-icon class="reasoning-icon"><MagicStick /></el-icon>
              <span class="reasoning-title">深度思考过程</span>
              <el-tag size="small" type="warning">推理中</el-tag>
            </div>
            <div class="reasoning-content markdown-content" v-html="renderMarkdown(streamingReasoning)"></div>
          </div>

          <!-- 最终内容显示 -->
          <div class="assistant-message-text markdown-content streaming-text" v-html="renderMarkdown(streamingContent)"></div>
          <div class="message-actions streaming-actions">
            <el-button text size="small" @click="copyStreamingContent" :disabled="!streamingContent">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
            <el-button text size="small" @click="stopStreaming">
              <el-icon><CircleClose /></el-icon>
              停止生成
            </el-button>
          </div>
        </div>

        <!-- 空白流式状态指示器 -->
        <div v-if="isStreaming && !streamingContent && !streamingReasoning" class="message-item assistant streaming-message">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 知识库和工具栏 -->
    <div class="tools-bar" v-if="conversationId || route.query.agentId">
      <div class="tools-bar-content">
        <!-- 知识库选择器 -->
        <div class="tool-section kb-section">
          <div class="tool-section-left">
            <el-icon class="tool-icon kb-icon"><Reading /></el-icon>
            <span class="tool-label">知识库:</span>
            <el-select
              v-model="selectedKnowledgeBase"
              placeholder="未启用知识库"
              clearable
              @change="handleKnowledgeBaseChange"
              class="tool-select kb-select"
            >
              <el-option
                v-for="kb in knowledgeBases"
                :key="kb.name"
                :label="kb.name"
                :value="kb.name"
              >
                <div class="kb-option">
                  <span class="kb-option-name">{{ kb.name }}</span>
                  <span class="kb-option-docs">{{ kb.num_documents || 0 }} 文档</span>
                </div>
              </el-option>
            </el-select>
            <el-tag v-if="selectedKnowledgeBase" type="success" size="small" class="kb-status">
              <el-icon><Check /></el-icon>
              已启用
            </el-tag>
          </div>
          <div class="tool-section-right">
            <el-button
              circle
              size="small"
              @click="showKnowledgeBaseManager"
              :icon="Management"
              title="管理知识库"
            />
          </div>
        </div>

        <!-- 分隔线 -->
        <el-divider direction="vertical" class="tool-divider" />

        <!-- 联网搜索开关 -->
        <div class="tool-section search-section">
          <el-icon class="tool-icon search-icon"><Search /></el-icon>
          <span class="tool-label">联网搜索</span>
          <el-switch
            v-model="enableWebSearch"
            active-text="开"
            inactive-text="关"
            size="default"
          />
          <el-tooltip
            v-if="conversation?.agent?.enable_web_search"
            content="该智能体默认启用联网搜索"
            placement="top"
          >
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>

        <!-- 分隔线 -->
        <el-divider direction="vertical" class="tool-divider" />

        <!-- 深度思考开关 -->
        <div class="tool-section thinking-section">
          <el-icon class="tool-icon thinking-icon"><MagicStick /></el-icon>
          <span class="tool-label">深度思考</span>
          <el-switch
            v-model="showReasoning"
            active-text="开"
            inactive-text="关"
            size="default"
          />
          <el-tooltip
            content="启用深度思考功能，让AI在回答前进行详细推理。注意：需要使用支持深度思考的模型（如glm-4-plus），并且仅对复杂问题触发推理过程"
            placement="top"
          >
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>

        <!-- 分隔线 -->
        <el-divider direction="vertical" class="tool-divider" />

        <!-- 流式输出速度控制 -->
        <div class="tool-section speed-section">
          <el-icon class="tool-icon speed-icon"><Timer /></el-icon>
          <span class="tool-label">输出速度</span>
          <el-select
            v-model="outputSpeed"
            class="speed-select"
            @change="handleSpeedChange"
            :disabled="isStreaming"
          >
            <el-option
              v-for="option in speedOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            >
              <div class="speed-option">
                <span class="speed-option-label">{{ option.label }}</span>
                <span class="speed-option-desc">{{ option.desc }}</span>
              </div>
            </el-option>
          </el-select>
          <el-tooltip
            content="控制AI回复的输出速度，可根据个人喜好和阅读习惯调整"
            placement="top"
          >
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
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

    <!-- 知识库管理组件 -->
    <KnowledgeBaseManager
      v-model:visible="kbManagerVisible"
      :conversation-id="conversationId"
      @knowledgeBaseSelected="handleKnowledgeBaseSelected"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Reading, Management, Check, Loading, CircleClose, Search, InfoFilled, MagicStick, Timer } from '@element-plus/icons-vue'
import { chatApi, conversationApi, agentApi } from '../api/agent'
import { knowledgeBaseApi } from '../api/knowledgeBase'
import { renderMarkdown } from '../utils/markdown'
import { formatTime } from '../utils/time'
import { throttle } from 'lodash-es'
import { showErrorNotification, ErrorTypes, withRetry, getErrorType } from '../utils/errorHandler'
import KnowledgeBaseManager from '../components/KnowledgeBaseManager.vue'

const router = useRouter()
const route = useRoute()

// 数据状态
const loading = ref(false)
const messages = ref([])
const conversation = ref(null)
const conversationId = ref(null)
const isStreaming = ref(false)
const streamingContent = ref('')
const streamingReasoning = ref('')
const isReasoningPhase = ref(false)
const abortController = ref(null)

// 知识库相关状态
const knowledgeBases = ref([])
const selectedKnowledgeBase = ref(null)
const kbManagerVisible = ref(false)

// 联网搜索相关状态
const enableWebSearch = ref(false)

// 深度思考相关状态
const showReasoning = ref(false)

// 流式输出速度控制
const outputSpeed = ref(30)  // 默认 30 字符/秒
const speedOptions = [
  { label: '慢速', value: 15, desc: '适合仔细阅读' },
  { label: '正常', value: 30, desc: '推荐速度' },
  { label: '快速', value: 80, desc: '提高效率' },
  { label: '极速', value: 0, desc: '原始速度，无限制' }
]

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

      // 如果智能体默认启用联网搜索，则设置开关状态
      if (conversation.value.agent?.enable_web_search) {
        enableWebSearch.value = true
      }
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
    const response = await chatApi.getMessages(conversationId.value)

    if (response.code === 200 || response.status === 'success') {
      messages.value = response.data || []
      await nextTick()
      scrollToBottom()
    } else {
      ElMessage.error(response.message || '获取消息历史失败')
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

// 流式发送消息（带固定速度控制）
const sendMessageStream = async (content) => {
  // 用户消息对象，用于错误时移除
  let userMessage = null
  const tokenBuffer = []  // token 缓冲区
  let isProcessing = false  // 是否正在处理缓冲区
  let receiveComplete = false  // 接收是否完成

  try {
    isStreaming.value = true
    streamingContent.value = ''
    streamingReasoning.value = ''
    isReasoningPhase.value = false
    abortController.value = new AbortController()

    // 立即将用户消息添加到消息列表中显示
    userMessage = {
      id: Date.now(), // 临时ID,后端会返回真实ID
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    }
    messages.value.push(userMessage)
    await nextTick()
    scrollToBottom()

    const token = localStorage.getItem('access_token')
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

    const response = await fetch(`${apiBaseUrl}/chat/conversations/${conversationId.value}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        content,
        stream: true,
        enable_web_search: enableWebSearch.value,
        show_reasoning: showReasoning.value
      }),
      signal: abortController.value.signal
    })

    if (!response.ok) {
      throw new Error('发送消息失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    // ========== 边接收边渲染模式 ==========

    // 启动接收线程（异步）
    const receiveData = async () => {
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))

                // 将事件添加到缓冲区
                if (data.type === 'start') {
                  tokenBuffer.push({ type: 'start', reasoning_enabled: data.reasoning_enabled })
                } else if (data.type === 'reasoning') {
                  tokenBuffer.push({ type: 'reasoning', content: data.content })
                } else if (data.type === 'reasoning_end') {
                  tokenBuffer.push({ type: 'reasoning_end' })
                } else if (data.type === 'content') {
                  tokenBuffer.push({ type: 'content', content: data.content })
                } else if (data.type === 'token') {
                  tokenBuffer.push({ type: 'token', content: data.content })
                } else if (data.type === 'end') {
                  tokenBuffer.push({ type: 'end', message_id: data.message_id, tokens: data.tokens })
                } else if (data.type === 'error') {
                  tokenBuffer.push({ type: 'error', message: data.message })
                }
              } catch (e) {
                // 忽略解析错误
              }
            }
          }
        }
        receiveComplete = true
      } catch (error) {
        console.error('接收数据出错:', error)
        tokenBuffer.push({ type: 'error', message: '接收数据失败' })
        receiveComplete = true
      }
    }

    // 启动渲染线程（异步）
    const processBuffer = async () => {
      if (isProcessing) return
      isProcessing = true

      let endReceived = false  // 是否收到 end 事件

      while (true) {
        // 如果缓冲区为空
        if (tokenBuffer.length === 0) {
          if (endReceived) {
            // 已收到 end 事件且缓冲区为空，退出
            break
          }
          if (receiveComplete) {
            // 接收完成但未收到 end，等待一下
            await new Promise(resolve => setTimeout(resolve, 50))
            continue
          }
          // 等待 10ms 后继续
          await new Promise(resolve => setTimeout(resolve, 10))
          continue
        }

        const token = tokenBuffer.shift()

        if (token.type === 'start') {
          if (token.reasoning_enabled) {
            isReasoningPhase.value = true
          }
        } else if (token.type === 'reasoning') {
          streamingReasoning.value += token.content
          isReasoningPhase.value = true
        } else if (token.type === 'reasoning_end') {
          isReasoningPhase.value = false
        } else if (token.type === 'content' || token.type === 'token') {
          streamingContent.value += token.content
        } else if (token.type === 'end') {
          // 标记收到 end 事件，但继续处理剩余缓冲区内容
          endReceived = true
          continue
        } else if (token.type === 'error') {
          ElMessage.error(token.message || '发送消息失败')
          streamingContent.value = ''
          streamingReasoning.value = ''
          break
        }

        // 更新UI和滚动
        await nextTick()
        scrollToBottom()

        // ========== 固定速度控制核心逻辑 ==========
        // 每个字（token）都单独处理，根据速度设置不同的延迟
        if (outputSpeed.value === 0) {
          // 极速模式：不延迟，直接显示（原始流式速度）
          continue
        } else {
          // 其他模式：每个字之间都有延迟，延迟时间 = 1000ms / 速度
          const delay = Math.max(10, Math.floor(1000 / outputSpeed.value))
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }

      // 流式输出结束后保存消息
      if (endReceived && streamingContent.value) {
        const finalContent = streamingContent.value
        const finalReasoning = streamingReasoning.value

        const messageData = {
          id: Date.now(),  // 使用临时 ID
          role: 'assistant',
          content: finalContent,
          created_at: new Date().toISOString()
        }

        if (finalReasoning) {
          messageData.reasoning = {
            content: finalReasoning,
            length: finalReasoning.length
          }
        }

        messages.value.push(messageData)
        await nextTick()

        // 清空流式状态
        streamingContent.value = ''
        streamingReasoning.value = ''

        setTimeout(() => {
          isStreaming.value = false
          isReasoningPhase.value = false
        }, 50)

        await nextTick()
        scrollToBottom()
      }

      isProcessing = false
    }

    // 同时启动接收和渲染线程
    await Promise.all([
      receiveData(),
      processBuffer()
    ])

    // 只刷新对话信息（标题、消息统计等），不需要重新获取消息列表
    await fetchConversation()

  } catch (error) {
    if (error.name === 'AbortError') {
      ElMessage.info('已停止生成')
    } else {
      // 使用增强的错误处理
      showErrorNotification(error, ElMessage, {
        duration: 5000
      })

      // 移除临时添加的用户消息
      if (userMessage) {
        const index = messages.value.findIndex(m => m.id === userMessage.id)
        if (index !== -1) {
          messages.value.splice(index, 1)
        }
      }

      // 如果是认证错误，跳转到登录页
      if (getErrorType(error) === ErrorTypes.AUTH) {
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      }
    }
    streamingContent.value = ''
    streamingReasoning.value = ''
  } finally {
    isStreaming.value = false
    isProcessing = false
    abortController.value = null
  }
}

// 普通发送消息
const sendMessageNormal = async (content) => {
  try {
    isStreaming.value = true

    // 立即将用户消息添加到消息列表中显示
    const userMessage = {
      id: Date.now(), // 临时ID,后端会返回真实ID
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    }
    messages.value.push(userMessage)
    await nextTick()
    scrollToBottom()

    const response = await chatApi.chat(conversationId.value, {
      content,
      stream: false,
      enable_web_search: enableWebSearch.value,
      show_reasoning: showReasoning.value
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

      // 如果用户已经选择了知识库，自动应用到新对话
      if (selectedKnowledgeBase.value) {
        try {
          await knowledgeBaseApi.toggleConversationRAG(conversationId.value, {
            enable_rag: true,
            rag_index_name: selectedKnowledgeBase.value,
            rag_config: {
              search_type: 'similarity',
              k: 5
            }
          })
          ElMessage.success(`已启用知识库: ${selectedKnowledgeBase.value}`)
        } catch (error) {
          console.error('启用知识库失败:', error)
        }
      }

      // 使用流式发送消息(会在 sendMessageStream 内部添加用户消息)
      await sendMessageStream(content)
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
    abortController.value = new AbortController()

    // 删除该消息后的所有消息
    const messageIndex = messages.value.findIndex(m => m.id === message.id)
    if (messageIndex !== -1) {
      messages.value = messages.value.slice(0, messageIndex)
    }

    const token = localStorage.getItem('access_token')
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

    const response = await fetch(`${apiBaseUrl}/chat/conversations/${conversationId.value}/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ stream: true }),
      signal: abortController.value.signal
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
              // 先保存流式内容
              const finalContent = streamingContent.value

              // 添加到消息列表
              messages.value.push({
                id: data.message_id,
                role: 'assistant',
                content: finalContent,
                created_at: new Date().toISOString()
              })

              // 等待消息添加完成后，再清空流式状态
              await nextTick()

              // 使用平滑过渡，先隐藏流式消息
              streamingContent.value = ''

              // 延迟重置流式状态，让DOM有时间渲染
              setTimeout(() => {
                isStreaming.value = false
              }, 50)

              // 滚动到底部
              await nextTick()
              scrollToBottom()
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    // 只刷新对话信息，不需要重新获取消息列表
    await fetchConversation()

  } catch (error) {
    if (error.name === 'AbortError') {
      ElMessage.info('已停止生成')
    } else {
      console.error('重新生成失败:', error)
      ElMessage.error('重新生成失败')
    }
    streamingContent.value = ''
  } finally {
    isStreaming.value = false
    abortController.value = null
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

// 复制流式内容
const copyStreamingContent = async () => {
  try {
    await navigator.clipboard.writeText(streamingContent.value)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 停止流式输出
const stopStreaming = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
}

// 给消息评分
const rateMessage = async (message, rating) => {
  try {
    const response = await chatApi.messageFeedback(message.id, { rating })

    if (response.code === 200) {
      ElMessage.success(`评分成功：${rating} 星`)

      // 更新消息的评分状态
      const messageIndex = messages.value.findIndex(m => m.id === message.id)
      if (messageIndex !== -1) {
        messages.value[messageIndex].rating = rating
      }
    } else {
      ElMessage.error(response.message || '评分失败')
    }
  } catch (error) {
    console.error('评分失败:', error)
    const errorMessage = error.backendMessage || error.message || '评分失败，请稍后重试'
    ElMessage.error(errorMessage)
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
      await fetchMessages()  // 添加这行，加载新对话的消息
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

// 滚动到底部（使用 throttle 节流优化性能）
const scrollToBottom = throttle(() => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}, 100)  // 100ms 内最多执行一次

// 监听输入框内容变化，动态调整行数
watch(inputMessage, (newValue) => {
  const lines = newValue.split('\n').length
  inputRows.value = Math.min(Math.max(lines, 1), 5)
})

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    const response = await knowledgeBaseApi.getKnowledgeBases()
    if (response.code === 200) {
      knowledgeBases.value = response.data || []
    }
  } catch (error) {
    console.error('加载知识库列表失败:', error)
  }
}

// 显示知识库管理器
const showKnowledgeBaseManager = () => {
  kbManagerVisible.value = true
}

// 知识库选择变化
const handleKnowledgeBaseChange = async (value) => {
  // 如果还没有创建对话，暂存选择，等创建对话后再应用
  if (!conversationId.value) {
    if (value) {
      ElMessage.info(`知识库 "${value}" 将在对话开始后启用`)
    }
    return
  }

  try {
    if (value) {
      // 启用 RAG 模式
      await knowledgeBaseApi.toggleConversationRAG(conversationId.value, {
        enable_rag: true,
        rag_index_name: value,
        rag_config: {
          search_type: 'similarity',
          k: 5
        }
      })
      ElMessage.success(`已启用知识库: ${value}`)
    } else {
      // 禁用 RAG 模式
      await knowledgeBaseApi.toggleConversationRAG(conversationId.value, {
        enable_rag: false,
        rag_index_name: null,
        rag_config: {}
      })
      ElMessage.info('已禁用知识库')
    }
  } catch (error) {
    console.error('切换知识库失败:', error)
    ElMessage.error(error.backendMessage || '切换知识库失败')
    // 恢复选择
    selectedKnowledgeBase.value = value ? null : value
  }
}

// 从知识库管理器选择知识库
const handleKnowledgeBaseSelected = (kbName) => {
  selectedKnowledgeBase.value = kbName
  handleKnowledgeBaseChange(kbName)
}

// 速度变化处理
const handleSpeedChange = (value) => {
  outputSpeed.value = value
  localStorage.setItem('chat_output_speed', value)

  // 显示当前速度提示
  const option = speedOptions.find(opt => opt.value === value)
  if (option) {
    ElMessage.success(`输出速度已设置为：${option.label}`)
  }
}

// 初始化
onMounted(async () => {
  // 从 localStorage 读取保存的速度设置
  const savedSpeed = localStorage.getItem('chat_output_speed')
  if (savedSpeed) {
    outputSpeed.value = parseInt(savedSpeed)
  }

  conversationId.value = route.query.conversationId || null

  if (conversationId.value) {
    await fetchConversation()
    await fetchMessages()
    // 加载当前对话的知识库配置
    if (conversation.value?.enable_rag) {
      selectedKnowledgeBase.value = conversation.value.rag_index_name
    }
  } else if (route.query.agentId) {
    // 如果有智能体ID，显示智能体信息
    ElMessage.info('开始新对话')
  }

  // 加载知识库列表
  await loadKnowledgeBases()
})

// 监听对话ID变化，重新加载对话信息和消息
watch(conversationId, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    // 清空当前消息，避免显示旧对话的消息
    messages.value = []
    await fetchConversation()
    await fetchMessages()  // 添加这行，加载新对话的消息

    // 更新知识库配置
    if (conversation.value?.enable_rag) {
      selectedKnowledgeBase.value = conversation.value.rag_index_name
    } else {
      selectedKnowledgeBase.value = null
    }
  }
})
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  overflow: hidden;
  max-width: 1400px;
  margin: 0 auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.06);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  backdrop-filter: blur(10px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.conversation-info h3 {
  margin: 0 0 6px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.conversation-info p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: transparent;
}

.loading-container,
.empty-chat {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.empty-icon {
  font-size: 80px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.messages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 900px;
  margin: 0 auto;
  padding: 0 8px;
}

.message-item {
  display: block;
  width: 100%;
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

.user-message {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.user-message-content {
  background: #f4f4f5;
  color: #27272a;
  border-radius: 20px;
  padding: 10px 14px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  max-width: 70%;
  display: inline-block;
  word-break: break-word;
  white-space: normal;
  font-size: 15px;
  line-height: 1.5;
  font-weight: 400;
  border: 1px solid #e4e4e7;
}

.assistant-message {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  margin-bottom: 16px;
}

.assistant-message-text {
  color: #27272a;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.4;
  font-size: 15px;
  font-weight: 400;
  width: 100%;
}

/* 确保表格内的文本不换行 */
.assistant-message-text :deep(table) {
  white-space: normal;
}

.assistant-message-text :deep(td),
.assistant-message-text :deep(th) {
  white-space: normal;
}

.streaming-message {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  margin-bottom: 16px;
}

.streaming-text {
  min-height: 24px;
}

.message-actions {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.message-actions :deep(.el-button) {
  color: #71717a;
  font-size: 12px;
  padding: 4px 10px;
  height: auto;
  border-radius: 6px;
  transition: all 0.2s ease;
  font-weight: 400;
  background: transparent;
  border: 1px solid transparent;
}

.message-actions :deep(.el-button:hover) {
  color: #52525b;
  background: #f4f4f5;
  border-color: #e4e4e7;
}

.streaming-actions {
  margin-top: 4px;
}

.streaming-actions :deep(.el-button) {
  font-size: 12px;
  padding: 4px 10px;
}

.rated-btn {
  color: #f59e0b !important;
  font-weight: 400;
}

/* 推理过程样式 */
.reasoning-container {
  margin-bottom: 12px;
  border: 1px solid #e4e4e7;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f4f4f5;
  border-bottom: 1px solid #e4e4e7;
}

.reasoning-icon {
  font-size: 16px;
  color: #8b5cf6;
}

.reasoning-title {
  font-size: 13px;
  font-weight: 500;
  color: #52525b;
  flex: 1;
}

.reasoning-content {
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
  color: #71717a;
  max-height: 400px;
  overflow-y: auto;
  background: white;
}

.reasoning-content :deep(p) {
  margin: 4px 0;
}

.reasoning-content :deep(code) {
  background: #f4f4f5;
  color: #71717a;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.reasoning-content :deep(pre) {
  background: #f4f4f5;
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

/* 深度思考开关样式 */
.thinking-section {
  flex: 1;
  justify-content: flex-start;
  gap: 10px;
}

.thinking-icon {
  color: #8b5cf6;
}

/* 流式输出速度控制样式 */
.speed-section {
  flex: 1;
  justify-content: flex-start;
  gap: 10px;
}

.speed-icon {
  color: #f59e0b;
}

.speed-select {
  width: 120px;
}

.speed-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  transition: all 0.2s;
}

.speed-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #f59e0b inset;
}

.speed-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.speed-option-label {
  font-weight: 500;
  color: #1e293b;
  font-size: 14px;
}

.speed-option-desc {
  font-size: 12px;
  color: #94a3b8;
}

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 12px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a1a1aa;
  animation: typing 1.4s infinite ease-in-out;
  box-shadow: 0 2px 4px rgba(161, 161, 170, 0.3);
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
    opacity: 0.4;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

/* Markdown 样式 */
.markdown-content {
  line-height: 1.4;
  color: #27272a;
}

.markdown-content :deep(p) {
  margin: 4px 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin: 16px 0 8px 0;
  font-weight: 600;
  color: #18181b;
  line-height: 1.3;
  letter-spacing: -0.02em;
}

.markdown-content :deep(h1) {
  font-size: 1.75em;
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
}

.markdown-content :deep(h3) {
  font-size: 1.25em;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(code) {
  background: #f4f4f5;
  color: #71717a;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
  font-weight: 400;
  border: 1px solid #e4e4e7;
}

.markdown-content :deep(pre) {
  background: #f4f4f5;
  color: #27272a;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  font-size: 14px;
  line-height: 1.6;
  border: 1px solid #e4e4e7;
}

.markdown-content :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
  font-weight: 400;
  border: none;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid #d4d4d8;
  padding-left: 12px;
  margin: 12px 0;
  color: #71717a;
  font-style: italic;
  background: #fafafa;
  padding: 10px 12px;
  border-radius: 0 6px 6px 0;
}

.markdown-content :deep(a) {
  color: #52525b;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.2s;
  font-weight: 400;
}

.markdown-content :deep(a:hover) {
  border-bottom-color: #52525b;
  color: #27272a;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  white-space: normal;
  display: table;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e4e4e7;
  padding: 8px 12px;
  text-align: left;
  white-space: normal;
}

.markdown-content :deep(th) {
  background: #fafafa;
  font-weight: 500;
  color: #52525b;
}

.markdown-content :deep(tr:hover) {
  background: #fafafa;
}

/* 输入区域 */
.chat-input-container {
  background: white;
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  backdrop-filter: blur(10px);
}

.input-wrapper {
  max-width: 100%;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.input-actions-left,
.input-actions-right {
  display: flex;
  gap: 8px;
}

/* 工具栏 */
.tools-bar {
  background: white;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
}

.tools-bar-content {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  gap: 16px;
}

/* 工具区块 */
.tool-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
}

.tool-section-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.tool-section-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.kb-icon {
  color: #7c3aed;
}

.search-icon {
  color: #3b82f6;
}

.tool-label {
  font-size: 14px;
  color: #475569;
  font-weight: 500;
  white-space: nowrap;
}

.tool-select {
  flex: 1;
  max-width: 300px;
}

/* 垂直分隔线 */
.tool-divider {
  height: 32px;
  margin: 0;
  border-color: #e5e7eb;
}

/* 信息提示图标 */
.info-icon {
  font-size: 16px;
  color: #94a3b8;
  cursor: help;
  margin-left: 4px;
  flex-shrink: 0;
}

.info-icon:hover {
  color: #3b82f6;
}

/* 知识库选择器样式 */
.kb-section {
  flex: 2;
  max-width: 60%;
}

.kb-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  transition: all 0.2s;
}

.kb-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #7c3aed inset;
}

.kb-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.kb-option-name {
  font-weight: 500;
  color: #1e293b;
  font-size: 14px;
}

.kb-option-docs {
  font-size: 12px;
  color: #94a3b8;
}

.kb-status {
  flex-shrink: 0;
}

/* 联网搜索区块 */
.search-section {
  flex: 1;
  justify-content: flex-start;
  gap: 10px;
}

.kb-selector-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 900px;
  margin: 0 auto;
}

.kb-selector-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.kb-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.kb-status {
  margin-left: 8px;
}

.kb-selector-right {
  margin-left: 12px;
}

/* 滚动条美化 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
  transition: background 0.2s;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 响应式 */
@media (max-width: 768px) {
  .messages-wrapper {
    padding: 0 4px;
  }

  .user-message .message-content,
  .assistant-message .message-content {
    max-width: 90%;
  }

  .message-actions {
    gap: 6px;
  }

  .message-actions :deep(.el-button) {
    padding: 5px 10px;
    font-size: 12px;
  }
}
</style>
