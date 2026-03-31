# 🚀 FuXi网络分析系统 - 前端v3

## 📋 项目概述

基于 **Vue 3 + TypeScript + Vuetify 3** 的现代化前端项目，提供网络流量分析、主机监控、风险评估等功能。

## ✨ 技术栈

- **框架**: Vue 3.4 + Composition API
- **语言**: TypeScript 4.9
- **UI库**: Vuetify 3.4
- **状态管理**: Pinia 2.1
- **路由**: Vue Router 4.2
- **图表**: ECharts 5.6 + vue-echarts 6.7
- **HTTP**: Axios 1.6
- **构建工具**: Vite 4.4

## 🎯 核心功能

### 1. 仪表盘
- 实时流量统计
- Top主机/应用分析
- 流量趋势图表
- 风险监控面板

### 2. 网络分析
- 流量监控与分析
- IPv6地址分析
- 活跃IP检测
- 地理位置可视化

### 3. 主机管理
- 本地/远程主机管理
- AS分布分析
- 国家分布统计
- 主机风险评估

### 4. 地址分析
- IPv6地址模式识别
- 地址活跃度监控
- 可疑地址检测
- 地址统计分析

### 5. ChatAI
- 智能数据分析
- MCP协议支持
- 多智能体系统
- 自然语言查询

### 6. 风险评估
- 危险主机检测
- 端口风险分析
- 风险趋势监控
- 安全告警

## 📁 项目结构

```
frontend_v3/
├── src/
│   ├── services/          # API服务层 ✅
│   │   ├── request.ts     # Axios配置
│   │   ├── dashboardApi.ts
│   │   ├── networkApi.ts
│   │   ├── hostsApi.ts
│   │   ├── addressApi.ts
│   │   ├── chataiApi.ts
│   │   ├── riskApi.ts
│   │   ├── authApi.ts
│   │   ├── settingApi.ts
│   │   ├── discoveryApi.ts
│   │   └── index.ts
│   │
│   ├── composables/       # 组合式函数 ✅
│   │   ├── useHosts.ts
│   │   ├── useAddress.ts
│   │   └── useRisk.ts
│   │
│   ├── components/        # Vue组件
│   │   ├── common/        # 通用组件
│   │   ├── charts/        # 图表组件
│   │   └── forms/         # 表单组件
│   │
│   ├── views/             # 页面组件
│   │   ├── dashboard/     # 仪表盘
│   │   ├── network/       # 网络分析
│   │   ├── hosts/         # 主机管理
│   │   ├── address/       # 地址分析
│   │   ├── chatai/        # ChatAI
│   │   └── risk/          # 风险评估
│   │
│   ├── layout/            # 布局组件 ✅
│   │   ├── SideBar.vue
│   │   ├── TopToolbar.vue
│   │   ├── Content.vue
│   │   └── DashboardLayout.vue
│   │
│   ├── types/             # TypeScript类型 ✅
│   │   ├── api.ts
│   │   └── sidebar.ts
│   │
│   ├── utils/             # 工具函数 ✅
│   │   ├── message.ts     # 消息提示
│   │   ├── format.ts      # 格式化工具
│   │   └── sidebar.ts     # 侧边栏配置
│   │
│   ├── stores/            # Pinia状态 ✅
│   │   ├── dashboard.ts
│   │   └── traffic.ts
│   │
│   ├── router/            # 路由配置 ✅
│   │   └── index.ts
│   │
│   ├── plugins/           # 插件配置 ✅
│   │   └── vuetify.ts
│   │
│   └── App.vue            # 根组件 ✅
│
├── public/                # 静态资源
├── vite.config.ts         # Vite配置 ✅
├── package.json           # 依赖配置 ✅
├── tsconfig.json          # TypeScript配置
├── test_api.html          # API测试页面 ✅
└── README.md              # 本文件

✅ = 已完成
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /home/ui/frontend_v3
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

服务将在 `http://localhost:3000` 启动

### 3. 构建生产版本

```bash
npm run build
```

## 🔧 配置说明

### API配置

**开发环境**：通过Vite代理自动转发到后端
```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:5001',
    changeOrigin: true
  }
}
```

**生产环境**：使用相对路径，由Nginx等反向代理处理
```typescript
// src/services/request.ts
let API_PATH = "/api/"
```

### 环境变量

创建 `.env.development` 文件：
```bash
# API基础地址（使用相对路径）
VITE_API_BASE_URL=/api/

# 应用标题
VITE_APP_TITLE=FuXi网络分析系统
```

## 📝 可用脚本

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 代码检查
npm run lint

# 类型检查
vue-tsc --noEmit
```

## 🧪 API测试

### 方法1: 使用测试页面（推荐）

```bash
# 启动开发服务器
npm run dev

# 在浏览器中打开
http://localhost:3000/test_api.html
```

### 方法2: 命令行测试

```bash
# 测试仪表盘API
curl http://localhost:3000/api/dashboard/top-hosts-chart

# 测试网络流量API
curl http://localhost:3000/api/network/traffic/stats
```

## 📚 文档

- [API使用文档](./README_API.md) - API服务使用指南
- [前后端请求流程详解](./前后端请求流程详解.md) - 完整请求流程
- [快速排错指南](./快速排错指南.md) - 问题排查方法
- [API完整性验证](./API完整性验证.md) - API对比和测试
- [重构计划文档](./重构计划文档.md) - 重构详细计划
- [实施指南](./实施指南.md) - 具体实施步骤

## 🎯 使用示例

### 在组件中使用API

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { dashboardApi } from '@/services'

const loadData = async () => {
  const response = await dashboardApi.getTopHostsChart()
  console.log(response.data)
}

onMounted(() => {
  loadData()
})
</script>
```

### 使用Composables

```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useHosts } from '@/composables/useHosts'

const {
  hosts,
  loading,
  fetchHostBasedTraffic
} = useHosts()

onMounted(() => {
  fetchHostBasedTraffic()
})
</script>
```

## 🐛 常见问题

### Q: 出现 ERR_CONNECTION_REFUSED 错误？

**A**: 检查 `src/services/request.ts` 是否使用相对路径：
```typescript
let API_PATH = "/api/"  // ✅ 正确
// 不要使用: "http://localhost:5001/api/" ❌
```

### Q: API请求404错误？

**A**: 
1. 确保后端服务运行在 5001 端口
2. 检查Vite代理配置
3. 验证后端API路径是否正确

### Q: 如何重启服务？

**A**:
```bash
# 停止当前服务 (Ctrl+C)
# 重新启动
npm run dev
```

## 🔍 API完整性

- ✅ 仪表盘API (7个方法)
- ✅ 网络流量API (18个方法)
- ✅ 主机分析API (5个方法)
- ✅ 地址分析API (5个方法)
- ✅ ChatAI API (15个方法)
- ✅ 风险评估API (4个方法)
- ✅ 认证API (4个方法)
- ✅ 系统设置API (7个方法)
- ✅ 主动发现API (23个方法)

**总计**: 88个API方法，100%完成 🎉

## 💡 开发建议

1. ✅ 优先使用 Composables 封装业务逻辑
2. ✅ 使用 TypeScript 类型确保类型安全
3. ✅ 使用相对路径发送API请求
4. ✅ 利用格式化工具统一数据展示
5. ✅ 充分利用响应拦截器处理错误

## 🌐 浏览器支持

- Chrome/Edge >= 90
- Firefox >= 88
- Safari >= 14

## 📞 技术支持

如有问题，请查看：
1. [前后端请求流程详解](./前后端请求流程详解.md)
2. [快速排错指南](./快速排错指南.md)
3. 运行 `/tmp/check_api.sh` 检查配置

---

**版本**: v3.0.0  
**最后更新**: 2024-10-02  
**状态**: ✅ 生产就绪

