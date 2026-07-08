<template>
  <div class="view-page">
    <div class="page-header">
      <h2 class="page-title">观看画面</h2>
      <div class="header-actions">
        <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 200px">
          <el-option 
            v-for="device in deviceList" 
            :key="device.id" 
            :label="device.deviceName" 
            :value="device.id"
          />
        </el-select>
        <el-button :type="isConnected ? 'danger' : 'success'" @click="toggleConnection">
          {{ isConnected ? '断开连接' : '连接设备' }}
        </el-button>
      </div>
    </div>
    
    <el-row :gutter="20">
      <!-- 视频画面 -->
      <el-col :span="18">
        <div class="card video-card">
          <div class="video-container" @click="handleVideoClick">
            <video 
              ref="videoRef"
              class="video-player"
              autoplay
              playsinline
            />
            
            <div v-if="!isConnected" class="video-placeholder">
              <el-icon :size="80"><VideoCamera /></el-icon>
              <p>请选择设备并连接</p>
            </div>
            
            <!-- 控制栏 -->
            <div v-if="isConnected" class="video-controls">
              <div class="control-left">
                <span class="device-name">{{ currentDevice?.deviceName }}</span>
              </div>
              <div class="control-center">
                <el-button-group>
                  <el-button @click="togglePlay">
                    <el-icon v-if="isPlaying"><VideoPause /></el-icon>
                    <el-icon v-else><VideoPlay /></el-icon>
                  </el-button>
                </el-button-group>
              </div>
              <div class="control-right">
                <el-dropdown @command="handleQualityChange">
                  <span class="quality-label">
                    {{ qualityLabels[videoQuality] }}
                    <el-icon><ArrowDown /></el-icon>
                  </span>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="original">原画</el-dropdown-item>
                      <el-dropdown-item command="high">高清</el-dropdown-item>
                      <el-dropdown-item command="medium">标清</el-dropdown-item>
                      <el-dropdown-item command="low">流畅</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </div>
      </el-col>
      
      <!-- 控制面板 -->
      <el-col :span="6">
        <div class="card control-panel">
          <div class="card-header">
            <span class="card-title">控制面板</span>
          </div>
          
          <!-- 设备信息 -->
          <div class="info-section">
            <h4>设备信息</h4>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="设备名称">
                {{ currentDevice?.deviceName || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="分辨率">
                {{ currentDevice?.screenWidth }}x{{ currentDevice?.screenHeight }}
              </el-descriptions-item>
              <el-descriptions-item label="连接方式">
                scrcpy
              </el-descriptions-item>
            </el-descriptions>
          </div>
          
          <!-- 鼠标控制 -->
          <div class="control-section">
            <h4>鼠标控制</h4>
            <div class="control-grid">
              <el-button @click="sendAction('click', { x: -50, y: 0 })">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button @click="sendAction('click', { x: 0, y: -50 })">
                <el-icon><ArrowUp /></el-icon>
              </el-button>
              <el-button @click="sendAction('click', { x: 0, y: 50 })">
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <el-button @click="sendAction('click', { x: 50, y: 0 })">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
            </div>
            <div class="click-buttons">
              <el-button type="primary" @click="sendAction('leftClick')">左键</el-button>
              <el-button type="warning" @click="sendAction('rightClick')">右键</el-button>
              <el-button type="success" @click="sendAction('doubleClick')">双击</el-button>
            </div>
          </div>
          
          <!-- 快捷操作 -->
          <div class="control-section">
            <h4>快捷操作</h4>
            <el-space wrap>
              <el-button size="small" @click="sendAction('home')">Home</el-button>
              <el-button size="small" @click="sendAction('back')">返回</el-button>
              <el-button size="small" @click="sendAction('power')">电源</el-button>
              <el-button size="small" @click="sendAction('volumeUp')">音量+</el-button>
              <el-button size="small" @click="sendAction('volumeDown')">音量-</el-button>
            </el-space>
          </div>
          
          <!-- 文字输入 -->
          <div class="control-section">
            <h4>文字输入</h4>
            <el-input 
              v-model="inputText" 
              placeholder="输入文字"
              @keyup.enter="sendText"
            >
              <template #append>
                <el-button @click="sendText">发送</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 截图预览 -->
    <div class="card screenshot-preview">
      <div class="card-header">
        <span class="card-title">实时画面</span>
        <el-button size="small" type="primary" @click="quickScreenshot">
          <el-icon><Camera /></el-icon>
          截图
        </el-button>
      </div>
      <div class="preview-grid">
        <img v-for="i in 4" :key="i" :src="`/api/screenshot/thumbnail?time=${Date.now()}`" alt="预览" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const deviceList = ref([
  { id: 1, deviceName: '夜神模拟器', screenWidth: 1280, screenHeight: 720 },
  { id: 2, deviceName: '雷电模拟器', screenWidth: 1920, screenHeight: 1080 },
  { id: 3, deviceName: '小米手机', screenWidth: 1080, screenHeight: 2400 }
])

const selectedDevice = ref(null)
const isConnected = ref(false)
const isPlaying = ref(true)
const videoQuality = ref('original')
const inputText = ref('')
const videoRef = ref(null)

const qualityLabels = {
  original: '原画',
  high: '高清',
  medium: '标清',
  low: '流畅'
}

const currentDevice = computed(() => {
  return deviceList.value.find(d => d.id === selectedDevice.value)
})

const toggleConnection = async () => {
  if (!selectedDevice.value) {
    ElMessage.warning('请先选择设备')
    return
  }
  
  if (isConnected.value) {
    isConnected.value = false
    ElMessage.success('已断开连接')
  } else {
    isConnected.value = true
    ElMessage.success('连接成功')
  }
}

const togglePlay = () => {
  isPlaying.value = !isPlaying.value
}

const handleQualityChange = (quality) => {
  videoQuality.value = quality
  ElMessage.success(`已切换到${qualityLabels[quality]}`)
}

const handleVideoClick = () => {
  // 视频点击事件
}

const sendAction = (action, params = {}) => {
  ElMessage.success(`发送动作: ${action}`)
}

const sendText = () => {
  if (inputText.value) {
    ElMessage.success(`发送文字: ${inputText.value}`)
    inputText.value = ''
  }
}

const quickScreenshot = () => {
  ElMessage.success('截图成功')
}
</script>

<style scoped lang="scss">
.view-page {
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
  
  .video-card {
    .video-container {
      position: relative;
      background: #000;
      border-radius: 8px;
      overflow: hidden;
      aspect-ratio: 16/9;
      
      .video-player {
        width: 100%;
        height: 100%;
        object-fit: contain;
      }
      
      .video-placeholder {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #666;
        
        p {
          margin-top: 15px;
        }
      }
      
      .video-controls {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 50px;
        background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        opacity: 0;
        transition: opacity 0.3s;
        
        &:hover {
          opacity: 1;
        }
        
        .device-name {
          color: #fff;
          font-size: 14px;
        }
        
        .quality-label {
          color: #fff;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 5px;
        }
      }
    }
  }
  
  .control-panel {
    .card-header {
      margin-bottom: 15px;
    }
    
    .info-section,
    .control-section {
      margin-bottom: 20px;
      
      h4 {
        font-size: 14px;
        margin: 0 0 10px;
        color: #333;
      }
    }
    
    .control-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 5px;
      width: 150px;
      margin: 0 auto 10px;
    }
    
    .click-buttons {
      display: flex;
      gap: 10px;
      justify-content: center;
    }
  }
  
  .screenshot-preview {
    margin-top: 20px;
    
    .preview-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      
      img {
        width: 100%;
        aspect-ratio: 16/9;
        object-fit: cover;
        border-radius: 4px;
        background: #000;
      }
    }
  }
}
</style>
