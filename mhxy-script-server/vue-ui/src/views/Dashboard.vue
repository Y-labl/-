<template>
  <div class="dashboard">
    <div class="page-header">
      <h2 class="page-title">控制台</h2>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        刷新数据
      </el-button>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-value">{{ stats.deviceCount }}</div>
          <div class="stat-label">设备总数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card success">
          <div class="stat-value">{{ stats.onlineCount }}</div>
          <div class="stat-label">在线设备</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card warning">
          <div class="stat-value">{{ stats.taskCount }}</div>
          <div class="stat-label">任务总数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card info">
          <div class="stat-value">{{ stats.runningCount }}</div>
          <div class="stat-label">运行中</div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 快捷操作 -->
    <el-row :gutter="20" class="action-row">
      <el-col :span="24">
        <div class="card">
          <div class="card-header">
            <span class="card-title">快捷操作</span>
          </div>
          <div class="quick-actions">
            <el-button type="primary" @click="quickAction('screenshot')">
              <el-icon><Camera /></el-icon>
              快速截图
            </el-button>
            <el-button type="success" @click="quickAction('view')">
              <el-icon><VideoCamera /></el-icon>
              开始观看
            </el-button>
            <el-button type="warning" @click="quickAction('recording')">
              <el-icon><VideoPlay /></el-icon>
              开始录制
            </el-button>
            <el-button type="danger" @click="quickAction('battle')">
              <el-icon><Operation /></el-icon>
              启动打怪
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 设备状态 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">设备状态</span>
            <el-button link type="primary" @click="$router.push('/layout/devices')">
              查看更多
            </el-button>
          </div>
          <el-table :data="deviceList" style="width: 100%">
            <el-table-column prop="deviceName" label="设备名称" />
            <el-table-column prop="ipAddress" label="IP地址" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button 
                  link 
                  type="primary" 
                  size="small"
                  @click="viewDevice(row)"
                >
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">最近任务</span>
            <el-button link type="primary" @click="$router.push('/layout/battle')">
              查看更多
            </el-button>
          </div>
          <el-table :data="taskList" style="width: 100%">
            <el-table-column prop="taskName" label="任务名称" />
            <el-table-column prop="taskType" label="类型" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getTaskStatusType(row.status)">
                  {{ getTaskStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="时间" width="160" />
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

const stats = reactive({
  deviceCount: 0,
  onlineCount: 0,
  taskCount: 0,
  runningCount: 0
})

const deviceList = ref([])
const taskList = ref([])

const getStatusType = (status) => {
  const types = { 0: 'info', 1: 'success', 2: 'warning' }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = { 0: '离线', 1: '在线', 2: '使用中' }
  return texts[status] || '未知'
}

const getTaskStatusType = (status) => {
  const types = { 0: 'info', 1: '', 2: 'success', 3: 'danger', 4: 'warning' }
  return types[status] || 'info'
}

const getTaskStatusText = (status) => {
  const texts = { 0: '等待', 1: '执行中', 2: '成功', 3: '失败', 4: '取消' }
  return texts[status] || '未知'
}

const refreshData = () => {
  // 模拟数据
  stats.deviceCount = 5
  stats.onlineCount = 3
  stats.taskCount = 12
  stats.runningCount = 2
  
  deviceList.value = [
    { deviceName: '安卓模拟器-1', ipAddress: '127.0.0.1:5555', status: 1 },
    { deviceName: '安卓模拟器-2', ipAddress: '127.0.0.1:5556', status: 2 },
    { deviceName: '真机-小米', ipAddress: '192.168.1.100:5555', status: 1 },
    { deviceName: '真机-华为', ipAddress: '192.168.1.101:5555', status: 0 },
    { deviceName: '模拟器-夜神', ipAddress: '127.0.0.1:62001', status: 1 }
  ]
  
  taskList.value = [
    { taskName: '日常任务-师门', taskType: '打怪', status: 2, createTime: '2026-07-08 16:30' },
    { taskName: '副本-水陆大会', taskType: '副本', status: 1, createTime: '2026-07-08 15:20' },
    { taskName: '抓鬼任务', taskType: '打怪', status: 2, createTime: '2026-07-08 14:10' },
    { taskName: '科举答题', taskType: '活动', status: 3, createTime: '2026-07-08 13:00' }
  ]
  
  ElMessage.success('数据已刷新')
}

const quickAction = (type) => {
  const routes = {
    screenshot: '/layout/screenshot',
    view: '/layout/view',
    recording: '/layout/recording',
    battle: '/layout/battle'
  }
  router.push(routes[type])
}

const viewDevice = (device) => {
  router.push('/layout/view')
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped lang="scss">
.dashboard {
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
  
  .stat-row {
    margin-bottom: 20px;
  }
  
  .action-row {
    margin-bottom: 20px;
    
    .quick-actions {
      display: flex;
      gap: 15px;
      
      .el-button {
        padding: 20px 30px;
        font-size: 16px;
        
        .el-icon {
          margin-right: 8px;
        }
      }
    }
  }
}
</style>
