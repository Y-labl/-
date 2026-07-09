<template>
  <div class="devices-page">
    <div class="page-header">
      <h2 class="page-title">设备管理</h2>
      <div class="header-actions">
        <el-button type="warning" @click="openScanDialog" :loading="scanning">
          <el-icon><Search /></el-icon>
          扫描设备
        </el-button>
        <el-button type="primary" @click="loadDevices">
          <el-icon><Refresh /></el-icon>
          刷新列表
        </el-button>
        <el-button type="success" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          手动添加
        </el-button>
      </div>
    </div>

    <!-- Device cards -->
    <div class="card">
      <el-row :gutter="20">
        <el-col
          v-for="device in deviceList"
          :key="device.id"
          :span="6"
          class="device-col"
        >
          <el-card class="device-card" shadow="hover">
            <div class="device-header">
              <el-icon class="device-icon" :class="device.deviceType === 'windows' ? 'windows' : 'mobile'">
                <Monitor v-if="device.deviceType === 'windows'" />
                <Iphone v-else />
              </el-icon>
              <div class="device-info">
                <div class="device-title">
                  <h4>{{ device.deviceName }}</h4>
                  <el-button size="small" :icon="Edit" circle @click.stop="handleEditTitle(device)" class="edit-title-btn" />
                </div>
                <p>{{ device.ipAddress }}:{{ device.port }}</p>
              </div>
              <el-tag :type="getStatusType(device.status)" size="small">
                {{ getStatusText(device.status) }}
              </el-tag>
            </div>

            <div class="device-preview">
              <div class="screen-preview" @click="refreshScreenshot(device)">
                <img v-if="device.screenshot" :src="device.screenshot" alt="设备画面" />
                <div v-else class="screenshot-placeholder">
                  <el-icon v-if="!device.loadingShot" class="placeholder-icon"><VideoCamera /></el-icon>
                  <el-icon v-else class="is-loading" :size="28"><Loading /></el-icon>
                  <span>{{ device.loadingShot ? '获取画面...' : (device.screenWidth ? device.screenWidth + 'x' + device.screenHeight : '暂无画面') }}</span>
                </div>
              </div>
            </div>

            <div class="device-footer">
              <span class="device-size">
                {{ device.screenWidth || '?' }}x{{ device.screenHeight || '?' }}
              </span>
              <div class="device-actions">
                <el-button size="small" type="primary" :disabled="device.status === 2" @click="handleConnect(device)">连接</el-button>
                <el-button size="small" type="danger" :disabled="device.status === 0" @click="handleDisconnect(device)">断开</el-button>
                <el-button size="small" type="danger" plain @click="handleDelete(device)">删除</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <div v-if="deviceList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Monitor /></el-icon>
        <p class="empty-text">暂无设备，请扫描或手动添加</p>
      </div>
    </div>

    <!-- Scan dialog -->
    <el-dialog v-model="showScanDialog" title="扫描可用设备" width="650px">
      <div v-if="scannedDevices.length > 0">
        <el-table :data="scannedDevices" style="width: 100%">
          <el-table-column prop="deviceName" label="设备名称" width="140" />
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <el-tag :type="row.deviceType === 'windows' ? '' : 'success'" size="small">
                {{ row.deviceType === 'windows' ? '模拟器' : 'Android' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="serial" label="序列号/地址" width="160" />
          <el-table-column label="分辨率" width="110">
            <template #default="{ row }">
              {{ row.screenWidth ? row.screenWidth + 'x' + row.screenHeight : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button v-if="!row.bound" type="primary" size="small" @click="handleBind(row)">绑定</el-button>
              <el-tag v-else type="info" size="small">已绑定</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else-if="!scanning" class="empty-state" style="padding: 40px 0">
        <p class="empty-text">未发现可用设备，请确保模拟器已启动或手机已通过 ADB 连接</p>
      </div>
      <div v-if="scanning" style="text-align: center; padding: 40px 0">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p style="margin-top: 10px">正在扫描设备...</p>
      </div>
      <template #footer>
        <el-button @click="showScanDialog = false">关闭</el-button>
        <el-button type="warning" @click="doScan" :loading="scanning">重新扫描</el-button>
      </template>
    </el-dialog>

    <!-- Add device dialog -->
    <el-dialog v-model="showAddDialog" title="手动添加设备" width="450px">
      <el-form :model="deviceForm" :rules="rules" label-width="80px">
        <el-form-item label="设备名称" prop="deviceName">
          <el-input v-model="deviceForm.deviceName" placeholder="例如：夜神模拟器" />
        </el-form-item>
        <el-form-item label="设备类型" prop="deviceType">
          <el-radio-group v-model="deviceForm.deviceType">
            <el-radio value="windows">模拟器</el-radio>
            <el-radio value="android">Android手机</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="IP地址" prop="ipAddress">
          <el-input v-model="deviceForm.ipAddress" placeholder="127.0.0.1" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="deviceForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="分辨率">
          <el-row :gutter="10">
            <el-col :span="12">
              <el-input-number v-model="deviceForm.screenWidth" placeholder="宽" :min="1" controls-position="right" />
            </el-col>
            <el-col :span="12">
              <el-input-number v-model="deviceForm.screenHeight" placeholder="高" :min="1" controls-position="right" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="deviceForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddDevice">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Search, Refresh, Plus, Iphone, Monitor, VideoCamera, Edit } from '@element-plus/icons-vue'
import { getDeviceList, getDeviceScreenshot, addDevice, deleteDevice, connectDevice, disconnectDevice, scanDevices, bindDevice, updateDevice } from '@/api/device'

const showAddDialog = ref(false)
const showScanDialog = ref(false)
const scanning = ref(false)
const deviceList = ref([])
const scannedDevices = ref([])
let screenshotTimer = null

const deviceForm = reactive({
  deviceName: '',
  deviceType: 'windows',
  ipAddress: '127.0.0.1',
  port: 5555,
  screenWidth: null,
  screenHeight: null,
  remark: ''
})

const rules = {
  deviceName: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  deviceType: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  ipAddress: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }]
}

const getStatusType = (status) => {
  const types = { 0: 'info', 1: 'success', 2: 'warning' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '离线', 1: '在线', 2: '使用中' }
  return texts[status] || '未知'
}

const refreshScreenshot = async (device) => {
  if (!device.deviceId) return
  device.loadingShot = true
  try {
    const res = await getDeviceScreenshot(device.id)
    if (res.data && res.data.base64) {
      device.screenshot = res.data.base64
    }
  } catch (e) {
    // silently fail, device may be offline
  } finally {
    device.loadingShot = false
  }
}

const pollScreenshots = () => {
  deviceList.value.forEach(d => {
    if (d.deviceId && (d.status === 1 || d.status === 2)) {
      refreshScreenshot(d)
    }
  })
}

const loadDevices = async () => {
  try {
    const res = await getDeviceList()
    deviceList.value = (res.data || []).map(d => ({ ...d, screenshot: null, loadingShot: false }))
    ElMessage.success('设备列表已刷新')
    // fetch screenshots after load
    pollScreenshots()
  } catch (e) {
    ElMessage.error('获取设备列表失败')
  }
}

const openScanDialog = async () => {
  showScanDialog.value = true
  await doScan()
}

const doScan = async () => {
  scanning.value = true
  scannedDevices.value = []
  try {
    const res = await scanDevices()
    scannedDevices.value = res.data || []
    if (scannedDevices.value.length === 0) {
      ElMessage.info('未发现可用设备')
    } else {
      ElMessage.success(`发现 ${scannedDevices.value.length} 台设备`)
    }
  } catch (e) {
    ElMessage.error('扫描失败')
  } finally {
    scanning.value = false
  }
}

const handleBind = async (device) => {
  try {
    await bindDevice(device)
    ElMessage.success(`已绑定 ${device.deviceName}`)
    device.bound = true
    loadDevices()
  } catch (e) {
    ElMessage.error('绑定失败')
  }
}

const handleConnect = async (device) => {
  try {
    await connectDevice(device.id)
    ElMessage.success(`已连接 ${device.deviceName}`)
    loadDevices()
  } catch (e) {
    ElMessage.error('连接失败')
  }
}

const handleDisconnect = async (device) => {
  try {
    await disconnectDevice(device.id)
    ElMessage.success(`已断开 ${device.deviceName}`)
    loadDevices()
  } catch (e) {
    ElMessage.error('断开失败')
  }
}

const handleDelete = async (device) => {
  try {
    await ElMessageBox.confirm(`确定删除设备 "${device.deviceName}"？`, '确认删除', { type: 'warning' })
    await deleteDevice(device.id)
    ElMessage.success('设备已删除')
    loadDevices()
  } catch (e) {
    // user cancelled
  }
}

const handleEditTitle = async (device) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入设备标题', '编辑标题', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: device.deviceName,
      inputPlaceholder: '输入设备标题，如 RVL_AL09',
    })
    if (value && value.trim()) {
      await updateDevice(device.id, { deviceName: value.trim() })
      ElMessage.success('标题已更新')
      loadDevices()
    }
  } catch (e) {
    // user cancelled
  }
}

const handleAddDevice = async () => {
  try {
    await addDevice(deviceForm)
    ElMessage.success('设备添加成功')
    showAddDialog.value = false
    loadDevices()
  } catch (e) {
    ElMessage.error('添加失败')
  }
}

onMounted(() => {
  loadDevices()
  // poll every 4s for screenshots
  screenshotTimer = setInterval(pollScreenshots, 4000)
})

onUnmounted(() => {
  if (screenshotTimer) clearInterval(screenshotTimer)
})
</script>

<style scoped lang="scss">
.devices-page {
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

  .device-col {
    margin-bottom: 20px;
  }

  .device-card {
    .device-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 15px;

      .device-icon {
        font-size: 32px;
        color: #409eff;
        &.windows { color: #409eff; }
        &.mobile { color: #67c23a; }
      }

      .device-info {
        flex: 1;
        .device-title {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-bottom: 5px;
          h4 { margin: 0; font-size: 14px; }
        }
        p { margin: 0; font-size: 12px; color: #999; }
      }
    }

    .device-preview {
      margin-bottom: 15px;
      .screen-preview {
        width: 100%;
        height: 180px;
        background: #1a1a2e;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        cursor: pointer;

        img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .screenshot-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          color: #666;
          font-size: 13px;

          .placeholder-icon { font-size: 36px; color: #444; }
        }
      }
    }

    .device-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      .device-size { font-size: 12px; color: #999; }
      .device-actions { display: flex; gap: 6px; }
    }
    .edit-title-btn { width: 24px; height: 24px; font-size: 12px; }
  }
}
</style>