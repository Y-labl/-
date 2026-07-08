<template>
  <div class="settings-page">
    <div class="page-header">
      <h2 class="page-title">系统设置</h2>
    </div>
    
    <el-row :gutter="20">
      <!-- 基本设置 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">基本设置</span>
          </div>
          <el-form :model="basicSettings" label-width="120px">
            <el-form-item label="应用名称">
              <el-input v-model="basicSettings.appName" />
            </el-form-item>
            <el-form-item label="主题">
              <el-radio-group v-model="basicSettings.theme">
                <el-radio label="light">浅色</el-radio>
                <el-radio label="dark">深色</el-radio>
                <el-radio label="auto">跟随系统</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="语言">
              <el-select v-model="basicSettings.language">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      
      <!-- 截图设置 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">截图设置</span>
          </div>
          <el-form :model="screenshotSettings" label-width="120px">
            <el-form-item label="保存路径">
              <el-input v-model="screenshotSettings.savePath">
                <template #append>
                  <el-button @click="selectPath">选择</el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="保存天数">
              <el-input-number 
                v-model="screenshotSettings.saveDays" 
                :min="1" 
                :max="365"
              />
              <span style="margin-left: 10px; color: #999">天</span>
            </el-form-item>
            <el-form-item label="图片格式">
              <el-select v-model="screenshotSettings.format">
                <el-option label="PNG" value="png" />
                <el-option label="JPEG" value="jpg" />
              </el-select>
            </el-form-item>
            <el-form-item label="匹配阈值">
              <el-slider 
                v-model="screenshotSettings.matchThreshold" 
                :min="0.5" 
                :max="1" 
                :step="0.01"
                show-input
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveScreenshotSettings">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      
      <!-- 录制设置 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">录制设置</span>
          </div>
          <el-form :model="recordingSettings" label-width="120px">
            <el-form-item label="保存路径">
              <el-input v-model="recordingSettings.savePath">
                <template #append>
                  <el-button @click="selectPath">选择</el-button>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item label="保存天数">
              <el-input-number 
                v-model="recordingSettings.saveDays" 
                :min="1" 
                :max="30"
              />
              <span style="margin-left: 10px; color: #999">天</span>
            </el-form-item>
            <el-form-item label="默认分辨率">
              <el-select v-model="recordingSettings.resolution">
                <el-option label="1920x1080" value="1920x1080" />
                <el-option label="1280x720" value="1280x720" />
                <el-option label="854x480" value="854x480" />
              </el-select>
            </el-form-item>
            <el-form-item label="默认帧率">
              <el-select v-model="recordingSettings.fps">
                <el-option label="60 FPS" :value="60" />
                <el-option label="30 FPS" :value="30" />
                <el-option label="15 FPS" :value="15" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveRecordingSettings">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      
      <!-- 打怪设置 -->
      <el-col :span="12">
        <div class="card">
          <div class="card-header">
            <span class="card-title">打怪设置</span>
          </div>
          <el-form :model="battleSettings" label-width="120px">
            <el-form-item label="自动重试">
              <el-input-number 
                v-model="battleSettings.autoRetry" 
                :min="0" 
                :max="10"
              />
              <span style="margin-left: 10px; color: #999">次</span>
            </el-form-item>
            <el-form-item label="重试间隔">
              <el-input-number 
                v-model="battleSettings.retryInterval" 
                :min="1" 
                :max="60"
              />
              <span style="margin-left: 10px; color: #999">秒</span>
            </el-form-item>
            <el-form-item label="操作间隔">
              <el-input-number 
                v-model="battleSettings.actionInterval" 
                :min="100" 
                :max="2000"
                :step="100"
              />
              <span style="margin-left: 10px; color: #999">毫秒</span>
            </el-form-item>
            <el-form-item label="截图延迟">
              <el-input-number 
                v-model="battleSettings.screenshotDelay" 
                :min="0" 
                :max="5000"
                :step="100"
              />
              <span style="margin-left: 10px; color: #999">毫秒</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveBattleSettings">保存</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
    
    <!-- 关于 -->
    <div class="card about-card">
      <div class="card-header">
        <span class="card-title">关于</span>
      </div>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="应用名称">
          梦幻西游自动化脚本
        </el-descriptions-item>
        <el-descriptions-item label="版本号">
          v1.0.0
        </el-descriptions-item>
        <el-descriptions-item label="开发者">
          MHXY Team
        </el-descriptions-item>
        <el-descriptions-item label="联系方式">
          support@mhxy.com
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'

const basicSettings = reactive({
  appName: '梦幻西游自动化脚本',
  theme: 'light',
  language: 'zh-CN'
})

const screenshotSettings = reactive({
  savePath: 'D:/mhxy/screenshots',
  saveDays: 30,
  format: 'png',
  matchThreshold: 0.85
})

const recordingSettings = reactive({
  savePath: 'D:/mhxy/recordings',
  saveDays: 7,
  resolution: '1920x1080',
  fps: 30
})

const battleSettings = reactive({
  autoRetry: 3,
  retryInterval: 5,
  actionInterval: 300,
  screenshotDelay: 500
})

const selectPath = () => {
  // 选择路径
}

const saveBasicSettings = () => {
  ElMessage.success('基本设置已保存')
}

const saveScreenshotSettings = () => {
  ElMessage.success('截图设置已保存')
}

const saveRecordingSettings = () => {
  ElMessage.success('录制设置已保存')
}

const saveBattleSettings = () => {
  ElMessage.success('打怪设置已保存')
}
</script>

<style scoped lang="scss">
.settings-page {
  .page-header {
    margin-bottom: 20px;
    
    .page-title {
      font-size: 20px;
      font-weight: bold;
    }
  }
  
  .about-card {
    margin-top: 20px;
  }
}
</style>
