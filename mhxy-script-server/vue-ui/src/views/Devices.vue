<template>
  <div class="devices-page">
    <div class="page-header">
      <h2 class="page-title">设备管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="refreshDevices">
          <el-icon><Refresh /></el-icon>
          刷新设备
        </el-button>
        <el-button type="success" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加设备
        </el-button>
      </div>
    </div>
    
    <!-- 设备列表 -->
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
              <el-icon class="device-icon" :class="getDeviceIcon(device.deviceType)">
                <Monitor v-if="device.deviceType === 'windows'" />
                <Iphone v-else />
              </el-icon>
              <div class="device-info">
                <h4>{{ device.deviceName }}</h4>
                <p>{{ device.ipAddress }}:{{ device.port }}</p>
              </div>
              <el-tag :type="getStatusType(device.status)" size="small">
                {{ getStatusText(device.status) }}
              </el-tag>
            </div>
            
            <div class="device-preview">
              <div class="screen-preview">
                <img v-if="device.screenshot" :src="device.screenshot" alt="设备截图" />
                <span v-else>暂无画面</span>
              </div>
            </div>
            
            <div class="device-footer">
              <span class="device-size">
                {{ device.screenWidth }}x{{ device.screenHeight }}
              </span>
              <div class="device-actions">
                <el-button 
                  size="small" 
                  type="primary"
                  :disabled="device.status === 2"
                  @click="connectDevice(device)"
                >
                  连接
                </el-button>
                <el-button 
                  size="small" 
                  type="danger"
                  :disabled="device.status === 0"
                  @click="disconnectDevice(device)"
                >
                  断开
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <div v-if="deviceList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Monitor /></el-icon>
        <p class="empty-text">暂无设备，请添加设备</p>
      </div>
    </div>
    
    <!-- 添加设备对话框 -->
    <el-dialog v-model="showAddDialog" title="添加设备" width="500px">
      <el-form ref="deviceFormRef" :model="deviceForm" :rules="rules" label-width="100px">
        <el-form-item label="设备名称" prop="deviceName">
          <el-input v-model="deviceForm.deviceName" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="deviceType">
          <el-select v-model="deviceForm.deviceType" placeholder="请选择设备类型">
            <el-option label="Windows模拟器" value="windows" />
            <el-option label="Android" value="android" />
            <el-option label="iOS" value="ios" />
          </el-select>
        </el-form-item>
        <el-form-item label="IP地址" prop="ipAddress">
          <el-input v-model="deviceForm.ipAddress" placeholder="127.0.0.1" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="deviceForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="deviceForm.remark" type="textarea" rows="3" />
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
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const showAddDialog = ref(false)
const deviceList = ref([])

const deviceForm = reactive({
  deviceName: '',
  deviceType: 'windows',
  ipAddress: '127.0.0.1',
  port: 5555,
  remark: ''
})

const rules = {
  deviceName: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  deviceType: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  ipAddress: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口', trigger: 'blur' }]
}

const getDeviceIcon = (type) => {
  return type === 'windows' ? 'windows' : 'mobile'
}

const getStatusType = (status) => {
  const types = { 0: 'info', 1: 'success', 2: 'warning' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '离线', 1: '在线', 2: '使用中' }
  return texts[status] || '未知'
}

const refreshDevices = () => {
  // 模拟数据
  deviceList.value = [
    {
      id: 1,
      deviceName: '夜神模拟器',
      deviceType: 'windows',
      ipAddress: '127.0.0.1',
      port: 62001,
      status: 1,
      screenWidth: 1280,
      screenHeight: 720,
      screenshot: null
    },
    {
      id: 2,
      deviceName: '雷电模拟器',
      deviceType: 'windows',
      ipAddress: '127.0.0.1',
      port: 5555,
      status: 2,
      screenWidth: 1920,
      screenHeight: 1080,
      screenshot: null
    },
    {
      id: 3,
      deviceName: '小米手机',
      deviceType: 'android',
      ipAddress: '192.168.1.100',
      port: 5555,
      status: 1,
      screenWidth: 1080,
      screenHeight: 2400,
      screenshot: null
    }
  ]
  ElMessage.success('设备列表已刷新')
}

const connectDevice = (device) => {
  ElMessage.success(`正在连接 ${device.deviceName}...`)
  device.status = 2
}

const disconnectDevice = (device) => {
  ElMessage.success(`已断开 ${device.deviceName}`)
  device.status = 0
}

const handleAddDevice = () => {
  ElMessage.success('设备添加成功')
  showAddDialog.value = false
  refreshDevices()
}

// 初始化
refreshDevices()
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
        
        &.windows {
          color: #409eff;
        }
        &.mobile {
          color: #67c23a;
        }
      }
      
      .device-info {
        flex: 1;
        
        h4 {
          margin: 0 0 5px;
          font-size: 14px;
        }
        
        p {
          margin: 0;
          font-size: 12px;
          color: #999;
        }
      }
    }
    
    .device-preview {
      margin-bottom: 15px;
      
      .screen-preview {
        width: 100%;
        height: 150px;
        background: #000;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #666;
        font-size: 14px;
        overflow: hidden;
        
        img {
          max-width: 100%;
          max-height: 100%;
        }
      }
    }
    
    .device-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .device-size {
        font-size: 12px;
        color: #999;
      }
      
      .device-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
}
</style>
