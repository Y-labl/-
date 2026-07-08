<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ 'is-collapse': isCollapse }">
      <div class="logo">
        <span v-if="!isCollapse">MHXY脚本</span>
        <span v-else>MH</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        :collapse="isCollapse"
        router
      >
        <el-menu-item index="/layout/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>控制台</template>
        </el-menu-item>
        
        <el-menu-item index="/layout/devices">
          <el-icon><Monitor /></el-icon>
          <template #title>设备管理</template>
        </el-menu-item>
        
        <el-menu-item index="/layout/screenshot">
          <el-icon><Camera /></el-icon>
          <template #title>截图管理</template>
        </el-menu-item>
        
        <el-menu-item index="/layout/view">
          <el-icon><VideoCamera /></el-icon>
          <template #title>观看画面</template>
        </el-menu-item>
        
        <el-menu-item index="/layout/recording">
          <el-icon><VideoPlay /></el-icon>
          <template #title>录制管理</template>
        </el-menu-item>
        
        <el-sub-menu index="battle">
          <template #title>
            <el-icon><Operation /></el-icon>
            <span>打怪场景</span>
          </template>
          <el-menu-item index="/layout/battle">场景列表</el-menu-item>
          <el-menu-item index="/layout/template">模板管理</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/layout/settings">
          <el-icon><Setting /></el-icon>
          <template #title>系统设置</template>
        </el-menu-item>
      </el-menu>
    </div>
    
    <!-- 主内容区 -->
    <div class="main-container">
      <div class="header">
        <div class="header-left">
          <el-icon class="toggle-btn" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/layout/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span>{{ userInfo.username }}</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { logout } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)

const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))

const activeMenu = computed(() => route.path)

const currentTitle = computed(() => {
  return route.meta?.title || ''
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleCommand = async (command) => {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning'
    })
    await logout()
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    router.push('/login')
  } else if (command === 'profile') {
    // 个人中心
  }
}
</script>

<style scoped lang="scss">
.layout-container {
  height: 100vh;
  display: flex;
  
  .sidebar {
    width: 200px;
    background: #304156;
    transition: width 0.3s;
    overflow: hidden;
    
    &.is-collapse {
      width: 64px;
      
      .logo span {
        font-size: 18px;
      }
    }
    
    .logo {
      height: 60px;
      line-height: 60px;
      text-align: center;
      background: #263445;
      color: #fff;
      font-size: 16px;
      font-weight: bold;
      letter-spacing: 2px;
    }
    
    .menu {
      border-right: none;
    }
  }
  
  .main-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    
    .header {
      height: 60px;
      background: #fff;
      border-bottom: 1px solid #e6e6e6;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      
      .header-left {
        display: flex;
        align-items: center;
        
        .toggle-btn {
          font-size: 20px;
          cursor: pointer;
          margin-right: 15px;
          color: #666;
          
          &:hover {
            color: #409eff;
          }
        }
      }
      
      .header-right {
        .user-info {
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          padding: 5px 10px;
          border-radius: 4px;
          
          &:hover {
            background: #f5f5f5;
          }
        }
      }
    }
    
    .content {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      background: #f0f2f5;
    }
  }
}
</style>
