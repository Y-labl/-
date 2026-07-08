<template>
  <div class="template-page">
    <div class="page-header">
      <h2 class="page-title">模板管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="uploadTemplate">
          <el-icon><Upload /></el-icon>
          上传模板
        </el-button>
      </div>
    </div>
    
    <!-- 模板分类 -->
    <div class="category-tabs">
      <el-radio-group v-model="currentCategory" @change="filterByCategory">
        <el-radio-button label="all">全部</el-radio-button>
        <el-radio-button label="button">按钮</el-radio-button>
        <el-radio-button label="dialog">对话框</el-radio-button>
        <el-radio-button label="npc">NPC</el-radio-button>
        <el-radio-button label="monster">怪物</el-radio-button>
        <el-radio-button label="item">物品</el-radio-button>
      </el-radio-group>
    </div>
    
    <!-- 模板列表 -->
    <div class="card">
      <div class="template-grid">
        <el-card 
          v-for="template in filteredTemplates" 
          :key="template.id" 
          class="template-card"
          shadow="hover"
        >
          <div class="template-preview">
            <img :src="template.thumbnail || '/placeholder.png'" alt="模板预览" />
          </div>
          <div class="template-info">
            <h4>{{ template.templateName }}</h4>
            <p class="template-category">{{ getCategoryText(template.category) }}</p>
            <p class="template-stats">
              使用 {{ template.usageCount }} 次 | 成功 {{ template.successCount }} 次
            </p>
          </div>
          <div class="template-actions">
            <el-button size="small" type="primary" @click="testTemplate(template)">
              测试
            </el-button>
            <el-button size="small" @click="editTemplate(template)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteTemplate(template)">
              删除
            </el-button>
          </div>
        </el-card>
      </div>
      
      <div v-if="filteredTemplates.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Picture /></el-icon>
        <p class="empty-text">暂无模板</p>
      </div>
    </div>
    
    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传模板" width="500px">
      <el-form ref="uploadFormRef" :model="uploadForm" label-width="100px">
        <el-form-item label="模板名称" prop="templateName">
          <el-input v-model="uploadForm.templateName" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-select v-model="uploadForm.category" placeholder="选择分类">
            <el-option label="按钮" value="button" />
            <el-option label="对话框" value="dialog" />
            <el-option label="NPC" value="npc" />
            <el-option label="怪物" value="monster" />
            <el-option label="物品" value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="匹配阈值">
          <el-slider 
            v-model="uploadForm.matchThreshold" 
            :min="0.5" 
            :max="1" 
            :step="0.01"
            show-input
          />
        </el-form-item>
        <el-form-item label="模板图片">
          <el-upload
            class="template-upload"
            drag
            action="/api/template/upload"
            :auto-upload="false"
            :on-change="handleFileChange"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将图片拖到此处，或<em>点击上传</em>
            </div>
          </el-upload>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>
    
    <!-- 测试对话框 -->
    <el-dialog v-model="showTestDialog" title="测试模板" width="80%">
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="test-preview">
            <h4>模板图片</h4>
            <img :src="currentTestTemplate.thumbnail" alt="模板" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="test-result">
            <h4>匹配结果</h4>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="相似度">
                {{ testResult.similarity }}%
              </el-descriptions-item>
              <el-descriptions-item label="位置">
                X: {{ testResult.x }}, Y: {{ testResult.y }}
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="testResult.found ? 'success' : 'danger'">
                  {{ testResult.found ? '匹配成功' : '未找到' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <el-button type="primary" @click="runTest" style="margin-top: 20px">
              重新测试
            </el-button>
          </div>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const currentCategory = ref('all')
const showUploadDialog = ref(false)
const showTestDialog = ref(false)

const uploadForm = reactive({
  templateName: '',
  category: 'button',
  matchThreshold: 0.85,
  description: '',
  file: null
})

const currentTestTemplate = ref({})
const testResult = ref({
  found: false,
  similarity: 0,
  x: 0,
  y: 0
})

const templateList = ref([
  {
    id: 1,
    templateName: '师门任务图标',
    category: 'button',
    thumbnail: '',
    usageCount: 156,
    successCount: 150,
    matchThreshold: 0.85
  },
  {
    id: 2,
    templateName: '战斗胜利对话框',
    category: 'dialog',
    thumbnail: '',
    usageCount: 89,
    successCount: 85,
    matchThreshold: 0.80
  },
  {
    id: 3,
    templateName: '傲来国NPC',
    category: 'npc',
    thumbnail: '',
    usageCount: 45,
    successCount: 42,
    matchThreshold: 0.85
  },
  {
    id: 4,
    templateName: '大海龟怪物',
    category: 'monster',
    thumbnail: '',
    usageCount: 234,
    successCount: 220,
    matchThreshold: 0.80
  },
  {
    id: 5,
    templateName: '金柳露物品',
    category: 'item',
    thumbnail: '',
    usageCount: 67,
    successCount: 65,
    matchThreshold: 0.90
  }
])

const filteredTemplates = computed(() => {
  if (currentCategory.value === 'all') {
    return templateList.value
  }
  return templateList.value.filter(t => t.category === currentCategory.value)
})

const getCategoryText = (category) => {
  const texts = {
    button: '按钮',
    dialog: '对话框',
    npc: 'NPC',
    monster: '怪物',
    item: '物品'
  }
  return texts[category] || '其他'
}

const filterByCategory = () => {
  // 重新筛选
}

const uploadTemplate = () => {
  showUploadDialog.value = true
}

const handleFileChange = (file) => {
  uploadForm.file = file.raw
}

const handleUpload = () => {
  if (!uploadForm.templateName) {
    ElMessage.warning('请输入模板名称')
    return
  }
  ElMessage.success('模板上传成功')
  showUploadDialog.value = false
}

const testTemplate = (template) => {
  currentTestTemplate.value = template
  showTestDialog.value = true
  runTest()
}

const runTest = () => {
  // 模拟测试结果
  testResult.value = {
    found: Math.random() > 0.3,
    similarity: Math.floor(Math.random() * 20 + 80),
    x: Math.floor(Math.random() * 500 + 100),
    y: Math.floor(Math.random() * 300 + 100)
  }
}

const editTemplate = (template) => {
  ElMessage.info('编辑模板')
}

const deleteTemplate = async (template) => {
  await ElMessageBox.confirm(`确定要删除模板 "${template.templateName}" 吗？`, '提示', { type: 'warning' })
  ElMessage.success('删除成功')
}
</script>

<style scoped lang="scss">
.template-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .page-title {
      font-size: 20px;
      font-weight: bold;
    }
  }
  
  .category-tabs {
    margin-bottom: 20px;
  }
  
  .template-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    
    .template-card {
      .template-preview {
        height: 120px;
        background: #f5f5f5;
        border-radius: 4px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        
        img {
          max-width: 100%;
          max-height: 100%;
        }
      }
      
      .template-info {
        margin-bottom: 10px;
        
        h4 {
          margin: 0 0 5px;
          font-size: 14px;
        }
        
        .template-category {
          margin: 0;
          font-size: 12px;
          color: #409eff;
        }
        
        .template-stats {
          margin: 5px 0 0;
          font-size: 11px;
          color: #999;
        }
      }
      
      .template-actions {
        display: flex;
        gap: 5px;
        
        .el-button {
          flex: 1;
          padding: 5px;
        }
      }
    }
  }
  
  .test-preview,
  .test-result {
    h4 {
      margin: 0 0 10px;
    }
    
    img {
      width: 100%;
      border-radius: 4px;
      background: #000;
    }
  }
}
</style>
