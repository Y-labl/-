<template>
  <div class="battle-detail">
    <div class="page-header">
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2 class="page-title">{{ sceneInfo.sceneName }}</h2>
      <el-button :type="isRunning ? 'danger' : 'primary'" @click="toggleTask">
        {{ isRunning ? '停止任务' : '启动任务' }}
      </el-button>
    </div>
    
    <el-row :gutter="20">
      <!-- 画面预览 -->
      <el-col :span="16">
        <div class="card">
          <div class="card-header">
            <span class="card-title">实时画面</span>
            <el-button size="small" type="primary" @click="captureScreen">
              <el-icon><Camera /></el-icon>
              截图
            </el-button>
          </div>
          <div class="screen-preview">
            <img v-if="currentScreen" :src="currentScreen" alt="实时画面" />
            <div v-else class="preview-placeholder">
              <el-icon :size="64"><VideoCamera /></el-icon>
              <p>设备未连接</p>
            </div>
          </div>
        </div>
        
        <!-- 执行日志 -->
        <div class="card log-card">
          <div class="card-header">
            <span class="card-title">执行日志</span>
            <el-button size="small" @click="clearLogs">清空</el-button>
          </div>
          <div class="log-container" ref="logContainer">
            <div 
              v-for="(log, index) in logs" 
              :key="index" 
              class="log-item"
              :class="log.type"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </el-col>
      
      <!-- 任务配置 -->
      <el-col :span="8">
        <!-- 任务状态 -->
        <div class="card status-card">
          <div class="card-header">
            <span class="card-title">任务状态</span>
            <el-tag :type="isRunning ? 'success' : 'info'">
              {{ isRunning ? '运行中' : '已停止' }}
            </el-tag>
          </div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="运行时间">
              {{ formatDuration(runningTime) }}
            </el-descriptions-item>
            <el-descriptions-item label="战斗次数">
              {{ taskStats.battleCount }}
            </el-descriptions-item>
            <el-descriptions-item label="击杀数量">
              {{ taskStats.killCount }}
            </el-descriptions-item>
            <el-descriptions-item label="死亡次数">
              {{ taskStats.deathCount }}
            </el-descriptions-item>
            <el-descriptions-item label="获得金币">
              {{ taskStats.goldEarned }}
            </el-descriptions-item>
            <el-descriptions-item label="获得经验">
              {{ taskStats.expEarned }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <!-- 场景配置 -->
        <div class="card config-card">
          <div class="card-header">
            <span class="card-title">场景配置</span>
            <el-button size="small" link type="primary" @click="editConfig">
              编辑
            </el-button>
          </div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="场景类型">
              {{ sceneInfo.sceneType }}
            </el-descriptions-item>
            <el-descriptions-item label="游戏区服">
              {{ sceneInfo.gameArea }} - {{ sceneInfo.gameServer }}
            </el-descriptions-item>
            <el-descriptions-item label="角色名称">
              {{ sceneInfo.roleName }}
            </el-descriptions-item>
            <el-descriptions-item label="角色等级">
              {{ sceneInfo.characterLevel }}
            </el-descriptions-item>
            <el-descriptions-item label="执行设备">
              {{ sceneInfo.deviceName }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <!-- 执行策略 -->
        <div class="card strategy-card">
          <div class="card-header">
            <span class="card-title">执行策略</span>
          </div>
          <div class="strategy-list">
            <div class="strategy-item">
              <span>自动战斗</span>
              <el-switch v-model="sceneInfo.autoBattle" disabled />
            </div>
            <div class="strategy-item">
              <span>自动恢复</span>
              <el-switch v-model="sceneInfo.autoRecovery" disabled />
            </div>
            <div class="strategy-item">
              <span>自动复活</span>
              <el-switch v-model="sceneInfo.autoRevival" disabled />
            </div>
            <div class="strategy-item">
              <span>自动拾取</span>
              <el-switch v-model="sceneInfo.autoPickup" disabled />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const sceneId = route.params.id

const isRunning = ref(false)
const runningTime = ref(0)
const currentScreen = ref(null)
const logContainer = ref(null)

let timer = null

const sceneInfo = reactive({
  sceneName: '日常任务-师门',
  sceneType: 'PVE',
  gameArea: '生日快乐',
  gameServer: '生日快乐10',
  roleName: '大唐官府01',
  characterLevel: 69,
  deviceName: '夜神模拟器',
  autoBattle: true,
  autoRecovery: true,
  autoRevival: true,
  autoPickup: true
})

const taskStats = reactive({
  battleCount: 0,
  killCount: 0,
  deathCount: 0,
  goldEarned: 0,
  expEarned: 0
})

const logs = ref([
  { time: '17:08:30', message: '任务已启动', type: 'info' },
  { time: '17:08:31', message: '正在连接设备...', type: 'info' },
  { time: '17:08:32', message: '设备连接成功', type: 'success' },
  { time: '17:08:35', message: '进入游戏...', type: 'info' },
  { time: '17:08:40', message: '找到师门任务npc', type: 'success' },
  { time: '17:08:42', message: '开始战斗 [第1场]', type: 'warning' },
  { time: '17:09:10', message: '战斗胜利，获得金币500，经验2000', type: 'success' }
])

const formatDuration = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const toggleTask = () => {
  if (isRunning.value) {
    stopTask()
  } else {
    startTask()
  }
}

const startTask = () => {
  isRunning.value = true
  runningTime.value = 0
  taskStats.battleCount = 0
  taskStats.killCount = 0
  
  addLog('任务已启动', 'info')
  
  timer = setInterval(() => {
    runningTime.value++
    taskStats.battleCount++
    taskStats.killCount += Math.floor(Math.random() * 3) + 1
    taskStats.goldEarned += Math.floor(Math.random() * 500) + 200
    taskStats.expEarned += Math.floor(Math.random() * 2000) + 500
    
    if (runningTime.value % 30 === 0) {
      addLog(`[第${taskStats.battleCount}场] 战斗进行中...`, 'warning')
    }
  }, 1000)
}

const stopTask = () => {
  isRunning.value = false
  if (timer) {
    clearInterval(timer)
    timer = null
  }
  addLog('任务已停止', 'info')
}

const addLog = (message, type = 'info') => {
  const now = new Date()
  const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
  logs.value.push({ time, message, type })
  
  // 滚动到底部
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

const clearLogs = () => {
  logs.value = []
}

const captureScreen = () => {
  ElMessage.success('截图成功')
}

const editConfig = () => {
  ElMessage.info('编辑配置')
}

onMounted(() => {
  // 加载场景信息
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped lang="scss">
.battle-detail {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .page-title {
      margin: 0;
      font-size: 20px;
      font-weight: bold;
    }
  }
  
  .screen-preview {
    width: 100%;
    aspect-ratio: 16/10;
    background: #000;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    
    img {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
    
    .preview-placeholder {
      color: #666;
      text-align: center;
    }
  }
  
  .log-card {
    margin-top: 20px;
    
    .log-container {
      height: 250px;
      overflow-y: auto;
      background: #1e1e1e;
      border-radius: 4px;
      padding: 10px;
      font-family: 'Consolas', monospace;
      font-size: 13px;
      
      .log-item {
        margin-bottom: 5px;
        
        .log-time {
          color: #888;
          margin-right: 10px;
        }
        
        &.info .log-message {
          color: #fff;
        }
        
        &.success .log-message {
          color: #4caf50;
        }
        
        &.warning .log-message {
          color: #ff9800;
        }
        
        &.error .log-message {
          color: #f44336;
        }
      }
    }
  }
  
  .status-card,
  .config-card,
  .strategy-card {
    margin-bottom: 20px;
  }
  
  .strategy-list {
    .strategy-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid #eee;
      
      &:last-child {
        border-bottom: none;
      }
    }
  }
}
</style>
