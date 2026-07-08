<template>
  <div class="screenshot-page">
    <div class="page-header">
      <h2 class="page-title">截图管理</h2>
      <div class="header-actions">
        <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 200px">
          <el-option 
            v-for="device in deviceList" 
            :key="device.id" 
            :label="device.deviceName" 
            :value="device.id"
          />
        </el-select>
        <el-button type="primary" @click="captureFullScreen">
          <el-icon><Camera /></el-icon>
          全屏截图
        </el-button>
      </div>
    </div>
    
    <el-row :gutter="20">
      <!-- 截图预览区 -->
      <el-col :span="16">
        <div class="card">
          <div class="card-header">
            <span class="card-title">屏幕预览</span>
            <div class="header-tools">
              <el-button size="small" @click="refreshPreview">
                <el-icon><Refresh /></el-icon>
              </el-button>
              <el-button size="small" type="primary" @click="captureNow">
                <el-icon><Camera /></el-icon>
                截图
              </el-button>
            </div>
          </div>
          <div class="preview-container">
            <div class="screen-preview" @click="handleRegionSelect">
              <img v-if="currentScreenshot" :src="currentScreenshot" alt="屏幕预览" />
              <div v-else class="preview-placeholder">
                <el-icon :size="64"><VideoCamera /></el-icon>
                <p>请先选择设备并连接</p>
              </div>
            </div>
            
            <!-- 区域选择 -->
            <div v-if="regionSelecting" class="region-overlay">
              <div 
                class="region-box" 
                :style="regionStyle"
                @mousedown="startRegionSelect"
              />
            </div>
          </div>
          
          <!-- 区域截图参数 -->
          <div class="region-form" v-if="regionSelecting">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="X坐标">
                  <el-input-number v-model="region.x" :min="0" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="Y坐标">
                  <el-input-number v-model="region.y" :min="0" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="宽度">
                  <el-input-number v-model="region.width" :min="1" />
                </el-form-item>
              </el-col>
              <el-col :span="6">
                <el-form-item label="高度">
                  <el-input-number v-model="region.height" :min="1" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-button type="success" @click="captureRegion">截取区域</el-button>
          </div>
        </div>
      </el-col>
      
      <!-- 截图列表 -->
      <el-col :span="8">
        <div class="card">
          <div class="card-header">
            <span class="card-title">截图历史</span>
            <el-button size="small" link type="primary" @click="loadScreenshots">
              刷新
            </el-button>
          </div>
          
          <div class="screenshot-list">
            <div 
              v-for="shot in screenshotList" 
              :key="shot.id" 
              class="screenshot-item"
              @click="previewScreenshot(shot)"
            >
              <img :src="shot.thumbnail" alt="缩略图" />
              <div class="screenshot-info">
                <p class="shot-name">{{ shot.fileName }}</p>
                <p class="shot-time">{{ shot.createTime }}</p>
              </div>
              <div class="screenshot-actions">
                <el-button size="small" link type="primary" @click.stop="viewScreenshot(shot)">
                  查看
                </el-button>
                <el-button size="small" link type="danger" @click.stop="deleteScreenshot(shot)">
                  删除
                </el-button>
              </div>
            </div>
            
            <div v-if="screenshotList.length === 0" class="empty-state">
              <p>暂无截图</p>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 截图预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="截图预览" width="80%">
      <img :src="previewImage" alt="截图预览" style="width: 100%" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const selectedDevice = ref(null)
const deviceList = ref([
  { id: 1, deviceName: '夜神模拟器' },
  { id: 2, deviceName: '雷电模拟器' },
  { id: 3, deviceName: '小米手机' }
])

const currentScreenshot = ref(null)
const screenshotList = ref([])
const showPreviewDialog = ref(false)
const previewImage = ref('')
const regionSelecting = ref(false)

const region = reactive({
  x: 0,
  y: 0,
  width: 200,
  height: 200
})

const regionStyle = computed(() => ({
  left: region.x + 'px',
  top: region.y + 'px',
  width: region.width + 'px',
  height: region.height + 'px'
}))

const captureFullScreen = () => {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择设备')
    return
  }
  ElMessage.success('全屏截图已保存')
  // 模拟截图
  loadScreenshots()
}

const captureNow = () => {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择设备')
    return
  }
  ElMessage.success('截图成功')
}

const refreshPreview = () => {
  ElMessage.success('画面已刷新')
}

const handleRegionSelect = () => {
  regionSelecting.value = !regionSelecting.value
}

const startRegionSelect = () => {
  // 开始区域选择
}

const captureRegion = () => {
  ElMessage.success(`区域截图成功: ${region.x}, ${region.y}, ${region.width}x${region.height}`)
  regionSelecting.value = false
}

const loadScreenshots = () => {
  // 模拟截图列表
  screenshotList.value = [
    { id: 1, fileName: 'screen_20260708_01.png', thumbnail: '', createTime: '2026-07-08 17:00' },
    { id: 2, fileName: 'screen_20260708_02.png', thumbnail: '', createTime: '2026-07-08 16:50' },
    { id: 3, fileName: 'screen_20260708_03.png', thumbnail: '', createTime: '2026-07-08 16:40' }
  ]
}

const previewScreenshot = (shot) => {
  currentScreenshot.value = shot.thumbnail || shot.url
}

const viewScreenshot = (shot) => {
  previewImage.value = shot.thumbnail || shot.url
  showPreviewDialog.value = true
}

const deleteScreenshot = async (shot) => {
  await ElMessageBox.confirm('确定要删除这张截图吗？', '提示', { type: 'warning' })
  ElMessage.success('删除成功')
  loadScreenshots()
}

// 初始化
loadScreenshots()
</script>

<style scoped lang="scss">
.screenshot-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .page-title {
      font-size: 20px;
      font-weight: bold;
    }
    
    .header-actions {
      display: flex;
      gap: 10px;
    }
  }
  
  .preview-container {
    position: relative;
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    
    .screen-preview {
      width: 100%;
      min-height: 400px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      img {
        max-width: 100%;
        max-height: 100%;
      }
      
      .preview-placeholder {
        color: #666;
        text-align: center;
        
        p {
          margin-top: 10px;
        }
      }
    }
    
    .region-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.3);
      
      .region-box {
        position: absolute;
        border: 2px dashed #409eff;
        background: rgba(64, 158, 255, 0.2);
        cursor: move;
      }
    }
  }
  
  .region-form {
    margin-top: 20px;
    padding: 15px;
    background: #f5f5f5;
    border-radius: 8px;
    
    .el-form-item {
      margin-bottom: 0;
    }
  }
  
  .screenshot-list {
    max-height: 500px;
    overflow-y: auto;
    
    .screenshot-item {
      display: flex;
      align-items: center;
      padding: 10px;
      border-bottom: 1px solid #eee;
      cursor: pointer;
      
      &:hover {
        background: #f5f5f5;
      }
      
      img {
        width: 60px;
        height: 40px;
        object-fit: cover;
        border-radius: 4px;
        background: #000;
      }
      
      .screenshot-info {
        flex: 1;
        margin-left: 10px;
        
        .shot-name {
          margin: 0;
          font-size: 13px;
        }
        
        .shot-time {
          margin: 5px 0 0;
          font-size: 12px;
          color: #999;
        }
      }
      
      .screenshot-actions {
        display: flex;
        gap: 5px;
      }
    }
  }
}
</style>
