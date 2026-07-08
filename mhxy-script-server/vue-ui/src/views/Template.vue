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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const currentCategory = ref('')
const templateList = ref([])
const showUploadDialog = ref(false)
const showEditDialog = ref(false)

const uploadForm = reactive({
  templateName: '', category: 'monster', matchThreshold: 0.85, description: '', file: null
})

const editForm = reactive({
  id: null, templateName: '', category: '', matchThreshold: 0.85, description: ''
})

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
</style>