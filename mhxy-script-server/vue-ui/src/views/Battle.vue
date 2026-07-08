<template>
  <div class="battle-page">
    <div class="page-header">
      <h2 class="page-title">打怪场景</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          新建场景
        </el-button>
      </div>
    </div>
    
    <!-- 场景列表 -->
    <div class="card">
      <div class="scene-grid">
        <el-card 
          v-for="scene in sceneList" 
          :key="scene.id" 
          class="scene-card"
          shadow="hover"
        >
          <div class="scene-header">
            <h3>{{ scene.sceneName }}</h3>
            <el-tag :type="getSceneType(scene.sceneType)" size="small">
              {{ getSceneTypeText(scene.sceneType) }}
            </el-tag>
          </div>
          
          <div class="scene-info">
            <p><span>区服：</span>{{ scene.gameArea }} - {{ scene.gameServer }}</p>
            <p><span>角色：</span>{{ scene.roleName || '未设置' }}</p>
            <p><span>等级：</span>{{ scene.characterLevel || '-' }}</p>
            <p><span>模式：</span>{{ scene.characterTeam === 'team' ? '组队' : '单人' }}</p>
          </div>
          
          <div class="scene-stats">
            <span>使用 {{ scene.useCount }} 次</span>
            <span>成功 {{ scene.successCount }} 次</span>
          </div>
          
          <div class="scene-actions">
            <el-button type="primary" @click="startScene(scene)">
              <el-icon><VideoPlay /></el-icon>
              启动
            </el-button>
            <el-button @click="editScene(scene)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" @click="deleteScene(scene)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </el-card>
      </div>
      
      <div v-if="sceneList.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Operation /></el-icon>
        <p class="empty-text">暂无场景配置，请创建新场景</p>
      </div>
    </div>
    
    <!-- 正在运行的任务 -->
    <div class="card running-tasks">
      <div class="card-header">
        <span class="card-title">运行中的任务</span>
        <el-tag type="danger">{{ runningTasks.length }} 个任务运行中</el-tag>
      </div>
      
      <el-table :data="runningTasks" style="width: 100%">
        <el-table-column prop="sceneName" label="场景名称" />
        <el-table-column prop="deviceName" label="设备" />
        <el-table-column prop="progress" label="进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="getProgressStatus(row.progress)" />
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="运行时长" width="120">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusType(row.status)">
              {{ getTaskStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="danger" size="small" @click="stopTask(row)">
              停止
            </el-button>
            <el-button link type="primary" size="small" @click="viewTask(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 添加/编辑场景对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      :title="isEdit ? '编辑场景' : '新建场景'" 
      width="700px"
    >
      <el-form ref="sceneFormRef" :model="sceneForm" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="场景名称" prop="sceneName">
              <el-input v-model="sceneForm.sceneName" placeholder="请输入场景名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="场景类型" prop="sceneType">
              <el-select v-model="sceneForm.sceneType" placeholder="选择类型">
                <el-option label="PVE" value="pve" />
                <el-option label="PVP" value="pvp" />
                <el-option label="副本" value="dungeon" />
                <el-option label="BOSS" value="boss" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="游戏区服" prop="gameType">
              <el-select v-model="sceneForm.gameType" placeholder="选择区服">
                <el-option label="点卡服" value="dianka" />
                <el-option label="畅玩服" value="changwan" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="区/服务器">
              <el-input v-model="sceneForm.gameArea" placeholder="如：生日快乐" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色名称">
              <el-input v-model="sceneForm.roleName" placeholder="游戏角色名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色等级">
              <el-input-number v-model="sceneForm.characterLevel" :min="1" :max="175" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="组队模式">
          <el-radio-group v-model="sceneForm.characterTeam">
            <el-radio label="single">单人</el-radio>
            <el-radio label="team">组队</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-divider>执行策略</el-divider>
        
        <el-form-item label="战斗策略">
          <el-switch v-model="sceneForm.autoBattle" active-text="自动战斗" />
          <el-switch v-model="sceneForm.autoRecovery" active-text="自动恢复" />
          <el-switch v-model="sceneForm.autoRevival" active-text="自动复活" />
          <el-switch v-model="sceneForm.autoPickup" active-text="自动拾取" />
        </el-form-item>
        
        <el-form-item label="执行设备">
          <el-select v-model="sceneForm.deviceId" placeholder="选择设备">
            <el-option 
              v-for="device in deviceList" 
              :key="device.id" 
              :label="device.deviceName" 
              :value="device.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="备注">
          <el-input v-model="sceneForm.remark" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveScene">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const showAddDialog = ref(false)
const isEdit = ref(false)

const deviceList = ref([
  { id: 1, deviceName: '夜神模拟器' },
  { id: 2, deviceName: '雷电模拟器' }
])

const sceneForm = reactive({
  id: null,
  sceneName: '',
  sceneType: 'pve',
  gameType: 'dianka',
  gameArea: '',
  gameServer: '',
  roleName: '',
  characterLevel: null,
  characterTeam: 'single',
  autoBattle: true,
  autoRecovery: true,
  autoRevival: true,
  autoPickup: true,
  deviceId: null,
  remark: ''
})

const rules = {
  sceneName: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
  sceneType: [{ required: true, message: '请选择场景类型', trigger: 'change' }],
  gameType: [{ required: true, message: '请选择区服', trigger: 'change' }]
}

const sceneList = ref([
  {
    id: 1,
    sceneName: '日常任务-师门',
    sceneType: 'pve',
    gameType: 'dianka',
    gameArea: '生日快乐',
    gameServer: '生日快乐10',
    roleName: '大唐官府01',
    characterLevel: 69,
    characterTeam: 'single',
    useCount: 156,
    successCount: 152
  },
  {
    id: 2,
    sceneName: '抓鬼任务',
    sceneType: 'pve',
    gameType: 'dianka',
    gameArea: '生日快乐',
    gameServer: '生日快乐10',
    roleName: '大唐官府01',
    characterLevel: 109,
    characterTeam: 'single',
    useCount: 89,
    successCount: 85
  },
  {
    id: 3,
    sceneName: '副本-水陆大会',
    sceneType: 'dungeon',
    gameType: 'dianka',
    gameArea: '生日快乐',
    gameServer: '生日快乐10',
    roleName: '大唐官府01',
    characterLevel: 129,
    characterTeam: 'team',
    useCount: 45,
    successCount: 42
  }
])

const runningTasks = ref([
  {
    id: 1,
    sceneName: '日常任务-师门',
    deviceName: '夜神模拟器',
    progress: 65,
    duration: 1800,
    status: 1
  }
])

const getSceneType = (type) => {
  const types = { pve: 'success', pvp: 'warning', dungeon: 'primary', boss: 'danger' }
  return types[type] || 'info'
}

const getSceneTypeText = (type) => {
  const texts = { pve: 'PVE', pvp: 'PVP', dungeon: '副本', boss: 'BOSS' }
  return texts[type] || '普通'
}

const getTaskStatusType = (status) => {
  const types = { 0: 'info', 1: '', 2: 'success', 3: 'danger' }
  return types[status] || 'info'
}

const getTaskStatusText = (status) => {
  const texts = { 0: '等待', 1: '执行中', 2: '成功', 3: '失败' }
  return texts[status] || '未知'
}

const getProgressStatus = (progress) => {
  if (progress >= 100) return 'success'
  if (progress >= 50) return ''
  return 'warning'
}

const formatDuration = (seconds) => {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}小时${m}分钟` : `${m}分钟`
}

const startScene = (scene) => {
  ElMessage.success(`正在启动场景: ${scene.sceneName}`)
}

const editScene = (scene) => {
  isEdit.value = true
  Object.assign(sceneForm, scene)
  showAddDialog.value = true
}

const deleteScene = async (scene) => {
  await ElMessageBox.confirm(`确定要删除场景 "${scene.sceneName}" 吗？`, '提示', { type: 'warning' })
  ElMessage.success('删除成功')
}

const saveScene = () => {
  ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
  showAddDialog.value = false
}

const stopTask = (task) => {
  ElMessageBox.confirm('确定要停止该任务吗？', '提示', { type: 'warning' })
    .then(() => {
      ElMessage.success('任务已停止')
    })
}

const viewTask = (task) => {
  router.push(`/layout/battle/${task.id}`)
}
</script>

<style scoped lang="scss">
.battle-page {
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
  
  .scene-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    
    .scene-card {
      .scene-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        
        h3 {
          margin: 0;
          font-size: 16px;
        }
      }
      
      .scene-info {
        margin-bottom: 15px;
        
        p {
          margin: 5px 0;
          font-size: 13px;
          color: #666;
          
          span {
            color: #999;
          }
        }
      }
      
      .scene-stats {
        display: flex;
        gap: 15px;
        font-size: 12px;
        color: #999;
        margin-bottom: 15px;
        padding-bottom: 15px;
        border-bottom: 1px solid #eee;
      }
      
      .scene-actions {
        display: flex;
        gap: 10px;
        
        .el-button {
          flex: 1;
        }
      }
    }
  }
  
  .running-tasks {
    margin-top: 20px;
  }
}
</style>
