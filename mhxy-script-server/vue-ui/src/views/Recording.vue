<template>
  <div class="recording-page">
    <div class="page-header">
      <h2 class="page-title">录制管理</h2>
      <div class="header-actions">
        <el-button type="success" @click="showStartDialog = true">
          <el-icon><VideoPlay /></el-icon>
          开始录制
        </el-button>
      </div>
    </div>
    
    <!-- 录制控制 -->
    <div class="card recording-control">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="设备状态">
            <template #value>
              <el-tag :type="isRecording ? 'danger' : 'success'">
                {{ isRecording ? '录制中' : '空闲' }}
              </el-tag>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="录制时长" :value="recordingTime" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="文件大小" :value="fileSize + ' MB'" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="帧率" :value="fps + ' FPS'" />
        </el-col>
      </el-row>
      
      <div class="control-buttons">
        <el-button v-if="!isRecording" type="success" size="large" @click="startRecording">
          <el-icon><VideoPlay /></el-icon>
          开始录制
        </el-button>
        <el-button v-else type="danger" size="large" @click="stopRecording">
          <el-icon><VideoPause /></el-icon>
          停止录制
        </el-button>
        <el-button type="warning" size="large" :disabled="!isRecording" @click="pauseRecording">
          {{ isPaused ? '继续' : '暂停' }}
        </el-button>
      </div>
    </div>
    
    <!-- 录制设置 -->
    <div class="card settings-card">
      <div class="card-header">
        <span class="card-title">录制设置</span>
      </div>
      <el-form :inline="true" :model="recordSettings">
        <el-form-item label="设备">
          <el-select v-model="recordSettings.deviceId" placeholder="选择设备">
            <el-option 
              v-for="device in deviceList" 
              :key="device.id" 
              :label="device.deviceName" 
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分辨率">
          <el-select v-model="recordSettings.resolution" placeholder="选择分辨率">
            <el-option label="原画 (1920x1080)" value="1920x1080" />
            <el-option label="高清 (1280x720)" value="1280x720" />
            <el-option label="标清 (854x480)" value="854x480" />
          </el-select>
        </el-form-item>
        <el-form-item label="帧率">
          <el-select v-model="recordSettings.fps" placeholder="选择帧率">
            <el-option label="60 FPS" :value="60" />
            <el-option label="30 FPS" :value="30" />
            <el-option label="15 FPS" :value="15" />
          </el-select>
        </el-form-item>
        <el-form-item label="码率">
          <el-input-number 
            v-model="recordSettings.bitrate" 
            :min="1000000" 
            :max="20000000" 
            :step="1000000"
          />
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 录制历史 -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">录制历史</span>
        <el-button size="small" @click="loadRecordings">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      
      <el-table :data="recordingList" style="width: 100%">
        <el-table-column prop="taskName" label="任务名称" width="180" />
        <el-table-column prop="duration" label="时长" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="fileSize" label="大小" width="100">
          <template #default="{ row }">
            {{ (row.fileSize / 1024 / 1024).toFixed(2) }} MB
          </template>
        </el-table-column>
        <el-table-column prop="resolution" label="分辨率" width="120" />
        <el-table-column prop="fps" label="帧率" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="playRecording(row)">
              播放
            </el-button>
            <el-button link type="success" size="small" @click="downloadRecording(row)">
              下载
            </el-button>
            <el-button link type="danger" size="small" @click="deleteRecording(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="recordingList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><VideoPlay /></el-icon>
        <p class="empty-text">暂无录制记录</p>
      </div>
    </div>
    
    <!-- 开始录制对话框 -->
    <el-dialog v-model="showStartDialog" title="开始录制" width="500px">
      <el-form ref="recordFormRef" :model="recordForm" label-width="100px">
        <el-form-item label="任务名称" prop="taskName">
          <el-input v-model="recordForm.taskName" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="选择设备" prop="deviceId">
          <el-select v-model="recordForm.deviceId" placeholder="选择设备">
            <el-option 
              v-for="device in deviceList" 
              :key="device.id" 
              :label="device.deviceName" 
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="保存路径">
          <el-input v-model="recordForm.outputPath" placeholder="留空使用默认路径" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showStartDialog = false">取消</el-button>
        <el-button type="primary" @click="handleStartRecording">开始</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const showStartDialog = ref(false)
const isRecording = ref(false)
const isPaused = ref(false)
const recordingTime = ref(0)
const fileSize = ref(0)
const fps = ref(30)

let timer = null

const deviceList = ref([
  { id: 1, deviceName: '夜神模拟器' },
  { id: 2, deviceName: '雷电模拟器' },
  { id: 3, deviceName: '小米手机' }
])

const recordSettings = reactive({
  deviceId: 1,
  resolution: '1920x1080',
  fps: 30,
  bitrate: 8000000
})

const recordForm = reactive({
  taskName: '',
  deviceId: 1,
  outputPath: ''
})

const recordingList = ref([
  {
    id: 1,
    taskName: '日常任务_20260708',
    duration: 3600,
    fileSize: 524288000,
    resolution: '1920x1080',
    fps: 30,
    status: 2,
    createTime: '2026-07-08 16:30:00'
  },
  {
    id: 2,
    taskName: '副本_水陆大会',
    duration: 1800,
    fileSize: 262144000,
    resolution: '1280x720',
    fps: 30,
    status: 2,
    createTime: '2026-07-08 15:00:00'
  }
])

const getStatusType = (status) => {
  const types = { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '等待', 1: '录制中', 2: '已完成', 3: '失败' }
  return texts[status] || '未知'
}

const formatDuration = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const loadRecordings = () => {
  ElMessage.success('列表已刷新')
}

const startRecording = () => {
  if (!recordSettings.deviceId) {
    ElMessage.warning('请先选择设备')
    return
  }
  isRecording.value = true
  isPaused.value = false
  recordingTime.value = 0
  fileSize.value = 0
  
  timer = setInterval(() => {
    if (!isPaused.value) {
      recordingTime.value++
      fileSize.value = Math.floor(recordingTime.value * 0.15) // 模拟文件增长
    }
  }, 1000)
  
  ElMessage.success('开始录制')
}

const stopRecording = () => {
  isRecording.value = false
  isPaused.value = false
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  ElMessage.success(`录制完成，时长: ${formatDuration(recordingTime.value)}`)
  loadRecordings()
}

const pauseRecording = () => {
  isPaused.value = !isPaused.value
  ElMessage.info(isPaused.value ? '已暂停' : '继续录制')
}

const handleStartRecording = () => {
  if (!recordForm.taskName) {
    ElMessage.warning('请输入任务名称')
    return
  }
  showStartDialog.value = false
  startRecording()
}

const playRecording = (row) => {
  ElMessage.info('播放功能开发中...')
}

const downloadRecording = (row) => {
  ElMessage.success('开始下载...')
}

const deleteRecording = async (row) => {
  await ElMessageBox.confirm('确定要删除这条录制吗？', '提示', { type: 'warning' })
  ElMessage.success('删除成功')
  loadRecordings()
}
</script>

<style scoped lang="scss">
.recording-page {
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
  
  .recording-control {
    .control-buttons {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-top: 20px;
      
      .el-button {
        padding: 15px 40px;
        font-size: 16px;
      }
    }
  }
  
  .settings-card {
    .el-form-item {
      margin-bottom: 0;
    }
  }
}
</style>
