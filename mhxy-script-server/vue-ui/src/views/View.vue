<template>
  <div class="view-page">
    <div class="page-header">
      <h2 class="page-title">观看画面</h2>
      <div class="header-actions">
        <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 200px" @change="onDeviceChange">
          <el-option v-for="device in onlineDevices" :key="device.id" :label="device.deviceName" :value="device.id" />
        </el-select>
        <el-button @click="refreshPreview" :loading="refreshing">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="18">
        <div class="card">
          <div class="preview-container">
            <img v-if="currentScreenshot" :src="currentScreenshot" alt="实时画面" class="preview-img" />
            <div v-else class="preview-placeholder">
              <el-icon v-if="!loadingShot" :size="80"><VideoCamera /></el-icon>
              <el-icon v-else class="is-loading" :size="40"><Loading /></el-icon>
              <p>{{ loadingShot ? '正在获取画面...' : (selectedDevice ? '点击刷新获取画面' : '请先选择在线设备') }}</p>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="6">
        <div class="card control-panel">
          <div class="card-header"><span class="card-title">设备信息</span></div>
          <el-descriptions :column="1" border size="small" v-if="currentDevice">
            <el-descriptions-item label="设备名称">{{ currentDevice.deviceName }}</el-descriptions-item>
            <el-descriptions-item label="分辨率">{{ currentDevice.screenWidth || '?' }} x {{ currentDevice.screenHeight || '?' }}</el-descriptions-item>
            <el-descriptions-item label="序列号">{{ currentDevice.deviceId || '-' }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="currentDevice.status === 1 ? 'success' : 'warning'" size="small">
                {{ currentDevice.status === 1 ? '在线' : '使用中' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <div v-else class="empty-state"><p>请选择设备</p></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getDeviceList, getDeviceScreenshot } from '@/api/device'

const selectedDevice = ref(null)
const deviceList = ref([])
const currentScreenshot = ref(null)
const refreshing = ref(false)
const loadingShot = ref(false)
let autoRefreshTimer = null

const onlineDevices = computed(() =>
  deviceList.value.filter(d => d.status === 1 || d.status === 2)
)

const currentDevice = computed(() =>
  deviceList.value.find(d => d.id === selectedDevice.value)
)

const fetchScreenshot = async () => {
  if (!selectedDevice.value) return
  loadingShot.value = true
  try {
    const res = await getDeviceScreenshot(selectedDevice.value)
    if (res.data && res.data.base64) currentScreenshot.value = res.data.base64
  } catch (e) {}
  finally { loadingShot.value = false }
}

const onDeviceChange = () => {
  currentScreenshot.value = null
  if (autoRefreshTimer) clearInterval(autoRefreshTimer)
  if (selectedDevice.value) {
    fetchScreenshot()
    autoRefreshTimer = setInterval(() => {
      if (document.visibilityState === 'visible') fetchScreenshot()
    }, 3000)
  }
}

const refreshPreview = () => fetchScreenshot()

const loadDevices = async () => {
  try {
    const res = await getDeviceList()
    deviceList.value = res.data || []
  } catch (e) {}
}

onMounted(() => { loadDevices() })
onUnmounted(() => { if (autoRefreshTimer) clearInterval(autoRefreshTimer) })
</script>

<style scoped lang="scss">
.view-page {
  .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
    .page-title { font-size: 20px; font-weight: bold; }
    .header-actions { display: flex; gap: 10px; }
  }
  .preview-container {
    background: #1a1a2e; border-radius: 8px; overflow: hidden;
    display: flex; align-items: center; justify-content: center;
    min-height: 500px;
    .preview-img { width: 100%; object-fit: contain; }
    .preview-placeholder { color: #666; text-align: center;
      p { margin-top: 15px; }
    }
  }
  .control-panel {
    .empty-state { padding: 40px 0; text-align: center; color: #999; }
  }
}
</style>