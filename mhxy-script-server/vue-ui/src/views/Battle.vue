<template>
  <div class="battle-page">
    <div class="page-header">
      <h2 class="page-title">打怪场景</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openAddDialog">
          <el-icon><Plus /></el-icon>
          新建场景
        </el-button>
      </div>
    </div>

    <div class="card">
      <div class="scene-grid">
        <el-card v-for="scene in sceneList" :key="scene.id" class="scene-card" shadow="hover">
          <div class="scene-header">
            <h3>{{ scene.sceneName }}</h3>
            <el-tag :type="getSceneTagType(scene.sceneType)" size="small">
              {{ getSceneTypeLabel(scene.sceneType) }}
            </el-tag>
          </div>
          <div class="scene-info">
            <p><span>区服：</span>{{ scene.gameArea }} - {{ scene.gameServer }}</p>
            <p><span>角色：</span>{{ scene.roleName || '未设置' }}</p>
            <p><span>等级：</span>{{ scene.characterLevel || '-' }}</p>
            <p><span>模式：</span>{{ scene.characterTeam === 'team' ? '组队' : '单人' }}</p>
            <p v-if="getBoundDevice(scene)"><span>设备：</span>{{ getBoundDevice(scene) }}</p>
          </div>
          <div class="scene-stats">
            <span>使用 {{ scene.useCount }} 次</span>
            <span>成功 {{ scene.successCount }} 次</span>
          </div>
          <div class="scene-actions">
            <el-button
              v-if="scene.sceneType !== 'steal_card'"
              type="primary" @click="startScene(scene)"
            >
              <el-icon><VideoPlay /></el-icon>启动
            </el-button>
            <el-button
              v-if="scene.sceneType === 'steal_card'"
              type="warning" :disabled="isSceneRunning(scene.id)"
              @click="openStealDialog(scene)"
            >
              <el-icon><VideoPlay /></el-icon>启动偷卡
            </el-button>
            <el-button
              v-if="scene.sceneType === 'steal_card' && isSceneRunning(scene.id)"
              type="danger" @click="stopStealScene(scene)"
            >
              <el-icon><VideoPause /></el-icon>停止偷卡
            </el-button>
            <el-button @click="editScene(scene)">
              <el-icon><Edit /></el-icon>编辑
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

    <div class="card running-tasks" style="margin-top:20px">
      <div class="card-header">
        <span class="card-title">运行中的任务</span>
        <el-tag type="danger">{{ runningTasks.length }} 个任务运行中</el-tag>
      </div>
      <el-table :data="runningTasks" style="width:100%">
        <el-table-column prop="sceneName" label="场景名称" />
        <el-table-column prop="deviceName" label="设备" />
        <el-table-column prop="progress" label="进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :status="getProgressStatus(row.progress)" />
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="运行时长" width="120">
          <template #default="{ row }">{{ formatDuration(row.duration) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskStatusTag(row.status)">{{ getTaskStatusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="danger" size="small" @click="stopTask(row)">停止</el-button>
            <el-button link type="primary" size="small" @click="viewTask(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新建/编辑场景 -->
    <el-dialog v-model="showFormDialog" :title="isEdit ? '编辑场景' : '新建场景'" width="800px">
      <el-tabs v-model="formTab" type="border-card">
        <el-tab-pane label="场景配置" name="scene">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="场景名称" prop="sceneName">
              <el-input v-model="form.sceneName" placeholder="请输入场景名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="场景类型" prop="sceneType">
              <el-select v-model="form.sceneType" placeholder="选择类型">
                <el-option label="PVE" value="pve" />
                <el-option label="PVP" value="pvp" />
                <el-option label="副本" value="dungeon" />
                <el-option label="BOSS" value="boss" />
                <el-option label="偷卡" value="steal_card" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="区服" prop="gameType">
              <el-select v-model="form.gameType">
                <el-option label="点卡服" value="dianka" />
                <el-option label="畅玩服" value="changwan" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="大区" prop="gameArea">
              <el-input v-model="form.gameArea" placeholder="如：生日快乐" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="服务器" prop="gameServer">
              <el-input v-model="form.gameServer" placeholder="如：生日快乐10" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色名" prop="roleName">
              <el-input v-model="form.roleName" placeholder="角色名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色等级">
              <el-input-number v-model="form.characterLevel" :min="1" :max="175" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模式">
              <el-radio-group v-model="form.characterTeam">
                <el-radio label="single">单人</el-radio>
                <el-radio label="team">组队</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="绑定设备" prop="deviceId">
              <el-select v-model="form.deviceId" placeholder="选择设备" clearable>
                <el-option v-for="dev in allDevices" :key="dev.id" :label="dev.deviceName" :value="dev.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="人物加血方式">
              <el-select v-model="form.battleStrategy.hpReplenish" style="width:100%">
                <el-option label="酒肆" value="酒肆" />
                <el-option label="红碗" value="红碗" />
                <el-option label="秘制" value="秘制" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="人物加蓝方式">
              <el-select v-model="form.battleStrategy.mpReplenish" style="width:100%">
                <el-option label="酒肆" value="酒肆" />
                <el-option label="蓝碗" value="蓝碗" />
                <el-option label="秘制" value="秘制" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="血量阈值">
              <div class="threshold-row">
                <el-slider v-model="form.battleStrategy.hpThreshold" :min="0" :max="100" :step="5" show-stops />
                <span class="threshold-value">{{ form.battleStrategy.hpThreshold }}%</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="蓝量阈值">
              <div class="threshold-row">
                <el-slider v-model="form.battleStrategy.mpThreshold" :min="0" :max="100" :step="5" show-stops />
                <span class="threshold-value">{{ form.battleStrategy.mpThreshold }}%</span>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20" class="battle-ops-row">
          <el-col :span="24">
            <div class="battle-ops-section">
              <div class="battle-ops-header">
                <div class="battle-ops-title">人物战斗操作：</div>
                <el-form-item label="自动导路" class="inline-auto-nav">
                  <el-switch v-model="form.battleStrategy.autoNavigate" active-text="开启" inactive-text="关闭" />
                </el-form-item>
              </div>
              <div class="battle-ops-body">
                <div class="battle-op-item">
                  <span>一、捕捉</span>
                  <el-switch v-model="form.battleStrategy.battleOps['1_capture']" />
                </div>
                <div class="battle-op-item">
                  <span>二、妙手空空</span>
                  <el-switch v-model="form.battleStrategy.battleOps['2_steal']" />
                  <el-button link type="primary" size="small" @click="openStealSettings">设置</el-button>
                </div>
                <div class="battle-op-item vertical after-options">
                  <div v-for="opt in afterOptions" :key="opt.key" class="after-option" :class="{ active: selectedAfterAction === opt.key }">
                    <el-switch :model-value="selectedAfterAction === opt.key" @change="selectAfterAction(opt.key)" />
                    <span>{{ opt.label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>
        </el-tab-pane>
        <el-tab-pane label="设备配置" name="device">
          <div class="device-config-tab">
            <el-table :data="allDevices" style="width:100%" size="small">
              <el-table-column prop="deviceName" label="设备名称" width="140" />
              <el-table-column prop="deviceId" label="序列号" width="140" />
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="getDeviceConfigRunning(row.id) ? 'warning' : 'info'" size="small">
                    {{ getDeviceConfigRunning(row.id) ? '运行中' : '空闲' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="目标怪物" min-width="160">
                <template #default="{ row }">
                  <span class="monster-preview">{{ getDeviceConfigField(row.id, 'targetMonsters') || '未配置' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" @click="openDeviceConfigDialog(row)">配置</el-button>
                  <el-button
                    v-if="!getDeviceConfigRunning(row.id)"
                    size="small" type="warning"
                    :disabled="!getDeviceConfigField(row.id, 'targetMonsters')"
                    @click="startDeviceSteal(row)"
                  >启动</el-button>
                  <el-button
                    v-else
                    size="small" type="danger"
                    @click="stopDeviceSteal(row)"
                  >停止</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="saveScene">保存</el-button>
      </template>
    </el-dialog>

    <!-- 妙手空空设置 -->
    <el-dialog v-model="showStealSettingsDialog" title="设置妙手空空" width="820px" class="steal-settings-dialog">
      <div class="steal-settings-subtitle">不支持自动换场景到: 丝绸之路、无名鬼域</div>
      <div class="steal-scene-rows">
        <div v-for="(row, index) in stealSettingsForm.stealScenes" :key="index" class="steal-scene-row">
          <el-checkbox v-model="row.enabled" class="row-enable" />
          <span class="row-label">场景{{ index + 1 }}</span>
          <el-select v-model="row.scene" class="row-select scene-select" size="small">
            <el-option v-for="s in sceneOptions" :key="s" :label="s" :value="s" />
          </el-select>
          <el-select v-model="row.rings" class="row-select" size="small">
            <el-option v-for="o in ringsOptions" :key="o" :label="o" :value="o" />
          </el-select>
          <el-select v-model="row.cards" class="row-select" size="small">
            <el-option v-for="o in cardsOptions" :key="o" :label="o" :value="o" />
          </el-select>
          <el-select v-model="row.minutes" class="row-select" size="small">
            <el-option v-for="o in minutesOptions" :key="o" :label="o" :value="o" />
          </el-select>
          <el-select v-model="row.switchMode" class="row-select" size="small">
            <el-option v-for="o in switchModeOptions" :key="o" :label="o" :value="o" />
          </el-select>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" class="steal-confirm-btn" @click="saveStealSettings">确认</el-button>
        <el-button @click="showStealSettingsDialog = false">取消</el-button>
      </template>
    </el-dialog>

    <!-- 设备配置编辑 -->
    <el-dialog v-model="showDeviceConfigDialog" :title="'设备配置 - ' + deviceConfigForm.deviceName" width="780px">
      <el-form :model="deviceConfigForm" label-width="100px">
        <!-- 锁定的设备 -->
        <el-form-item label="绑定设备">
          <el-tag type="primary" size="large">{{ deviceConfigForm.deviceName }}</el-tag>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="区服">
              <el-select v-model="deviceConfigForm.gameType" style="width:100%">
                <el-option label="点卡服" value="dianka" />
                <el-option label="畅玩服" value="changwan" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="大区">
              <el-input v-model="deviceConfigForm.gameArea" placeholder="如：生日快乐" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="服务器">
              <el-input v-model="deviceConfigForm.gameServer" placeholder="如：生日快乐10" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色名">
              <el-input v-model="deviceConfigForm.roleName" placeholder="角色名称" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="角色等级">
              <el-input-number v-model="deviceConfigForm.characterLevel" :min="1" :max="175" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模式">
              <el-radio-group v-model="deviceConfigForm.characterTeam">
                <el-radio label="single">单人</el-radio>
                <el-radio label="team">组队</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 目标怪物 -->
        <el-form-item label="目标怪物">
          <el-input v-model="deviceConfigForm.targetMonsters" placeholder="如：噬天虎,炎魔神,金饶僧" />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="人物加血方式">
              <el-select v-model="deviceConfigForm.battleStrategy.hpReplenish" style="width:100%">
                <el-option label="酒肆" value="酒肆" />
                <el-option label="红碗" value="红碗" />
                <el-option label="秘制" value="秘制" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="人物加蓝方式">
              <el-select v-model="deviceConfigForm.battleStrategy.mpReplenish" style="width:100%">
                <el-option label="酒肆" value="酒肆" />
                <el-option label="蓝碗" value="蓝碗" />
                <el-option label="秘制" value="秘制" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="血量阈值">
              <div class="threshold-row">
                <el-slider v-model="deviceConfigForm.battleStrategy.hpThreshold" :min="0" :max="100" :step="5" show-stops />
                <span class="threshold-value">{{ deviceConfigForm.battleStrategy.hpThreshold }}%</span>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="蓝量阈值">
              <div class="threshold-row">
                <el-slider v-model="deviceConfigForm.battleStrategy.mpThreshold" :min="0" :max="100" :step="5" show-stops />
                <span class="threshold-value">{{ deviceConfigForm.battleStrategy.mpThreshold }}%</span>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 战斗操作 -->
        <div class="battle-ops-row">
          <div class="battle-ops-section">
            <div class="battle-ops-header">
              <div class="battle-ops-title">人物战斗操作：</div>
              <el-form-item label="自动导路" class="inline-auto-nav">
                <el-switch v-model="deviceConfigForm.battleStrategy.autoNavigate" active-text="开启" inactive-text="关闭" />
              </el-form-item>
            </div>
            <div class="battle-ops-body">
              <div class="battle-op-item">
                <span>一、捕捉</span>
                <el-switch v-model="deviceConfigForm.battleStrategy.battleOps['1_capture']" />
              </div>
              <div class="battle-op-item">
                <span>二、妙手空空</span>
                <el-switch v-model="deviceConfigForm.battleStrategy.battleOps['2_steal']" />
              </div>
              <div class="battle-op-item vertical after-options">
                <div v-for="opt in afterOptions" :key="opt.key" class="after-option" :class="{ active: deviceAfterAction === opt.key }">
                  <el-switch :model-value="deviceAfterAction === opt.key" @change="selectDeviceAfterAction(opt.key)" />
                  <span>{{ opt.label }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <el-row :gutter="20" style="margin-top:12px">
          <el-col :span="12">
            <el-form-item label="地图点击区域">
              <el-input v-model="deviceConfigForm.mapClickArea" placeholder="x1,y1,x2,y2" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="模板置信度">
              <el-input-number v-model="deviceConfigForm.templateConfidence" :min="0.5" :max="1.0" :step="0.05" :precision="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="行走间隔(ms)">
              <el-input-number v-model="deviceConfigForm.walkInterval" :min="100" :max="2000" :step="50" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="偷卡次数">
              <el-input-number v-model="deviceConfigForm.stealAttempts" :min="1" :max="10" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="自动战斗">
              <el-switch v-model="deviceConfigForm.autoBattle" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="自动恢复">
              <el-switch v-model="deviceConfigForm.autoRecovery" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="自动复活">
              <el-switch v-model="deviceConfigForm.autoRevival" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="自动拾取">
              <el-switch v-model="deviceConfigForm.autoPickup" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showDeviceConfigDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDeviceConfig">保存配置</el-button>
      </template>
    </el-dialog>

    <!-- 选择设备启动 -->    <!-- 选择设备启动 -->
    <el-dialog v-model="showDeviceDialog" title="选择设备" width="450px">
      <el-form label-width="80px">
        <el-form-item label="选择设备">
          <el-select v-model="selectedDeviceId" placeholder="请选择设备" style="width:100%">
            <el-option v-for="dev in onlineDevices" :key="dev.id" :label="dev.deviceName + ' (' + dev.deviceId + ')'" :value="dev.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDeviceDialog = false">取消</el-button>
        <el-button :type="pendingSceneType === 'steal_card' ? 'warning' : 'primary'" @click="confirmStartScene">启动</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoPlay, VideoPause, Edit, Delete, Operation } from '@element-plus/icons-vue'
import {
  getBattleSceneList, addBattleScene, updateBattleScene, deleteBattleScene,
  startBattleScene, stopBattleScene, getBattleExecutionList, startSteal, stopSteal,
  getStealConfigByDevice, saveStealConfig, startStealByDevice, stopStealByDevice,
  getStealConfigList, getStealRunningDevices
} from '@/api/battle'
import { getDeviceList } from '@/api/device'

const router = useRouter()
const sceneList = ref([])
const runningTasks = ref([])
const allDevices = ref([])
const onlineDevices = ref([])
const showFormDialog = ref(false)
const formTab = ref('scene')
const showDeviceDialog = ref(false)
const isEdit = ref(false)
const editingSceneId = ref(null)
const selectedDeviceId = ref(null)

// 设备级配置状态
const showDeviceConfigDialog = ref(false)
const editingDeviceId = ref(null)
const deviceConfigs = reactive({})
const deviceRunning = reactive({})
const deviceConfigForm = reactive({
  deviceId: null, deviceName: '',
  gameType: 'dianka', gameArea: '', gameServer: '', roleName: '',
  characterLevel: null, characterTeam: 'single',
  configName: '偷卡配置',
  targetMonsters: '噬天虎,炎魔神,金饶僧',
  battleStrategy: {
    hpReplenish: '酒肆', mpReplenish: '酒肆',
    hpThreshold: 40, mpThreshold: 30,
    autoNavigate: true,
    battleOps: {
      '1_capture': true,
      '2_steal': true,
      '3_1_after_skill': true,
      '3_2_after_normal_attack': false,
      '3_3_after_defense': false,
      '3_4_direct_battle': false,
      '3_5_escape': false
    }
  },
  mapClickArea: '80,180,980,2200',
  templateConfidence: 0.80,
  walkInterval: 500,
  stealAttempts: 3,
  autoBattle: true, autoRecovery: true, autoRevival: true, autoPickup: true
})
const pendingSceneId = ref(null)
const pendingSceneType = ref('')
const runningSceneIds = ref({})
let pollTimer = null

function defaultStrategy() {
  return {
    hpReplenish: '酒肆',
    mpReplenish: '酒肆',
    hpThreshold: 40,
    mpThreshold: 30,
    autoNavigate: true,
    battleOps: {
      '1_capture': true,
      '2_steal': true,
      '3_1_after_skill': true,
      '3_2_after_normal_attack': false,
      '3_3_after_defense': false,
      '3_4_direct_battle': false,
      '3_5_escape': false
    }
  }
}

const form = reactive({
  sceneName: '', sceneType: 'pve', gameType: 'dianka',
  gameArea: '', gameServer: '', roleName: '',
  characterLevel: null, characterTeam: 'single',
  autoBattle: true, autoRecovery: true, autoRevival: true, autoPickup: true,
  deviceId: null,
  battleStrategy: defaultStrategy()
})

const rules = {
  sceneName: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
  sceneType: [{ required: true, message: '请选择场景类型', trigger: 'change' }],
  gameType: [{ required: true, message: '请选择区服', trigger: 'change' }]
}

const getSceneTagType = (t) => ({ pve: 'success', pvp: 'warning', dungeon: 'primary', boss: 'danger', steal_card: '' })[t] || 'info'
const getSceneTypeLabel = (t) => ({ pve: 'PVE', pvp: 'PVP', dungeon: '副本', boss: 'BOSS', steal_card: '偷卡' })[t] || '普通'
const getTaskStatusTag = (s) => ({ 0: 'info', 1: '', 2: 'success', 3: 'danger' })[s] || 'info'
const getTaskStatusLabel = (s) => ({ 0: '等待', 1: '执行中', 2: '成功', 3: '失败' })[s] || '未知'
const getProgressStatus = (p) => p >= 100 ? 'success' : p >= 50 ? '' : 'warning'
const formatDuration = (s) => { const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60); return h > 0 ? h + '小时' + m + '分钟' : m + '分钟' }
const isSceneRunning = (id) => !!runningSceneIds.value[id]
const getBoundDevice = (scene) => {
  if (!scene.deviceId) return null
  const dev = allDevices.value.find(d => d.id === scene.deviceId)
  return dev ? dev.deviceName : null
}

const loadScenes = async () => {
  try { const res = await getBattleSceneList(); sceneList.value = res.data || [] } catch (e) { /* */ }
}
const loadExecutions = async () => {
  try { const res = await getBattleExecutionList(); runningTasks.value = res.data || [] } catch (e) { /* */ }
}
const loadDevices = async () => {
  try {
    const res = await getDeviceList()
    allDevices.value = res.data || []
    onlineDevices.value = (res.data || []).filter(d => d.status === 'online' || d.status === 1)
  } catch (e) { /* */ }
}

const openAddDialog = () => {
  isEdit.value = false
  editingSceneId.value = null
  resetForm()
  showFormDialog.value = true
}

const editScene = (scene) => {
  isEdit.value = true
  editingSceneId.value = scene.id
  const strat = scene.battleStrategy ? JSON.parse(JSON.stringify(scene.battleStrategy)) : defaultStrategy()
  if (!strat.battleOps) strat.battleOps = defaultStrategy().battleOps
  Object.assign(form, {
    sceneName: scene.sceneName, sceneType: scene.sceneType, gameType: scene.gameType,
    gameArea: scene.gameArea, gameServer: scene.gameServer, roleName: scene.roleName,
    characterLevel: scene.characterLevel, characterTeam: scene.characterTeam,
    autoBattle: scene.autoBattle, autoRecovery: scene.autoRecovery,
    autoRevival: scene.autoRevival, autoPickup: scene.autoPickup,
    deviceId: scene.deviceId || null,
    battleStrategy: strat
  })
  showFormDialog.value = true
}

const deleteScene = async (scene) => {
  try {
    await ElMessageBox.confirm('确定要删除场景 "' + scene.sceneName + '" 吗？', '提示', { type: 'warning' })
    await deleteBattleScene(scene.id)
    ElMessage.success('删除成功')
    loadScenes()
  } catch (e) { /* cancelled */ }
}

const saveScene = async () => {
  try {
    if (isEdit.value) {
      await updateBattleScene(editingSceneId.value, { ...form })
      ElMessage.success('更新成功')
    } else {
      await addBattleScene({ ...form })
      ElMessage.success('创建成功')
    }
    showFormDialog.value = false
    loadScenes()
  } catch (e) { /* */ }
}

const startScene = (scene) => {
  pendingSceneId.value = scene.id
  pendingSceneType.value = scene.sceneType
  selectedDeviceId.value = scene.deviceId || null
  loadDevices()
  showDeviceDialog.value = true
}

const openStealDialog = (scene) => {
  pendingSceneId.value = scene.id
  pendingSceneType.value = 'steal_card'
  selectedDeviceId.value = scene.deviceId || null
  loadDevices()
  showDeviceDialog.value = true
}

const confirmStartScene = async () => {
  if (!selectedDeviceId.value) { ElMessage.warning('请选择设备'); return }
  try {
    if (pendingSceneType.value === 'steal_card') {
      await startSteal(pendingSceneId.value, selectedDeviceId.value)
      runningSceneIds.value[pendingSceneId.value] = true
      ElMessage.success('偷卡已启动')
    } else {
      await startBattleScene(pendingSceneId.value, selectedDeviceId.value)
      ElMessage.success('场景已启动')
    }
    showDeviceDialog.value = false
    loadExecutions()
  } catch (e) { ElMessage.error('启动失败') }
}

const stopStealScene = async (scene) => {
  try {
    await ElMessageBox.confirm('确定要停止偷卡场景 "' + scene.sceneName + '" 吗？', '提示', { type: 'warning' })
    await stopSteal(scene.id)
    delete runningSceneIds.value[scene.id]
    ElMessage.success('偷卡已停止')
    loadExecutions()
  } catch (e) { /* cancelled */ }
}

const stopTask = async (task) => {
  try {
    await ElMessageBox.confirm('确定要停止该任务吗？', '提示', { type: 'warning' })
    if (task.sceneType === 'steal_card') {
      await stopSteal(task.sceneId)
      delete runningSceneIds.value[task.sceneId]
    } else {
      await stopBattleScene(task.sceneId)
    }
    ElMessage.success('任务已停止')
    loadExecutions()
  } catch (e) { /* cancelled */ }
}

const viewTask = (task) => { router.push('/layout/battle/' + task.id) }

const afterOptions = [
  { key: '3_1_after_skill', label: '三、1.点选技能后自动战斗' },
  { key: '3_2_after_normal_attack', label: '2.普通攻击后自动战斗' },
  { key: '3_3_after_defense', label: '3.防御后自动战斗' },
  { key: '3_4_direct_battle', label: '4.直接自动战斗' },
  { key: '3_5_escape', label: '5.逃跑' }
]

const selectedAfterAction = computed({
  get() {
    const ops = form.battleStrategy.battleOps || {}
    return afterOptions.find(o => ops[o.key])?.key || '3_1_after_skill'
  },
  set(val) { selectAfterAction(val) }
})

const selectAfterAction = (key) => {
  const ops = form.battleStrategy.battleOps || {}
  afterOptions.forEach(o => { ops[o.key] = false })
  ops[key] = true
}

// 设备配置的战斗操作辅助
const deviceAfterAction = computed({
  get() {
    const ops = deviceConfigForm.battleStrategy.battleOps || {}
    return afterOptions.find(o => ops[o.key])?.key || '3_1_after_skill'
  },
  set(val) { selectDeviceAfterAction(val) }
})

const selectDeviceAfterAction = (key) => {
  const ops = deviceConfigForm.battleStrategy.battleOps || {}
  afterOptions.forEach(o => { ops[o.key] = false })
  ops[key] = true
}

const showStealSettingsDialog = ref(false)
const stealSettingsForm = reactive({
  stealScenes: []
})

const sceneOptions = [
  '龙窟五层', '凤巢四层', '子母河底', '小西天', '小雷音寺', '女娲神迹', '须弥东界', '银华镜'
]
const ringsOptions = ['得3个环', '得2个环', '得1个环']
const cardsOptions = ['无要求', '得1张卡片', '得2张卡片', '得3张卡片']
const minutesOptions = ['满180分钟', '满120分钟', '满60分钟']
const switchModeOptions = ['后换场景', '停止']

const defaultStealScenes = () => [
  { enabled: false, scene: '龙窟五层', rings: '得3个环', cards: '得2张卡片', minutes: '满180分钟', switchMode: '后换场景' },
  { enabled: false, scene: '凤巢四层', rings: '得3个环', cards: '无要求', minutes: '满180分钟', switchMode: '后换场景' },
  { enabled: false, scene: '子母河底', rings: '得3个环', cards: '无要求', minutes: '满180分钟', switchMode: '后换场景' },
  { enabled: false, scene: '小西天', rings: '得3个环', cards: '得2张卡片', minutes: '满180分钟', switchMode: '后换场景' },
  { enabled: true, scene: '小雷音寺', rings: '得3个环', cards: '得2张卡片', minutes: '满180分钟', switchMode: '后换场景' },
  { enabled: true, scene: '女娲神迹', rings: '得3个环', cards: '得2张卡片', minutes: '满180分钟', switchMode: '后换场景' },
  { enabled: false, scene: '须弥东界', rings: '得3个环', cards: '得2张卡片', minutes: '满180分钟', switchMode: '后换场景' },
  { enabled: false, scene: '银华镜', rings: '得3个环', cards: '得2张卡片', minutes: '满180分钟', switchMode: '后换场景' }
]

const openStealSettings = () => {
  const stealConfig = form.battleStrategy.stealConfig || {}
  stealSettingsForm.stealScenes = (stealConfig.stealScenes || defaultStealScenes()).map(s => ({ ...s }))
  showStealSettingsDialog.value = true
}


// ========== 设备级配置方法 ==========
const getDeviceConfigField = (deviceId, field) => {
  const c = deviceConfigs[deviceId]
  if (!c) return null
  if (field === 'targetMonsters') return c.targetMonsters
  return c[field]
}

const getDeviceConfigRunning = (deviceId) => {
  return !!deviceRunning[deviceId]
}

const loadDeviceConfigs = async () => {
  try {
    const res = await getStealConfigList()
    if (res.data) {
      for (const cfg of res.data) {
        deviceConfigs[cfg.deviceId] = cfg
      }
    }
  } catch (e) { /* ignore */ }
}

const loadDeviceRunningStatus = async () => {
  try {
    const res = await getStealRunningDevices()
    if (res.data) {
      // Clear old states
      Object.keys(deviceRunning).forEach(k => delete deviceRunning[k])
      for (const d of res.data) {
        deviceRunning[d.deviceId] = true
      }
    }
  } catch (e) { /* ignore */ }
}

const openDeviceConfigDialog = async (device) => {
  editingDeviceId.value = device.id
  try {
    const res = await getStealConfigByDevice(device.id)
    const cfg = res.data || {}
    const defaultOps = {
      '1_capture': true, '2_steal': true,
      '3_1_after_skill': true, '3_2_after_normal_attack': false,
      '3_3_after_defense': false, '3_4_direct_battle': false,
      '3_5_escape': false
    }
    const bs = cfg.battleStrategy || {}
    Object.assign(deviceConfigForm, {
      deviceId: device.id,
      deviceName: device.deviceName,
      gameType: bs.gameType || cfg.gameType || 'dianka',
      gameArea: bs.gameArea || cfg.gameArea || '',
      gameServer: bs.gameServer || cfg.gameServer || '',
      roleName: bs.roleName || cfg.roleName || '',
      characterLevel: bs.characterLevel || cfg.characterLevel || null,
      characterTeam: bs.characterTeam || cfg.characterTeam || 'single',
      configName: cfg.configName || '偷卡配置',
      targetMonsters: cfg.targetMonsters || '噬天虎,炎魔神,金饶僧',
      battleStrategy: {
        hpReplenish: bs.hpReplenish || '酒肆',
        mpReplenish: bs.mpReplenish || '酒肆',
        hpThreshold: bs.hpThreshold ?? 40,
        mpThreshold: bs.mpThreshold ?? 30,
        autoNavigate: bs.autoNavigate !== undefined ? !!bs.autoNavigate : true,
        battleOps: { ...defaultOps, ...(bs.battleOps || {}) }
      },
      mapClickArea: cfg.mapClickArea || '80,180,980,2200',
      templateConfidence: cfg.templateConfidence ?? 0.80,
      walkInterval: cfg.walkInterval || 500,
      stealAttempts: cfg.stealAttempts || 3,
      autoBattle: cfg.autoBattle !== undefined ? !!cfg.autoBattle : true,
      autoRecovery: cfg.autoRecovery !== undefined ? !!cfg.autoRecovery : true,
      autoRevival: cfg.autoRevival !== undefined ? !!cfg.autoRevival : true,
      autoPickup: cfg.autoPickup !== undefined ? !!cfg.autoPickup : true
    })
  } catch (e) { /* load failed */ }
  showDeviceConfigDialog.value = true
}

const saveDeviceConfig = async () => {
  if (!editingDeviceId.value) return
  try {
    const data = {
      configName: deviceConfigForm.configName,
      targetMonsters: deviceConfigForm.targetMonsters,
      battleStrategy: {
        ...deviceConfigForm.battleStrategy,
        gameType: deviceConfigForm.gameType,
        gameArea: deviceConfigForm.gameArea,
        gameServer: deviceConfigForm.gameServer,
        roleName: deviceConfigForm.roleName,
        characterLevel: deviceConfigForm.characterLevel,
        characterTeam: deviceConfigForm.characterTeam
      },
      mapClickArea: deviceConfigForm.mapClickArea,
      templateConfidence: deviceConfigForm.templateConfidence,
      walkInterval: deviceConfigForm.walkInterval,
      stealAttempts: deviceConfigForm.stealAttempts,
      autoBattle: deviceConfigForm.autoBattle ? 1 : 0,
      autoRecovery: deviceConfigForm.autoRecovery ? 1 : 0,
      autoRevival: deviceConfigForm.autoRevival ? 1 : 0,
      autoPickup: deviceConfigForm.autoPickup ? 1 : 0
    }
    const res = await saveStealConfig(editingDeviceId.value, data)
    // Update local cache
    deviceConfigs[editingDeviceId.value] = res.data || data
    ElMessage.success('设备配置已保存')
    showDeviceConfigDialog.value = false
  } catch (e) { ElMessage.error('保存失败') }
}

const startDeviceSteal = async (device) => {
  try {
    await startStealByDevice(device.id)
    deviceRunning[device.id] = true
    ElMessage.success(`已启动 ${device.deviceName} 偷卡`)
  } catch (e) { ElMessage.error('启动失败') }
}

const stopDeviceSteal = async (device) => {
  try {
    await ElMessageBox.confirm(`确定要停止 "${device.deviceName}" 的偷卡吗？`, '提示', { type: 'warning' })
    await stopStealByDevice(device.id)
    delete deviceRunning[device.id]
    ElMessage.success(`已停止 ${device.deviceName}`)
  } catch (e) { /* cancelled */ }
}
const saveStealSettings = () => {
  if (!form.battleStrategy.stealConfig) form.battleStrategy.stealConfig = {}
  form.battleStrategy.stealConfig.stealScenes = JSON.parse(JSON.stringify(stealSettingsForm.stealScenes))
  showStealSettingsDialog.value = false
  ElMessage.success('妙手空空设置已保存')
}

const resetForm = () => {
  Object.assign(form, {
    sceneName: '', sceneType: 'pve', gameType: 'dianka',
    gameArea: '', gameServer: '', roleName: '',
    characterLevel: null, characterTeam: 'single',
    autoBattle: true, autoRecovery: true, autoRevival: true, autoPickup: true,
    deviceId: null,
    battleStrategy: defaultStrategy()
  })
}

onMounted(() => {
  loadScenes()
  loadExecutions()
  loadDevices()
  loadDeviceConfigs()
  loadDeviceRunningStatus()
  pollTimer = setInterval(() => { loadExecutions(); loadDeviceRunningStatus() }, 3000)
})

onUnmounted(() => {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
})
</script>

<style scoped lang="scss">
.battle-page {
  .page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;
    .page-title { font-size:20px; font-weight:bold; }
  }
  .scene-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px;
    .scene-card {
      .scene-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;
        h3 { margin:0; font-size:16px; }
      }
      .scene-info { margin-bottom:15px;
        p { margin:5px 0; font-size:13px; color:#666; span { color:#999; } }
      }
      .scene-stats { display:flex; gap:15px; font-size:12px; color:#999; margin-bottom:15px; padding-bottom:15px; border-bottom:1px solid #eee; }
      .scene-actions { display:flex; gap:10px; .el-button { flex:1; } }
    }
  }
  .battle-ops-row { margin-top:10px; }
  .threshold-row { display:flex; align-items:center; gap:12px; width:100%;
    .el-slider { flex:1; }
    .threshold-value { min-width:40px; text-align:right; font-size:13px; color:#666; }
  }
  .battle-ops-section {
    .battle-ops-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px;
      .battle-ops-title { font-size:14px; font-weight:500; color:#333; margin:0; }
      .inline-auto-nav { margin-bottom:0;
        .el-form-item__content { line-height:32px; }
      }
    }
    .battle-ops-body { display:flex; flex-direction:column; gap:6px;
      .battle-op-item { width:100%; }
      .battle-op-item.vertical { width:100%; }
    }
    .battle-op-item {
      display:flex; align-items:center; justify-content:space-between;
      padding:8px 0; font-size:13px; color:#555;
      .el-switch { margin-left:auto; }
      .el-button { margin-left:8px; }
    }
    .battle-op-item.vertical {
      flex-direction:column; align-items:flex-start; justify-content:flex-start;
      .after-label { margin-bottom:8px; font-weight:500; color:#333; }
      .el-radio-group { display:flex; flex-direction:column; gap:8px; }
      .el-radio { height:auto; line-height:1.5; margin-right:0; }
    }
    .battle-op-item.vertical.after-options {
      padding-top:0;
      .after-option {
        display:flex; align-items:center; gap:10px;
        padding:6px 0; font-size:13px; color:#555; cursor:pointer;
        .el-switch { margin-left:0; }
        span { user-select:none; }
      }
      .after-option.active span { color:#409eff; }
    }
  }
}
.steal-settings-dialog {
  .steal-settings-subtitle { font-size:13px; color:#f56c6c; margin-bottom:18px; }
  .steal-scene-rows { display:flex; flex-direction:column; gap:10px; }
  .steal-scene-row {
    display:flex; align-items:center; gap:8px; font-size:13px; color:#555;
    .row-enable { margin-right:4px; }
    .row-label { min-width:48px; color:#666; }
    .row-select { width:120px; }
    .row-select.scene-select { width:120px; }
  }
}

.device-config-tab {
  .monster-preview {
    color: #409eff;
    font-size: 13px;
  }
}

.device-config-dialog {
  .el-form-item { margin-bottom: 16px; }
}
</style>
