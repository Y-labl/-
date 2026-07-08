import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/layout/dashboard'
  },
  {
    path: '/dashboard',
    redirect: '/layout/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/layout',
    component: () => import('@/views/Layout.vue'),
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '控制台' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/Devices.vue'),
        meta: { title: '设备管理' }
      },
      {
        path: 'screenshot',
        name: 'Screenshot',
        component: () => import('@/views/Screenshot.vue'),
        meta: { title: '截图管理' }
      },
      {
        path: 'view',
        name: 'View',
        component: () => import('@/views/View.vue'),
        meta: { title: '观看画面' }
      },
      {
        path: 'recording',
        name: 'Recording',
        component: () => import('@/views/Recording.vue'),
        meta: { title: '录制管理' }
      },
      {
        path: 'battle',
        name: 'Battle',
        component: () => import('@/views/Battle.vue'),
        meta: { title: '打怪场景' }
      },
      {
        path: 'battle/:id',
        name: 'BattleDetail',
        component: () => import('@/views/BattleDetail.vue'),
        meta: { title: '场景详情' }
      },
      {
        path: 'template',
        name: 'Template',
        component: () => import('@/views/Template.vue'),
        meta: { title: '模板管理' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
