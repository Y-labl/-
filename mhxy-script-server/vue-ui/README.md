# 梦幻西游自动化脚本 - Vue前端

基于 Vue 3 + Element Plus 的自动化图色脚本管理平台。

## 📁 项目结构

```
vue-ui/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口
│   │   ├── auth.js        # 认证相关
│   │   ├── battle.js      # 打怪场景
│   │   ├── device.js      # 设备管理
│   │   ├── recording.js   # 录制管理
│   │   └── screenshot.js  # 截图管理
│   ├── assets/            # 资源文件
│   │   └── styles.scss    # 全局样式
│   ├── components/        # 公共组件
│   ├── router/            # 路由配置
│   ├── utils/             # 工具函数
│   │   └── request.js     # Axios封装
│   ├── views/             # 页面组件
│   │   ├── Login.vue      # 登录页
│   │   ├── Layout.vue     # 布局组件
│   │   ├── Dashboard.vue  # 控制台
│   │   ├── Devices.vue    # 设备管理
│   │   ├── Screenshot.vue # 截图管理
│   │   ├── View.vue       # 观看画面
│   │   ├── Recording.vue  # 录制管理
│   │   ├── Battle.vue      # 打怪场景
│   │   ├── BattleDetail.vue # 场景详情
│   │   ├── Template.vue   # 模板管理
│   │   └── Settings.vue   # 系统设置
│   ├── App.vue            # 根组件
│   └── main.js            # 入口文件
├── index.html             # HTML模板
├── package.json           # 项目配置
├── vite.config.js         # Vite配置
└── 启动前端.bat           # 启动脚本
```

## 🚀 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

或双击 `启动前端.bat`

### 3. 访问页面

打开浏览器访问: http://localhost:3000

默认账号: admin / admin123

## 📱 功能模块

### 1. 控制台
- 系统运行状态概览
- 设备状态监控
- 任务执行统计
- 快捷操作入口

### 2. 设备管理
- 设备列表展示
- 设备连接/断开
- 设备信息配置
- 实时画面预览

### 3. 截图管理
- 全屏截图
- 区域截图
- 截图历史
- 模板提取

### 4. 观看画面
- 实时画面查看
- 鼠标键盘控制
- 快捷操作按钮
- 画质切换

### 5. 录制管理
- 开始/停止录制
- 录制参数配置
- 录制历史
- 文件下载

### 6. 打怪场景
- 场景配置管理
- 一键启动
- 实时监控
- 执行日志

### 7. 模板管理
- 模板上传
- 分类管理
- 匹配测试
- 使用统计

### 8. 系统设置
- 基本设置
- 截图设置
- 录制设置
- 打怪设置

## 🔧 配置说明

### API代理配置

在 `vite.config.js` 中配置API代理:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true
    }
  }
}
```

### 主题配置

在 `src/main.js` 中配置Element Plus主题:

```javascript
import 'element-plus/dist/index.css'
```

## 📦 技术栈

- Vue 3.4
- Vue Router 4
- Pinia
- Element Plus
- Axios
- Vite 5
- SCSS

## 🛠️ 构建发布

```bash
# 开发环境
npm run dev

# 生产环境打包
npm run build

# 预览打包结果
npm run preview
```

## ⚠️ 注意事项

1. 确保后端服务已启动 (默认 http://localhost:8080)
2. 首次运行需要安装Node.js (>= 16)
3. 部分功能需要设备连接后才能使用
