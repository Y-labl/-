<template>
  <div class="template-page">
    <div class="page-header">
      <h2 class="page-title">模板管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openUploadDialog">
          <el-icon><Upload /></el-icon>
          上传模板
        </el-button>
      </div>
    </div>

    <div class="category-tabs">
      <el-radio-group v-model="currentCategory" @change="loadTemplates">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="button">按钮</el-radio-button>
        <el-radio-button label="dialog">对话框</el-radio-button>
        <el-radio-button label="npc">NPC</el-radio-button>
        <el-radio-button label="monster">怪物</el-radio-button>
        <el-radio-button label="item">物品</el-radio-button>
      </el-radio-group>
    </div>

    <div class="card">
      <div class="template-grid">
        <el-card v-for="t in templateList" :key="t.id" class="template-card" shadow="hover">
          <div class="template-preview">
            <img :src="t.thumbnail" alt="模板预览" @error="e => e.target.style.display='none'" />
          </div>
          <div class="template-info">
            <h4>{{ t.templateName }}</h4>
            <p class="template-category">{{ getCategoryText(t.category) }}</p>
            <p class="template-stats">{{ t.width || '?' }}x{{ t.height || '?' }} | {{ formatSize(t.fileSize) }}</p>
          </div>
          <div class="template-actions">
            <el-button size="small" type="primary" @click="openEditDialog(t)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteTemplate(t)">删除</el-button>
            <el-button size="small" type="success" @click="openTestDialog(t)">测试</el-button>
          </div>
        </el-card>
      </div>
      <div v-if="templateList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Picture /></el-icon>
        <p class="empty-text">暂无模板</p>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传模板" width="500px">
      <el-form label-width="80px">
        <el-form-item label="模板名称">
          <el-input v-model="uploadForm.templateName" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="uploadForm.category">
            <el-option label="按钮" value="button" />
            <el-option label="对话框" value="dialog" />
            <el-option label="NPC" value="npc" />
            <el-option label="怪物" value="monster" />
            <el-option label="物品" value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配阈值">
          <el-slider v-model="uploadForm.matchThreshold" :min="0.5" :max="1" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="模板图片">
          <el-upload drag :auto-upload="false" :on-change="handleFileChange" accept="image/*">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽或点击上传</div>
          </el-upload>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :disabled="!uploadForm.file">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑模板" width="450px">
      <el-form label-width="80px" v-if="editForm.id">
        <el-form-item label="模板名称">
          <el-input v-model="editForm.templateName" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editForm.category">
            <el-option label="按钮" value="button" />
            <el-option label="对话框" value="dialog" />
            <el-option label="NPC" value="npc" />
            <el-option label="怪物" value="monster" />
            <el-option label="物品" value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配阈值">
          <el-slider v-model="editForm.matchThreshold" :min="0.5" :max="1" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 测试匹配 -->
    <el-dialog v-model="showTestDialog" title="模板匹配测试" width="900px" class="test-dialog">
      <div class="test-body">
        <!-- 选择设备 -->
        <div class="test-actions">
          <el-select v-model="testDeviceId" placeholder="选择设备" style="width:100%">
            <el-option v-for="dev in testDevices" :key="dev.id" :label="dev.deviceName" :value="dev.id" />
          </el-select>
          <el-button type="primary" @click="runDeviceMatchTest" :loading="testRunning" :disabled="!testDeviceId" style="margin-top:12px;width:100%">
            截图并匹配
          </el-button>
        </div>

        <!-- 模板图片与目标图片并列 -->
        <div class="image-preview-row">
          <div class="preview-panel template-preview-panel">
            <div class="panel-title">模板图片</div>
            <div class="preview-image-wrapper">
              <img :src="testTemplate.thumbnail" class="preview-image" />
            </div>
            <div class="preview-meta">
              <span class="template-name">{{ testTemplate.templateName }}</span>
              <span class="template-size">{{ testTemplate.width || '?' }}x{{ testTemplate.height || '?' }}</span>
            </div>
          </div>
          <div class="preview-panel uploaded-preview-panel">
            <div class="panel-title">目标图片</div>
            <div class="preview-image-wrapper upload-wrapper">
              <el-upload
                v-if="!testTargetUrl"
                drag
                :auto-upload="false"
                :on-change="handleTestFileChange"
                accept="image/*"
                class="preview-upload"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">拖拽或点击上传目标图片</div>
              </el-upload>
              <img v-else :src="testTargetUrl" class="preview-image" />
            </div>
            <el-button type="primary" @click="runMatchTest" :loading="testRunning" :disabled="!testFile" style="margin-top:12px;width:100%">
              开始匹配
            </el-button>
          </div>
        </div>


        <!-- 匹配结果 -->
        <div v-if="testResult" class="test-result">
          <div class="panel-title">匹配结果</div>

          <div class="result-status">
            <el-tag :type="testResult.data.matched ? 'success' : 'danger'" size="large">
              {{ testResult.data.matched ? '匹配成功' : '未匹配' }}
            </el-tag>
              <span class="similarity-text">相似度：{{ (testResult.data.similarity * 100).toFixed(2) }}%</span>
              <span class="duration-text">耗时：{{ testDuration }}ms</span>
          </div>

          <!-- 目标图片 + 矩形标注 -->
          <div class="result-image-wrapper" ref="resultImageWrap">
            <img
              v-if="testTargetUrl"
              :src="testTargetUrl"
              class="result-image"
              @load="onResultImageLoad"
              ref="resultImage"
            />
            <div
              v-for="(pt, idx) in (testResult.data.matchPoints || [])"
              :key="'rect-' + idx"
              class="match-rect"
              :style="getRectStyle(pt)"
            />
          </div>

          <div v-if="testResult.data.matched" class="match-positions">
            <div v-for="(pt, idx) in testResult.data.matchPoints" :key="idx" class="match-position-item">
              位置{{ idx + 1 }}：中心 ({{ pt.x }}, {{ pt.y }})
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { getDeviceList } from '@/api/device'

const currentCategory = ref('')
const templateList = ref([])
const showUploadDialog = ref(false)
const showEditDialog = ref(false)

const uploadForm = reactive({
  templateName: '', category: 'monster', matchThreshold: 0.75, description: '', file: null
})

const editForm = reactive({
  id: null, templateName: '', category: '', matchThreshold: 0.75, description: ''
})


// 测试相关状态
const showTestDialog = ref(false)
const testTemplate = reactive({ id: null, templateName: '', thumbnail: '', width: 0, height: 0 })
const testFile = ref(null)
const testTargetUrl = ref(null)
const testDeviceId = ref(null)
const testDevices = ref([])
const testRunning = ref(false)
const testThreshold = ref(0.75)
const testResult = ref(null)
const testDuration = ref(0)
const resultImageSize = reactive({ width: 0, height: 0 })
const resultImage = ref(null)
const resultImageWrap = ref(null)

const getCategoryText = (cat) => {
  const m = { button: '按钮', dialog: '对话框', npc: 'NPC', monster: '怪物', item: '物品' }
  return m[cat] || cat
}

const formatSize = (bytes) => {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1048576).toFixed(1) + 'MB'
}

const loadTemplates = async () => {
  try {
    const params = currentCategory.value ? { category: currentCategory.value } : {}
    const res = await axios.get('/api/template/list', { params })
    templateList.value = res.data.data || []
  } catch (e) { ElMessage.error('加载模板失败') }
}

const handleFileChange = (file) => { uploadForm.file = file.raw }

const openUploadDialog = () => {
  uploadForm.templateName = ''
  uploadForm.category = 'monster'
  uploadForm.matchThreshold = 0.85
  uploadForm.description = ''
  uploadForm.file = null
  showUploadDialog.value = true
}

const handleUpload = async () => {
  if (!uploadForm.templateName) { ElMessage.warning('请输入模板名称'); return }
  const fd = new FormData()
  fd.append('file', uploadForm.file)
  fd.append('templateName', uploadForm.templateName)
  fd.append('category', uploadForm.category)
  fd.append('matchThreshold', uploadForm.matchThreshold)
  fd.append('description', uploadForm.description || '')
  try {
    await axios.post('/api/template/upload', fd)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    loadTemplates()
  } catch (e) { ElMessage.error('上传失败') }
}

const openEditDialog = (t) => {
  editForm.id = t.id
  editForm.templateName = t.templateName
  editForm.category = t.category
  editForm.matchThreshold = t.matchThreshold || 0.85
  editForm.description = t.description || ''
  showEditDialog.value = true
}

const handleEdit = async () => {
  try {
    await axios.put('/api/template/' + editForm.id, {
      templateName: editForm.templateName,
      category: editForm.category,
      matchThreshold: editForm.matchThreshold,
      description: editForm.description
    })
    ElMessage.success('保存成功')
    showEditDialog.value = false
    loadTemplates()
  } catch (e) { ElMessage.error('保存失败') }
}

const deleteTemplate = async (t) => {
  try {
    await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
    await axios.delete('/api/template/' + t.id)
    ElMessage.success('已删除')
    loadTemplates()
  } catch (e) {}
}


const openTestDialog = async (t) => {
  testTemplate.id = t.id
  testTemplate.templateName = t.templateName
  testTemplate.thumbnail = t.thumbnail
  testTemplate.width = t.width || 0
  testTemplate.height = t.height || 0
  testFile.value = null
  testTargetUrl.value = null
  testDeviceId.value = null
  testResult.value = null
  // 加载设备列表
  try {
    const res = await getDeviceList()
    testDevices.value = res.data || []
  } catch (e) { testDevices.value = [] }
  showTestDialog.value = true
}

const handleTestFileChange = (file) => {
  testFile.value = file.raw
  testTargetUrl.value = URL.createObjectURL(file.raw)
}

const runMatchTest = async () => {
  if (!testFile.value) { ElMessage.warning('请先选择目标图片'); return }
  testRunning.value = true
  const t0 = performance.now()
  try {
    const fd = new FormData()
    fd.append('file', testFile.value)
    const res = await axios.post('/api/template/' + testTemplate.id + '/match', fd, { timeout: 30000 })
    testResult.value = res.data
    if (testResult.value.data?.matched) {
      ElMessage.success('匹配成功！')
    } else {
      ElMessage.warning('未找到匹配位置')
    }
  } catch (e) { ElMessage.error(e.code === 'ECONNABORTED' ? '请求超时' : '匹配失败') }
}

const runDeviceMatchTest = async () => {
  if (!testDeviceId.value) { ElMessage.warning('请选择设备'); return }
  testRunning.value = true
  const t0 = performance.now()
  try {
    const fd = new FormData()
    fd.append('deviceId', testDeviceId.value)
    const res = await axios.post('/api/template/' + testTemplate.id + '/match-device', fd, { timeout: 30000 })
    testResult.value = res.data
    if (res.data.data?.screenshotBase64) {
      testTargetUrl.value = res.data.data.screenshotBase64
    }
    if (res.data.data?.matched) {
      ElMessage.success('匹配成功！')
    } else {
      ElMessage.warning('未找到匹配位置')
    }
  } catch (e) { ElMessage.error(e.code === 'ECONNABORTED' ? '请求超时' : '匹配失败') }
}
const onResultImageLoad = () => {
  if (resultImage.value) {
    resultImageSize.width = resultImage.value.offsetWidth
    resultImageSize.height = resultImage.value.offsetHeight
  }
}

const getRectStyle = (pt) => {
  if (!testResult.value?.data || !resultImageSize.width) return {}
  const data = testResult.value.data
  const scaleX = resultImageSize.width / data.imageWidth
  const scaleY = resultImageSize.height / data.imageHeight
  const tw = data.templateWidth * scaleX
  const th = data.templateHeight * scaleY
  const left = (pt.x - data.templateWidth / 2) * scaleX
  const top = (pt.y - data.templateHeight / 2) * scaleY
  return {
    position: 'absolute',
    left: left + 'px',
    top: top + 'px',
    width: tw + 'px',
    height: th + 'px',
    border: '3px solid #ffd700',
    background: 'rgba(255, 215, 0, 0.2)',
    boxShadow: '0 0 8px rgba(255, 215, 0, 0.5)',
    pointerEvents: 'none'
}
}
onMounted(() => { loadTemplates() })
</script>

<style scoped lang="scss">
.template-page {
  .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
    .page-title { font-size: 20px; font-weight: bold; }
  }
  .category-tabs { margin-bottom: 20px; }
  .template-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;
    .template-card {
      .template-preview { height: 120px; background: #f5f5f5; border-radius: 4px; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; overflow: hidden;
        img { max-width: 100%; max-height: 100%; }
      }
      .template-info { margin-bottom: 10px;
        h4 { margin: 0 0 5px; font-size: 14px; }
        .template-category { margin: 0; font-size: 12px; color: #409eff; }
        .template-stats { margin: 5px 0 0; font-size: 11px; color: #999; }
      }
      .template-actions { display: flex; gap: 5px; .el-button { flex: 1; padding: 5px; } }
    }
  }
}
.test-dialog {
  .test-body {
    display: flex; flex-direction: column; gap: 20px;
    .panel-title { font-size: 14px; font-weight: bold; margin-bottom: 10px; color: #333; }

    .test-actions {
      .el-select { width: 100%; }
    }

    .image-preview-row {
      display: flex; gap: 20px;
      .preview-panel {
        flex: 1; min-width: 0;
        .preview-image-wrapper {
          display: flex; align-items: center; justify-content: center;
          height: 220px; border: 1px solid #eee; border-radius: 4px; overflow: hidden; background: #f5f5f5;
          .preview-image { max-width: 100%; max-height: 100%; object-fit: contain; }
          .preview-empty { color: #999; font-size: 13px; }
        }
        .preview-image-wrapper.upload-wrapper {
          padding: 0;
          .preview-upload {
            width: 100%; height: 100%;
            :deep(.el-upload) { width: 100%; height: 100%; }
            :deep(.el-upload-dragger) {
              width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box;
              .el-icon--upload { font-size: 32px; color: #c0c4cc; margin: 0 0 10px; }
              .el-upload__text { font-size: 13px; color: #999; line-height: 1.5; }
            }
          }
        }
        .preview-meta {
          margin-top: 8px; font-size: 12px; color: #666; display: flex; flex-direction: column; gap: 4px;
          .template-name { font-weight: 500; color: #333; }
          .template-size { color: #999; }
        }
      }
    }

    .test-result {
      .result-status { display: flex; align-items: center; gap: 12px; margin-bottom: 10px;
        .similarity-text { font-size: 14px; color: #666; font-weight: 500; }
      }
      .result-image-wrapper {
        position: relative; display: inline-block; max-width: 100%; border: 1px solid #eee; border-radius: 4px; overflow: hidden;
        .result-image { display: block; max-width: 100%; max-height: 500px; }
      }
      .match-positions { margin-top: 10px;
        .match-position-item { font-size: 13px; color: #409eff; padding: 2px 0; }
      }
    }
  }
}

</style>
