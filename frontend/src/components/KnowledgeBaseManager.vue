<template>
  <el-dialog
    v-model="dialogVisible"
    title="知识库管理"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 工具栏 -->
    <template #header>
      <div class="dialog-header">
        <span>知识库管理</span>
        <el-button type="primary" size="small" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建知识库
        </el-button>
      </div>
    </template>

    <!-- 知识库列表 -->
    <div v-loading="loading" class="knowledge-list">
      <el-empty v-if="!loading && knowledgeBases.length === 0" description="暂无知识库">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          创建第一个知识库
        </el-button>
      </el-empty>

      <el-table
        v-else
        :data="knowledgeBases"
        stripe
        class="knowledge-table"
        :header-cell-style="{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: '#ffffff',
          fontWeight: '600',
          fontSize: '14px'
        }"
        :row-style="{ height: '70px' }"
        :cell-style="{ padding: '16px 0' }"
      >
        <el-table-column prop="name" label="索引名称" width="200">
          <template #default="{ row }">
            <div class="index-name-cell">
              <div class="index-name-wrapper">
                <el-icon class="index-icon" color="#667eea"><Reading /></el-icon>
                <span class="index-name-text">{{ row.name }}</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="220">
          <template #default="{ row }">
            <div class="description-cell">
              {{ row.description || '暂无描述' }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="num_documents" label="文档数量" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="large" class="stat-tag">
              <el-icon class="tag-icon"><Document /></el-icon>
              {{ row.num_documents || 0 }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="size_mb" label="存储大小" width="120" align="center">
          <template #default="{ row }">
            <div class="size-cell">
              <el-icon class="size-icon"><Connection /></el-icon>
              <span>{{ row.size_mb ? row.size_mb.toFixed(2) + ' MB' : 'N/A' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="170" align="center">
          <template #default="{ row }">
            <div class="time-cell">
              <el-icon class="time-icon"><View /></el-icon>
              <span>{{ formatDateTime(row.created_at) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button size="default" @click="handleView(row)" class="action-btn view-btn">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button size="default" @click="handleAddDocument(row)" class="action-btn upload-btn">
                <el-icon><Upload /></el-icon>
                添加文档
              </el-button>
              <el-button size="default" type="danger" @click="handleDelete(row)" class="action-btn delete-btn">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建知识库对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建知识库"
      width="600px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="120px">
        <el-form-item label="索引名称" prop="index_name">
          <el-input
            v-model="createForm.index_name"
            placeholder="只能包含字母、数字、下划线和中划线"
            maxlength="50"
            show-word-limit
          />
          <div class="form-tip">唯一标识，用于API调用和切换知识库</div>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="2"
            placeholder="知识库的简要描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="文档文件">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :on-exceed="handleExceed"
            :file-list="fileList"
            drag
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持格式：{{ supportedFormatsText }}，{{ fileSizeText }}
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="分块参数">
          <div class="chunk-params">
            <el-input-number
              v-model="createForm.chunk_size"
              :min="100"
              :max="4000"
              :step="100"
              placeholder="分块大小"
            />
            <el-input-number
              v-model="createForm.chunk_overlap"
              :min="0"
              :max="1000"
              :step="50"
              placeholder="重叠大小"
            />
            <el-select v-model="createForm.splitter_type" placeholder="分块器类型">
              <el-option label="递归分块" value="recursive" />
              <el-option label="字符分块" value="character" />
              <el-option label="Markdown分块" value="markdown" />
              <el-option label="Token分块" value="token" />
            </el-select>
          </div>
          <div class="form-tip">留空使用默认配置</div>
        </el-form-item>

        <el-form-item label="覆盖已存在">
          <el-switch v-model="createForm.overwrite" />
          <span class="switch-label">如果知识库已存在，是否覆盖</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          创建知识库
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加文档对话框 -->
    <el-dialog
      v-model="addDocDialogVisible"
      title="添加文档到知识库"
      width="600px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-alert
        v-if="currentKB"
        :title="`将文档添加到知识库：${currentKB.name}`"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      />

      <el-form :model="addDocForm" ref="addDocFormRef" label-width="120px">
        <el-form-item label="文档文件" required>
          <el-upload
            ref="addDocUploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleAddDocFileChange"
            :on-remove="handleAddDocFileRemove"
            :on-exceed="handleExceed"
            :file-list="addDocFileList"
            drag
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持格式：{{ supportedFormatsText }}，{{ fileSizeText }}
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="分块参数">
          <div class="chunk-params">
            <el-input-number
              v-model="addDocForm.chunk_size"
              :min="100"
              :max="4000"
              :step="100"
              placeholder="分块大小"
            />
            <el-input-number
              v-model="addDocForm.chunk_overlap"
              :min="0"
              :max="1000"
              :step="50"
              placeholder="重叠大小"
            />
            <el-select v-model="addDocForm.splitter_type" placeholder="分块器类型">
              <el-option label="递归分块" value="recursive" />
              <el-option label="字符分块" value="character" />
              <el-option label="Markdown分块" value="markdown" />
              <el-option label="Token分块" value="token" />
            </el-select>
          </div>
          <div class="form-tip">留空使用默认配置</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addDocDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addingDoc" @click="handleAddDocSubmit">
          添加文档
        </el-button>
      </template>
    </el-dialog>

    <!-- 知识库详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`知识库详情 - ${currentKB?.name}`"
      width="900px"
      append-to-body
    >
      <div v-if="currentKB" class="detail-content">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4 class="section-title">
            <el-icon><Reading /></el-icon>
            基本信息
          </h4>
          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="索引名称" :span="1">
              <el-tag type="primary" size="large">{{ currentKB.name }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="1">
              {{ currentKB.description || '暂无描述' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 统计信息 -->
        <div class="detail-section">
          <h4 class="section-title">
            <el-icon><Document /></el-icon>
            统计信息
          </h4>
          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="文档数量">
              <el-tag type="success" size="large">
                <el-icon class="tag-icon"><Document /></el-icon>
                {{ currentKB.doc_count || currentKB.num_documents || 0 }} 个
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="存储大小">
              <el-tag type="info" size="large">
                <el-icon class="tag-icon"><Connection /></el-icon>
                {{ currentKB.size_mb ? currentKB.size_mb.toFixed(2) + ' MB' : 'N/A' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 配置信息 -->
        <div class="detail-section">
          <h4 class="section-title">
            <el-icon><Connection /></el-icon>
            配置信息
          </h4>
          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="向量维度" v-if="currentKB.metadata">
              {{ currentKB.metadata.dimension || 'N/A' }}
            </el-descriptions-item>
            <el-descriptions-item label="存储路径" :span="2">
              <el-text truncated>{{ currentKB.path || 'N/A' }}</el-text>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 分块配置 -->
        <div class="detail-section" v-if="currentKB.metadata && (currentKB.metadata.chunk_size || currentKB.metadata.chunk_overlap || currentKB.metadata.splitter_type)">
          <h4 class="section-title">
            <el-icon><Upload /></el-icon>
            分块配置
          </h4>
          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="分块大小" v-if="currentKB.metadata.chunk_size">
              {{ currentKB.metadata.chunk_size }} tokens
            </el-descriptions-item>
            <el-descriptions-item label="重叠大小" v-if="currentKB.metadata.chunk_overlap">
              {{ currentKB.metadata.chunk_overlap }} tokens
            </el-descriptions-item>
            <el-descriptions-item label="分块器类型" :span="2" v-if="currentKB.metadata.splitter_type">
              {{ getSplitterTypeName(currentKB.metadata.splitter_type) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 时间信息 -->
        <div class="detail-section">
          <h4 class="section-title">
            <el-icon><View /></el-icon>
            时间信息
          </h4>
          <el-descriptions :column="2" border class="detail-descriptions">
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(currentKB.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDateTime(currentKB.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleAddDocument(currentKB)">
          <el-icon><Upload /></el-icon>
          添加文档
        </el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Reading,
  View,
  Upload,
  Delete,
  UploadFilled,
  Document,
  Connection
} from '@element-plus/icons-vue'
import { knowledgeBaseApi } from '../api/knowledgeBase'
import { ragApi } from '../api/rag'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  conversationId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'knowledgeBaseSelected'])

// 响应式数据
const dialogVisible = ref(false)
const loading = ref(false)
const knowledgeBases = ref([])
const currentKB = ref(null)

// 支持的文件格式
const supportedFormats = ref([])
const maxFileSize = ref(100) // 默认100MB

// 创建知识库相关
const createDialogVisible = ref(false)
const creating = ref(false)
const createFormRef = ref(null)
const fileList = ref([])
const createForm = reactive({
  index_name: '',
  description: '',
  chunk_size: null,
  chunk_overlap: null,
  splitter_type: 'recursive',
  overwrite: false
})

const createRules = {
  index_name: [
    { required: true, message: '请输入索引名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和中划线', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入描述', trigger: 'blur' }
  ]
}

// 添加文档相关
const addDocDialogVisible = ref(false)
const addingDoc = ref(false)
const addDocFormRef = ref(null)
const addDocFileList = ref([])
const addDocForm = reactive({
  chunk_size: null,
  chunk_overlap: null,
  splitter_type: 'recursive'
})

// 知识库详情
const detailDialogVisible = ref(false)

// 监听 visible 变化
watch(() => props.visible, (newVal) => {
  dialogVisible.value = newVal
  if (newVal) {
    loadKnowledgeBases()
  }
})

watch(dialogVisible, (newVal) => {
  emit('update:visible', newVal)
})

// 计算属性 - 格式化支持格式文本
const supportedFormatsText = computed(() => {
  if (supportedFormats.value.length === 0) {
    return '加载中...'
  }
  const formatNames = supportedFormats.value.map(f => f.description || f.type)
  return formatNames.join('、')
})

// 计算属性 - 格式化文件大小文本
const fileSizeText = computed(() => {
  return `最大 ${maxFileSize.value}MB`
})

// 加载支持的文件格式
const loadSupportedFormats = async () => {
  try {
    const response = await ragApi.getSupportedFormats()
    if (response.code === 200 && response.data) {
      supportedFormats.value = response.data.formats || []
      maxFileSize.value = response.data.max_file_size_mb || 100
    }
  } catch (error) {
    console.error('获取支持的文件格式失败:', error)
    // 使用默认值
    supportedFormats.value = [
      { extension: '.pdf', type: 'pdf', description: 'PDF文档' },
      { extension: '.txt', type: 'text', description: '纯文本' },
      { extension: '.md', type: 'markdown', description: 'Markdown' },
      { extension: '.html', type: 'html', description: 'HTML' },
      { extension: '.json', type: 'json', description: 'JSON' }
    ]
    maxFileSize.value = 100
  }
}

// 加载知识库列表
const loadKnowledgeBases = async () => {
  loading.value = true
  try {
    const response = await knowledgeBaseApi.getKnowledgeBases()
    knowledgeBases.value = response.data || []
  } catch (error) {
    ElMessage.error(error.backendMessage || '加载知识库列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  createDialogVisible.value = true
  resetCreateForm()
}

// 重置创建表单
const resetCreateForm = () => {
  Object.assign(createForm, {
    index_name: '',
    description: '',
    chunk_size: null,
    chunk_overlap: null,
    splitter_type: 'recursive',
    overwrite: false
  })
  fileList.value = []
  if (createFormRef.value) {
    createFormRef.value.clearValidate()
  }
}

// 文件选择变化
const handleFileChange = (file, uploadFileList) => {
  console.log('handleFileChange - file:', file)
  console.log('handleFileChange - uploadFileList:', uploadFileList)
  console.log('handleFileChange - file.raw:', file.raw)
  console.log('handleFileChange - file.name:', file.name)

  // Element Plus Upload 组件传递的是整个文件列表
  // file 参数就是新选中的文件对象
  if (file && file.raw) {
    // 确保 raw 属性存在（这是实际的 File 对象）
    fileList.value = [file]
    console.log('文件已添加到 fileList，当前 fileList:', fileList.value)
  } else {
    console.error('文件对象无效或缺少 raw 属性')
    fileList.value = []
  }
}

// 文件移除
const handleFileRemove = () => {
  fileList.value = []
}

// 处理超出限制
const handleExceed = () => {
  ElMessage.warning('最多只能上传 1 个文件')
}

// 创建知识库
const handleCreate = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  await createFormRef.value.validate()

  creating.value = true
  try {
    const formData = new FormData()

    // 获取文件对象
    const fileWrapper = fileList.value[0]
    console.log('准备上传 - 文件包装对象:', fileWrapper)
    console.log('准备上传 - file.raw:', fileWrapper.raw)

    // 确保使用正确的文件对象
    const fileToUpload = fileWrapper.raw
    if (!fileToUpload) {
      console.error('文件对象无效，file.raw 为空')
      ElMessage.error('文件对象无效，请重新选择文件')
      return
    }

    console.log('实际上传的文件对象:', fileToUpload)
    console.log('文件名:', fileToUpload.name)
    console.log('文件类型:', fileToUpload.type)
    console.log('文件大小:', fileToUpload.size)

    formData.append('file', fileToUpload)
    formData.append('index_name', createForm.index_name)
    formData.append('description', createForm.description)

    if (createForm.chunk_size) {
      formData.append('chunk_size', createForm.chunk_size)
    }
    if (createForm.chunk_overlap) {
      formData.append('chunk_overlap', createForm.chunk_overlap)
    }
    if (createForm.splitter_type) {
      formData.append('splitter_type', createForm.splitter_type)
    }
    formData.append('overwrite', createForm.overwrite.toString())

    console.log('FormData 内容:')
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}:`, value)
    }

    await knowledgeBaseApi.createKnowledgeBase(formData)

    ElMessage.success('知识库创建成功')
    createDialogVisible.value = false
    loadKnowledgeBases()
  } catch (error) {
    console.error('创建知识库错误:', error)
    ElMessage.error(error.backendMessage || '创建知识库失败')
  } finally {
    creating.value = false
  }
}

// 查看知识库详情
const handleView = async (row) => {
  currentKB.value = row
  detailDialogVisible.value = true

  // 加载详细信息
  await loadKnowledgeBaseDetail(row.name)
}

// 加载知识库详细信息
const loadKnowledgeBaseDetail = async (indexName) => {
  try {
    const response = await knowledgeBaseApi.getKnowledgeBaseInfo(indexName)
    if (response.code === 200 || response.status === 'success') {
      // 更新currentKB为详细信息
      currentKB.value = { ...currentKB.value, ...response.data }
    }
  } catch (error) {
    console.error('加载知识库详情失败:', error)
    // 不显示错误消息，因为基本信息已经显示
  }
}

// 添加文档
const handleAddDocument = (row) => {
  currentKB.value = row
  addDocDialogVisible.value = true
  resetAddDocForm()
}

// 重置添加文档表单
const resetAddDocForm = () => {
  Object.assign(addDocForm, {
    chunk_size: null,
    chunk_overlap: null,
    splitter_type: 'recursive'
  })
  addDocFileList.value = []
}

// 添加文档文件选择
const handleAddDocFileChange = (file, uploadFileList) => {
  console.log('handleAddDocFileChange - file:', file)
  console.log('handleAddDocFileChange - file.raw:', file.raw)
  console.log('handleAddDocFileChange - file.name:', file.name)

  if (file && file.raw) {
    addDocFileList.value = [file]
    console.log('添加文档文件已添加到 addDocFileList')
  } else {
    console.error('添加文档 - 文件对象无效或缺少 raw 属性')
    addDocFileList.value = []
  }
}

// 添加文档文件移除
const handleAddDocFileRemove = () => {
  addDocFileList.value = []
}

// 提交添加文档
const handleAddDocSubmit = async () => {
  if (addDocFileList.value.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  addingDoc.value = true
  try {
    const formData = new FormData()

    // 获取文件对象
    const fileWrapper = addDocFileList.value[0]
    console.log('添加文档 - 文件包装对象:', fileWrapper)
    console.log('添加文档 - file.raw:', fileWrapper.raw)

    // 确保使用正确的文件对象
    const fileToUpload = fileWrapper.raw
    if (!fileToUpload) {
      console.error('添加文档 - 文件对象无效，file.raw 为空')
      ElMessage.error('文件对象无效，请重新选择文件')
      return
    }

    console.log('添加文档 - 实际上传的文件对象:', fileToUpload)
    console.log('添加文档 - 文件名:', fileToUpload.name)
    console.log('添加文档 - 文件类型:', fileToUpload.type)
    console.log('添加文档 - 文件大小:', fileToUpload.size)

    formData.append('file', fileToUpload)

    if (addDocForm.chunk_size) {
      formData.append('chunk_size', addDocForm.chunk_size)
    }
    if (addDocForm.chunk_overlap) {
      formData.append('chunk_overlap', addDocForm.chunk_overlap)
    }
    if (addDocForm.splitter_type) {
      formData.append('splitter_type', addDocForm.splitter_type)
    }

    console.log('添加文档 - FormData 内容:')
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}:`, value)
    }

    await knowledgeBaseApi.addDocumentToKnowledgeBase(currentKB.value.name, formData)

    ElMessage.success('文档添加成功')
    addDocDialogVisible.value = false
    loadKnowledgeBases()
  } catch (error) {
    console.error('添加文档错误:', error)
    ElMessage.error(error.backendMessage || '添加文档失败')
  } finally {
    addingDoc.value = false
  }
}

// 删除知识库
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库 "${row.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await knowledgeBaseApi.deleteKnowledgeBase(row.name)
    ElMessage.success('知识库删除成功')
    loadKnowledgeBases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.backendMessage || '删除知识库失败')
    }
  }
}

// 关闭对话框
const handleClose = () => {
  dialogVisible.value = false
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr || dateStr === 'N/A') return 'N/A'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化数字（添加千分位）
const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString('zh-CN')
}

// 获取分块器类型名称
const getSplitterTypeName = (type) => {
  const typeMap = {
    'recursive': '递归分块',
    'character': '字符分块',
    'markdown': 'Markdown分块',
    'token': 'Token分块'
  }
  return typeMap[type] || type || 'N/A'
}

// 组件挂载时加载支持的文件格式
onMounted(() => {
  loadSupportedFormats()
})
</script>

<style scoped>
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.knowledge-list {
  min-height: 400px;
  padding: 16px 0;
}

.knowledge-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

:deep(.knowledge-table .el-table__header-wrapper) {
  border-radius: 8px 8px 0 0;
}

:deep(.knowledge-table th.el-table__cell) {
  border: none;
}

:deep(.knowledge-table tr:hover > td) {
  background-color: #f5f7fa !important;
}

/* 索引名称单元格 */
.index-name-cell {
  display: flex;
  align-items: center;
}

.index-name-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.index-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.index-name-text {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  word-break: break-word;
}

/* 描述单元格 */
.description-cell {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  padding: 0 8px;
}

/* 统计标签 */
.stat-tag {
  padding: 10px 18px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 6px;
}

.stat-tag .tag-icon {
  font-size: 16px;
  margin-right: 6px;
}

/* 存储大小单元格 */
.size-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.size-icon {
  font-size: 16px;
  color: #409eff;
}

/* 时间单元格 */
.time-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
}

.time-icon {
  font-size: 14px;
  color: #909399;
}

/* 操作按钮 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  font-size: 13px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
}

.view-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

.view-btn:hover {
  background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
}

.upload-btn {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: none;
  color: white;
}

.upload-btn:hover {
  background: linear-gradient(135deg, #e078eb 0%, #d64556 100%);
}

.delete-btn {
  padding: 8px 12px;
}

.delete-btn:hover {
  background-color: #f56c6c;
  border-color: #f56c6c;
}

.upload-area {
  width: 100%;
}

.chunk-params {
  display: flex;
  gap: 12px;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.switch-label {
  margin-left: 12px;
  font-size: 14px;
  color: #606266;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px;
}

:deep(.el-icon--upload) {
  font-size: 67px;
  color: #409eff;
  margin-bottom: 16px;
}

:deep(.el-upload__text) {
  font-size: 14px;
  color: #606266;
}

/* 详情对话框样式 */
.detail-content {
  padding: 8px 0;
}

.detail-section {
  margin-bottom: 28px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  padding: 10px 16px;
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

.detail-descriptions {
  margin-top: 0;
}

:deep(.detail-descriptions .el-descriptions__label) {
  font-weight: 600;
  background-color: #f5f7fa !important;
  color: #303133;
  width: 120px;
}

:deep(.detail-descriptions .el-descriptions__body) {
  background-color: #ffffff;
}

:deep(.detail-descriptions .el-descriptions__cell) {
  padding: 16px 20px;
  line-height: 1.8;
  font-size: 14px;
}

:deep(.detail-descriptions .el-descriptions__content) {
  color: #606266;
}

.tag-icon {
  margin-right: 6px;
  font-size: 16px;
  vertical-align: middle;
}

:deep(.el-tag--large) {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
}

:deep(.el-upload__text em) {
  color: #409eff;
  font-style: normal;
}

:deep(.el-upload__tip) {
  margin-top: 7px;
  font-size: 12px;
  color: #909399;
}
</style>
