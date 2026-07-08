# 梦幻西游自动化图色脚本系统

基于 Spring Boot + Vue 3 的梦幻西游自动化图色脚本管理平台。

## 📁 项目结构

```
mhxy-script-server/
├── src/
│   ├── main/
│   │   ├── java/com/mhxy/
│   │   │   ├── MhxyApplication.java     # 启动类
│   │   │   ├── config/                   # 配置类
│   │   │   ├── controller/              # 控制器
│   │   │   ├── entity/                  # 实体类
│   │   │   ├── dto/                     # 数据传输对象
│   │   │   ├── service/                 # 服务层
│   │   │   ├── mapper/                 # 数据访问层
│   │   │   ├── script/                 # 脚本控制器
│   │   │   └── util/                   # 工具类
│   │   └── resources/
│   │       └── application.yml         # 配置文件
│   └── test/                           # 测试类
│
├── vue-ui/                            # Vue前端项目
│   ├── src/
│   │   ├── api/                       # API接口
│   │   ├── views/                     # 页面组件
│   │   ├── router/                   # 路由配置
│   │   └── utils/                    # 工具函数
│   ├── package.json
│   └── vite.config.js
│
├── sql/                               # 数据库脚本
│   └── init.sql                      # 初始化SQL
│
├── templates/                         # 模板图片目录
├── screenshots/                      # 截图保存目录
└── README.md                         # 项目说明
```

## 🚀 快速开始

### 1. 数据库准备

```bash
# 登录MySQL
mysql -u root -p

# 执行初始化脚本
source D:/Program Files/mhxy/mhxy-script-server/sql/init.sql
```

**数据库信息:**
- 数据库名: `mhxy_script`
- 用户名: `root`
- 密码: `root`

### 2. 启动后端服务

```bash
cd "D:\Program Files\mhxy\mhxy-script-server"
mvn spring-boot:run
```

或双击 `启动项目.bat`

后端地址: http://localhost:8080

### 3. 启动前端服务

```bash
cd "D:\Program Files\mhxy\mhxy-script-server\vue-ui"
npm install
npm run dev
```

或双击 `启动前端.bat`

前端地址: http://localhost:3000

### 4. 访问系统

打开浏览器访问: http://localhost:3000

**默认账号:** admin / admin123

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

## 🔧 API接口

### 认证接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/logout` | POST | 用户登出 |
| `/api/auth/userinfo` | GET | 获取用户信息 |

### 设备接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/device/list` | GET | 获取设备列表 |
| `/api/device/{id}` | GET | 获取设备详情 |
| `/api/device` | POST | 添加设备 |
| `/api/device/{id}` | PUT | 更新设备 |
| `/api/device/{id}` | DELETE | 删除设备 |
| `/api/device/{id}/connect` | POST | 连接设备 |
| `/api/device/{id}/disconnect` | POST | 断开设备 |

### 打怪场景接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/battle/scene/list` | GET | 获取场景列表 |
| `/api/battle/scene/{id}` | GET | 获取场景详情 |
| `/api/battle/scene` | POST | 添加场景 |
| `/api/battle/scene/{id}` | PUT | 更新场景 |
| `/api/battle/scene/{id}` | DELETE | 删除场景 |
| `/api/battle/scene/{id}/start` | POST | 启动场景 |
| `/api/battle/scene/{id}/stop` | POST | 停止场景 |

### 图色脚本接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/script/screenshot/full` | GET | 全屏截图 |
| `/api/script/screenshot/region` | GET | 区域截图 |
| `/api/script/match/find` | GET | 查找模板 |
| `/api/script/action/findAndClick` | GET | 查找并点击 |
| `/api/script/mouse/click` | POST | 鼠标点击 |
| `/api/script/keyboard/type` | POST | 键盘输入 |

## 🛠️ 技术栈

### 后端
- Spring Boot 3.2.0
- MySQL 8.0
- MyBatis-Plus 3.5.5
- OpenCV 4.8.0
- Java AWT Robot

### 前端
- Vue 3.4
- Vue Router 4
- Pinia
- Element Plus
- Axios
- Vite 5

## 📋 数据库表

| 表名 | 说明 |
|------|------|
| sys_user | 用户表 |
| device | 设备表 |
| screenshot | 截图记录表 |
| recording | 录制任务表 |
| view_connection | 观看连接表 |
| battle_scene | 打怪场景配置表 |
| task_execution | 任务执行记录表 |
| template_image | 模板图片表 |
| operation_log | 操作日志表 |
| system_config | 系统配置表 |

## ⚠️ 注意事项

1. **数据库**: 确保MySQL服务已启动，并执行了 `sql/init.sql` 初始化脚本
2. **端口**: 后端占用8080端口，前端占用3000端口，确保端口未被占用
3. **依赖**: 前端需要Node.js (>= 16)，后端需要JDK 17+
4. **权限**: 部分功能需要管理员权限运行

## 📝 常用命令

```bash
# 后端构建
mvn clean package

# 后端运行
mvn spring-boot:run

# 前端安装依赖
npm install

# 前端开发
npm run dev

# 前端打包
npm run build
```

## 🔗 相关文档

- [前端项目README](./vue-ui/README.md)
- [Spring Boot文档](https://spring.io/projects/spring-boot)
- [Vue 3文档](https://vuejs.org/)
- [Element Plus文档](https://element-plus.org/)
