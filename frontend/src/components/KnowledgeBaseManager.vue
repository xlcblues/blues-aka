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
        <el-button type="primary" @click="showCreateDialog">创建第一个知识库</el-button>
      </el-empty>

      <el-table
        v-else
        :data="knowledgeBases"
        stripe
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column prop="name" label="索引名称" width="180">
          <template #default="{ row }">
            <div class="index-name">
              <el-icon><Reading /></el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <span>{{ row.description || '暂无描述' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="num_documents" label="文档数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.num_documents || 0 }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="size_mb" label="大小" width="100" align="center">
          <template #default="{ row }">
            <span>{{ row.size_mb ? row.size_mb.toFixed(2) + ' MB' : 'N/A' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <span>{{ formatDateTime(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="handleView(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button size="small" @click="handleAddDocument(row)">
                <el-icon><Upload /></el-icon>
                添加文档
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-button-group>
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
                支持格式：PDF、TXT、Markdown、HTML、JSON，最大 16MB
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
                支持格式：PDF、TXT、Markdown、HTML、JSON，最大 16MB
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
      width="600px"
      append-to-body
    >
      <el-descriptions :column="2" border v-if="currentKB">
        <el-descriptions-item label="索引名称">
          {{ currentKB.name }}
        </el-descriptions-item>
        <el-descriptions-item label="文档数量">
          {{ currentKB.num_documents || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="存储大小">
          {{ currentKB.size_mb ? currentKB.size_mb.toFixed(2) + ' MB' : 'N/A' }}
        </el-descriptions-item>
        <el-descriptions-item label="向量存储类型">
          {{ currentKB.store_type || 'N/A' }}
        </el-descriptions-item>
        <el-descriptions-item label="嵌入模型">
          {{ currentKB.embedding_model || 'N/A' }}
        </el-descriptions-item>
        <el-descriptions-item label="存储路径">
          <el-text truncated>{{ currentKB.path || 'N/A' }}</el-text>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" span="2">
          {{ formatDateTime(currentKB.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间" span="2">
          {{ formatDateTime(currentKB.updated_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" span="2">
          {{ currentKB.description || '暂无描述' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Reading,
  View,
  Upload,
  Delete,
  UploadFilled
} from '@element-plus/icons-vue'
import { knowledgeBaseApi } from '../api/knowledgeBase'

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
const handleView = (row) => {
  currentKB.value = row
  detailDialogVisible.value = true
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
</script>

<style scoped>
.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.knowledge-list {
  min-height: 300px;
}

.index-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
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
