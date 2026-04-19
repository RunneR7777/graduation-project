<template>
    <v-row class="mb-4">
        <v-col class="text-right">
            <v-btn color="error" prepend-icon="mdi-file-document" @click="generateReport" :loading="isGenerating">
            自主生成安全分析报告 (PDF)
            </v-btn>
        </v-col>
        </v-row>

        <v-dialog v-model="showReportDialog" max-width="900px">
        <v-card>
            <v-card-title class="bg-primary text-white">
            校园网络 IPv6 流量智能安全分析报告
            </v-card-title>
            <v-card-text class="pa-6" style="min-height: 400px;">
            <div v-html="formattedReport" style="line-height: 1.8; font-size: 16px;"></div>
            </v-card-text>
            <v-card-actions class="pa-4">
            <v-spacer></v-spacer>
            <v-btn color="grey" variant="text" @click="showReportDialog = false">关闭</v-btn>
            <v-btn color="success" prepend-icon="mdi-printer" @click="exportPDF">直接打印/导出PDF</v-btn>
            </v-card-actions>
        </v-card>
        </v-dialog>
    <div class="ml-4">
        <v-card-title>
            <v-list-item-action>
                <v-icon class="teal--text">mdi-view-dashboard</v-icon>
            </v-list-item-action>
            <v-list-item-content class="ml-n3">
                <v-list-item-title class="teal--text">
                    <span>仪表盘</span>
                </v-list-item-title>
            </v-list-item-content>
        </v-card-title>

        <!-- 趋势图弹出对话框 -->
        <v-dialog 
            v-model="showTrendDialog" 
            max-width="900"
            @input="handleDialogChange"
            content-class="trend-dialog"
        >
            <v-card>
                <v-card-title class="headline">
                    安全风险趋势详情
                    <v-spacer></v-spacer>
                    <v-btn icon @click="showTrendDialog = false">
                        <v-icon>mdi-close</v-icon>
                    </v-btn>
                </v-card-title>
                <v-card-text>
                    <DashboardRiskTrend ref="riskTrend" />
                </v-card-text>
            </v-card>
        </v-dialog>

        <!-- 安全风险卡片 -->
        <v-row class="mr-8 ml-2 mt-2 mb-2">
            <v-col cols="12" sm="6" md="3" class="pa-2">
                <v-card
                    class="mx-auto dashboard-card elevation-3"
                    height="180"
                    @click="goToPath('/network/traffic')"
                    hover
                    style="cursor: pointer"
                    color="teal darken-1"
                >
                    <v-card-title class="d-flex justify-space-between align-center card-content">
                        <div class="white--text card-text-container">
                            <div class="d-flex align-center mb-4">
                                <v-icon left size="24" color="white">mdi-chart-timeline-variant</v-icon>
                                <span class="text-h6 font-weight-bold">流量流向</span>
                            </div>
                            <div class="text-body-1">
                                <div class="d-flex align-center mb-2">
                                    <span class="mr-2">活跃流数量:</span>
                                    <span class="text-h6 font-weight-bold">{{ dashboardStats.activeFlows }}</span>
                                </div>
                                <div class="d-flex align-center">
                                    <span class="mr-2">危险流数量:</span>
                                    <span class="text-h6 font-weight-bold red--text text--lighten-3">{{ dashboardStats.riskFlows }}</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-center justify-center progress-container">
                            <v-progress-circular
                                :value="dashboardStats.flowHealthScore"
                                size="80"
                                width="8"
                                :color="getProgressColor(dashboardStats.flowHealthScore)"
                                background-color="rgba(0, 121, 107, 0.5)"
                            >
                                <span class="text-h6 font-weight-bold white--text">{{ dashboardStats.flowHealthScore }}</span>
                            </v-progress-circular>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
            
            <v-col cols="12" sm="6" md="3" class="pa-2">
                <v-card
                    class="mx-auto dashboard-card elevation-3"
                    height="180"
                    @click="goToPath('/hosts/host-based')"
                    hover
                    style="cursor: pointer"
                    color="teal darken-1"
                >
                    <v-card-title class="d-flex justify-space-between align-center card-content">
                        <div class="white--text card-text-container">
                            <div class="d-flex align-center mb-4">
                                <v-icon left size="24" color="white">mdi-server-network</v-icon>
                                <span class="text-h6 font-weight-bold">主机</span>
                            </div>
                            <div class="text-body-1">
                                <div class="d-flex align-center mb-2">
                                    <span class="mr-2">本地主机数:</span>
                                    <span class="text-h6 font-weight-bold">{{ dashboardStats.localHosts }}</span>
                                </div>
                                <div class="d-flex align-center">
                                    <span class="mr-2">远程主机数:</span>
                                    <span class="text-h6 font-weight-bold">{{ dashboardStats.remoteHosts }}</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-center justify-center progress-container">
                            <div class="text-center white--text stat-container">
                                <div class="stat-value red--text text--lighten-3">{{ dashboardStats.riskHosts }}</div>
                                <div class="stat-label">危险主机</div>
                                <v-chip size="x-small" color="red lighten-4" text-color="red darken-4" class="mt-1">
                                    <v-icon size="x-small" class="mr-1">mdi-arrow-up</v-icon>{{ dashboardStats.riskHostsChange }}%
                                </v-chip>
                            </div>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
            
            <v-col cols="12" sm="6" md="3" class="pa-2">
                <v-card
                    class="mx-auto dashboard-card elevation-3"
                    height="180"
                    @click="goToPath('/address/statistics')"
                    hover
                    style="cursor: pointer"
                    color="teal darken-1"
                >
                    <v-card-title class="d-flex justify-space-between align-center card-content">
                        <div class="white--text card-text-container">
                            <div class="d-flex align-center mb-4">
                                <v-icon left size="24" color="white">mdi-ip-network</v-icon>
                                <span class="text-h6 font-weight-bold">活跃地址</span>
                            </div>
                            <div class="text-body-1">
                                <div class="d-flex align-center mb-2">
                                    <span class="mr-2">内部活跃地址:</span>
                                    <span class="text-h6 font-weight-bold">{{ dashboardStats.internalActiveAddresses }}</span>
                                </div>
                                <div class="d-flex align-center">
                                    <span class="mr-2">外部扫描地址:</span>
                                    <span class="text-h6 font-weight-bold">{{ dashboardStats.externalScanAddresses }}</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-center justify-center progress-container">
                            <div class="text-center white--text stat-container">
                                <div class="stat-value">{{ dashboardStats.totalActiveAddresses }}</div>
                                <div class="stat-label">总计</div>
                                <v-chip size="x-small" color="light-green lighten-4" text-color="light-green darken-4" class="mt-1">
                                    <v-icon size="x-small" class="mr-1">mdi-check-circle</v-icon>LIVE
                                </v-chip>
                            </div>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
            
            <v-col cols="12" sm="6" md="3" class="pa-2">
                <v-card
                    class="mx-auto dashboard-card elevation-3"
                    height="180"
                    @click="goToPath('/risk/ports')"
                    hover
                    style="cursor: pointer"
                    color="teal darken-1"
                >
                    <v-card-title class="d-flex justify-space-between align-center card-content">
                        <div class="white--text card-text-container">
                            <div class="d-flex align-center mb-4">
                                <v-icon left size="24" color="white">mdi-lan-connect</v-icon>
                                <span class="text-h6 font-weight-bold">端口</span>
                            </div>
                            <div class="text-body-1">
                                <div class="d-flex align-center mb-2">
                                    <span class="mr-2">端口数:</span>
                                    <span class="text-h6 font-weight-bold">{{ dashboardStats.totalPorts }}</span>
                                </div>
                                <div class="d-flex flex-wrap">
                                    <span class="mr-2">Top端口:</span>
                                    <v-chip x-small color="white" text-color="teal darken-3" class="mr-1 mb-1">22</v-chip>
                                    <v-chip x-small color="white" text-color="teal darken-3" class="mr-1 mb-1">80</v-chip>
                                    <v-chip x-small color="white" text-color="teal darken-3" class="mb-1">443</v-chip>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-center justify-center progress-container">
                            <v-progress-circular
                                :value="dashboardStats.portHealthScore"
                                size="80"
                                width="8"
                                :color="getProgressColor(dashboardStats.portHealthScore)"
                                background-color="rgba(0, 121, 107, 0.5)"
                            >
                                <span class="text-h6 font-weight-bold white--text">{{ dashboardStats.portHealthScore }}</span>
                            </v-progress-circular>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
        </v-row>
        
        <!-- 流量分析概览 -->
        <v-row class="mr-8 ml-2 mt-4">
            <v-col cols="12">
                <v-card>
                    <v-card-title>
                        <v-icon class="mr-2 teal--text">mdi-chart-timeline-variant</v-icon>
                        流量分析概览
                    </v-card-title>
                    <v-divider></v-divider>
                    <v-card-text>
                        <v-row>
                            <v-col cols="12" md="4">
                                <v-card outlined class="chart-card">
                                    <v-card-title class="subtitle-1">本地主机流量分布</v-card-title>
                                    <v-card-text>
                                        <div>
                                            <div ref="topHostsChart" style="width: 100%; height: 280px;"></div>
                                            <div v-if="topHostsLoading" class="text-center">
                                                <v-progress-circular indeterminate color="teal" size="20"></v-progress-circular>
                                            </div>
                                            <div v-if="topHostsError" class="text-center error--text">
                                                <small>{{ topHostsError }}</small>
                                            </div>
                                        </div>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                            
                            <v-col cols="12" md="4">
                                <v-card outlined class="chart-card">
                                    <v-card-title class="subtitle-1">应用协议分布</v-card-title>
                                    <v-card-text>
                                        <div>
                                            <div ref="topAppsChart" style="width: 100%; height: 280px;"></div>
                                            <div v-if="topAppsLoading" class="text-center">
                                                <v-progress-circular indeterminate color="teal" size="20"></v-progress-circular>
                                            </div>
                                            <div v-if="topAppsError" class="text-center error--text">
                                                <small>{{ topAppsError }}</small>
                                            </div>
                                        </div>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                            
                            <v-col cols="12" md="4">
                                <v-card outlined class="chart-card">
                                    <v-card-title class="subtitle-1">流量安全分类</v-card-title>
                                    <v-card-text>
                                        <div>
                                            <div ref="trafficClassChart" style="width: 100%; height: 280px;"></div>
                                            <div v-if="trafficClassLoading" class="text-center">
                                                <v-progress-circular indeterminate color="teal" size="20"></v-progress-circular>
                                            </div>
                                            <div v-if="trafficClassError" class="text-center error--text">
                                                <small>{{ trafficClassError }}</small>
                                            </div>
                                        </div>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row>
                        
                        <!-- Top5主机列表 -->
                        <v-row class="mt-4">
                            <v-col cols="12">
                                <v-card elevation="2" class="list-card">
                                    <v-card-title class="list-card-header py-4">
                                        <v-icon left color="white" size="22">mdi-server</v-icon>
                                        <span class="text-subtitle-1 font-weight-bold white--text">Top5主机</span>
                                        <v-spacer></v-spacer>
                                        <v-select
                                            v-model="hostFilter"
                                            :items="hostFilterOptions"
                                            label="主机类型"
                                            density="compact"
                                            variant="outlined"
                                            hide-details
                                            class="host-filter"
                                            style="max-width: 150px"
                                            bg-color="white"
                                        ></v-select>
                                    </v-card-title>
                                    <v-divider></v-divider>
                                    <v-card-text class="pa-0">
                                        <v-table class="elegant-table">
                                            <thead>
                                                <tr class="table-header">
                                                    <th class="text-left font-weight-bold">地址</th>
                                                    <th class="text-left font-weight-bold">ASN</th>
                                                    <th class="text-center font-weight-bold">流数</th>
                                                    <th class="text-center font-weight-bold">总字节数</th>
                                                    <th class="text-center font-weight-bold">流量占比</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="(host, index) in filteredTopHosts" :key="index" class="table-row">
                                                    <td class="text-body-2">
                                                        <v-chip size="small" color="teal lighten-5" text-color="teal darken-2" class="font-weight-medium">
                                                            {{ host.address }}
                                                        </v-chip>
                                                    </td>
                                                    <td>
                                                        <div class="d-flex align-center">
                                                            <v-icon size="small" color="blue-grey" class="mr-2">mdi-earth</v-icon>
                                                            <span class="text-body-2">{{ host.asnName }}</span>
                                                        </div>
                                                    </td>
                                                    <td class="text-center">
                                                        <v-chip size="small" variant="outlined" color="teal">{{ host.flows }}</v-chip>
                                                    </td>
                                                    <td class="text-center text-body-2 font-weight-medium">{{ host.totalBytes }}</td>
                                                    <td>
                                                        <div class="d-flex align-center justify-center">
                                                            <v-progress-linear
                                                                :model-value="host.activity"
                                                                height="10"
                                                                :color="getProgressColor(host.activity)"
                                                                bg-color="grey-lighten-3"
                                                                class="mr-3"
                                                                rounded
                                                                style="min-width: 100px"
                                                            ></v-progress-linear>
                                                            <span class="text-caption font-weight-bold">{{ host.activity }}%</span>
                                                        </div>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </v-table>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row>
                        
                        <!-- Top5前缀分布列表 -->
                        <!-- <v-row class="mt-4">
                            <v-col cols="12">
                                <v-card elevation="2" class="list-card">
                                    <v-card-title class="list-card-header py-4">
                                        <v-icon left color="white" size="22">mdi-ip-network</v-icon>
                                        <span class="text-subtitle-1 font-weight-bold white--text">Top5前缀分布</span>
                                        <v-spacer></v-spacer>
                                        <v-chip size="small" color="white" text-color="teal darken-2" class="font-weight-bold">
                                            <v-icon size="small" class="mr-1">mdi-ipv6</v-icon>
                                            IPv6
                                        </v-chip>
                                    </v-card-title>
                                    <v-divider></v-divider>
                                    <v-card-text class="pa-0">
                                        <v-table class="elegant-table">
                                            <thead>
                                                <tr class="table-header">
                                                    <th class="text-left font-weight-bold">前缀</th>
                                                    <th class="text-center font-weight-bold">类型</th>
                                                    <th class="text-center font-weight-bold">地址总数</th>
                                                    <th class="text-center font-weight-bold">活跃地址数</th>
                                                    <th class="text-center font-weight-bold">更新时间</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="(prefix, index) in topPrefixes" :key="index" class="table-row">
                                                    <td class="text-body-2">
                                                        <v-chip size="small" color="indigo lighten-5" text-color="indigo darken-2" class="font-weight-medium">
                                                            {{ prefix.prefix }}
                                                        </v-chip>
                                                    </td>
                                                    <td class="text-center">
                                                        <v-chip size="small" color="blue-grey lighten-4" text-color="blue-grey darken-2">
                                                            {{ prefix.type }}
                                                        </v-chip>
                                                    </td>
                                                    <td class="text-center">
                                                        <v-tooltip bottom>
                                                            <template v-slot:activator="{ props }">
                                                                <div v-bind="props" class="d-flex align-center justify-center">
                                                                    <span class="text-body-2 mr-2 font-weight-medium">{{ prefix.usageCount }}</span>
                                                                    <v-icon size="small" color="teal">mdi-information-outline</v-icon>
                                                                </div>
                                                            </template>
                                                            <span>该前缀理论上包含的地址总数</span>
                                                        </v-tooltip>
                                                    </td>
                                                    <td class="text-center">
                                                        <v-chip size="small" variant="outlined" color="green">{{ prefix.activeCount }}</v-chip>
                                                    </td>
                                                    <td class="text-center text-caption text-grey-darken-1">{{ prefix.updateTime }}</td>
                                                </tr>
                                            </tbody>
                                        </v-table>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row> -->
                        
                        <!-- 主要流量会话 -->
                        <v-row class="mt-4">
                            <v-col cols="12">
                                <v-card elevation="2" class="list-card">
                                    <v-card-title class="list-card-header py-4">
                                        <v-icon left color="white" size="22">mdi-connection</v-icon>
                                        <span class="text-subtitle-1 font-weight-bold white--text">主要流量会话</span>
                                        <v-spacer></v-spacer>
                                        <v-chip size="small" color="white" text-color="teal darken-2" class="font-weight-bold">
                                            <v-icon size="small" class="mr-1">mdi-clock-fast</v-icon>
                                            实时
                                        </v-chip>
                                    </v-card-title>
                                    <v-divider></v-divider>
                                    <v-card-text class="pa-0">
                                        <v-table class="elegant-table">
                                            <thead>
                                                <tr class="table-header">
                                                    <th class="text-left font-weight-bold" width="35%">源IP</th>
                                                    <th class="text-left font-weight-bold" width="25%">ASN</th>
                                                    <th class="text-left font-weight-bold" width="35%">目标IP</th>
                                                    <th class="text-center font-weight-bold" width="5%">状态</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr v-for="(flow, index) in topFlows" :key="index" class="table-row">
                                                    <td class="text-body-2 flow-cell">
                                                        <div class="d-flex align-center">
                                                            <v-icon size="small" color="blue" class="mr-2">mdi-arrow-right-circle</v-icon>
                                                            <span class="font-weight-medium text-truncate">{{ flow.source }}</span>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <div class="d-flex align-center">
                                                            <v-icon size="small" color="blue-grey" class="mr-2">mdi-earth</v-icon>
                                                            <span class="text-body-2">{{ flow.asn }}</span>
                                                        </div>
                                                    </td>
                                                    <td class="text-body-2 flow-cell">
                                                        <div class="d-flex align-center">
                                                            <v-icon size="small" color="orange" class="mr-2">mdi-bullseye-arrow</v-icon>
                                                            <span class="font-weight-medium text-truncate">{{ flow.destination }}</span>
                                                        </div>
                                                    </td>
                                                    <td class="text-center">
                                                        <v-chip size="small" color="success" variant="flat">
                                                            <v-icon size="x-small" class="mr-1">mdi-check-circle</v-icon>
                                                            活跃
                                                        </v-chip>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </v-table>
                                        <div class="pa-3 d-flex justify-end align-center bg-grey-lighten-5">
                                            <v-icon size="small" color="teal" class="mr-2">mdi-clock-outline</v-icon>
                                            <span class="text-caption text-grey-darken-1 mr-2">{{ currentTime }} - 更新中</span>
                                            <v-progress-circular
                                                indeterminate
                                                size="18"
                                                width="2"
                                                color="teal"
                                            ></v-progress-circular>
                                        </div>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
    </div>
</template>

<script setup lang="ts">
import { marked } from 'marked';
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useDashboardStore } from '@/stores/dashboard'
import DashboardRiskTrend from './DashboardRiskTrend.vue'
import * as echarts from 'echarts/core'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册 ECharts 组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  PieChart,
  CanvasRenderer
])

const router = useRouter()
const dashboardStore = useDashboardStore()

const isGenerating = ref(false);
const showReportDialog = ref(false);
const reportText = ref('');

// 将 Markdown 转换为 HTML
const formattedReport = computed(() => {
  return marked(reportText.value);
});

// 点击生成报告按钮
const generateReport = async () => {
  isGenerating.value = true;
  try {
    // 使用浏览器原生的 fetch 发送请求，绝对不会报错
    const response = await fetch('/api/report/generate');
    const res = await response.json();
    
    // 适配后端 Response.success 返回的格式 { status: { code: 200 }, data: { report: '...' } }
    if (res.status && res.status.code === 200) {
      reportText.value = res.data.report;
      showReportDialog.value = true;
    } else {
      alert('生成失败: ' + (res.status?.message || '未知错误'));
    }
  } catch (error) {
    console.error("生成报告出错:", error);
    alert('网络错误，无法连接到大模型接口');
  } finally {
    isGenerating.value = false;
  }
};

// 导出为 PDF 功能 
const exportPDF = () => {
  const printWindow = window.open('', '_blank');
  
  // 加上判空处理：如果浏览器拦截了弹窗，printWindow 就会是 null
  if (!printWindow) {
    alert('无法打开打印预览窗口，请检查浏览器是否拦截了弹出窗口！');
    return;
  }

  printWindow.document.write(`
    <html>
      <head>
        <title>校园网络 IPv6 安全分析报告</title>
        <style>
          body { font-family: 'Microsoft YaHei', sans-serif; padding: 40px; color: #333; line-height: 1.6; }
          h1, h2, h3 { color: #1976d2; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
        </style>
      </head>
      <body>
        ${formattedReport.value}
      </body>
    </html>
  `);
  printWindow.document.close();
  // 触发浏览器的打印弹窗
  setTimeout(() => { printWindow.print(); }, 500); 
};


// 响应式数据
const showTrendDialog = ref(false)
const riskTrend = ref<any>(null)

// 图表相关
const topHostsChart = ref<HTMLElement | null>(null)
const topAppsChart = ref<HTMLElement | null>(null)
const trafficClassChart = ref<HTMLElement | null>(null)

// ECharts 实例
const topHostsChartInstance = ref<any>(null)
const topAppsChartInstance = ref<any>(null)
const trafficClassChartInstance = ref<any>(null)

// 加载状态
const topHostsLoading = ref(false)
const topAppsLoading = ref(false)
const trafficClassLoading = ref(false)

// 错误状态
const topHostsError = ref<string | null>(null)
const topAppsError = ref<string | null>(null)
const trafficClassError = ref<string | null>(null)

// 主机筛选
const hostFilter = ref('all')
const hostFilterOptions = [
  { text: '所有主机', value: 'all' },
  { text: '本地主机', value: 'local' },
  { text: '远程主机', value: 'remote' }
]

// 数据
const topHosts = ref<any[]>([])
const topPrefixes = ref<any[]>([])
const topFlows = ref<any[]>([
  { 
    source: '2001:da8:215:3c0a:1552:a5f7:e564:c6d9', 
    asn: 'AS4538 (中国教育和科研计算机网)',
    destination: '240:cc0a9:1000:1:8'
  },
  {
    source: '2001:da8:215:8f01:ddde:77e:b226:cebd',
    asn: 'AS4538 (中国教育和科研计算机网)',
    destination: '240:cc0a9:1000:1:8'
  },
  {
    source: '2409:8a38:a617:d030:788d',
    asn: 'AS4134 (中国电信)',
    destination: '2001:da8:215:8f01:7f5f:a349:7fb9:e749'
  },
  {
    source: '2001:da8:215:3c0a:e542:bdc:a479:c443',
    asn: 'AS4538 (中国教育和科研计算机网)',
    destination: '2001:da8:201d:1108:578'
  }
])

const currentTime = ref(new Date().toLocaleString())

// 仪表盘统计数据
const dashboardStats = computed(() => ({
    activeFlows: 128,
    riskFlows: 12,
    flowHealthScore: 85,
    localHosts: 42,
    remoteHosts: 156,
    riskHosts: 8,
    riskHostsChange: 12,
    internalActiveAddresses: 86,
    externalScanAddresses: 23,
    totalActiveAddresses: 109,
    totalPorts: 238,
    portHealthScore: 72
}))

// 计算属性 - 筛选后的主机列表
const filteredTopHosts = computed(() => {
  if (hostFilter.value === 'all') {
    return topHosts.value.slice(0, 5)
  }
  const filtered = topHosts.value.filter((host: any) => host.type === hostFilter.value)
  return filtered.slice(0, 5)
})

// 方法
const goToPath = (path: string) => {
    router.push(path)
}

const handleDialogChange = (value: boolean) => {
    if (value && riskTrend.value) {
        // 当对话框打开时，刷新趋势图数据
        // riskTrend.value.refreshData()
    }
}

const getProgressColor = (value: number) => {
    if (value >= 90) return 'green lighten-1'
    if (value >= 70) return 'light-green lighten-1'
    if (value >= 50) return 'yellow lighten-1'
    if (value >= 30) return 'orange lighten-1'
    return 'red lighten-1'
}

// 初始化图表
const initCharts = async () => {
  await nextTick()
  initTopHostsChart()
  initTopAppsChart()
  initTrafficClassChart()
}

// 初始化本地主机流量分布图表
const initTopHostsChart = () => {
  if (!topHostsChart.value) return
  
  if (topHostsChartInstance.value) {
    topHostsChartInstance.value.dispose()
  }
  
  topHostsChartInstance.value = echarts.init(topHostsChart.value)
  fetchTopHostsData()
}

// 初始化应用协议分布图表
const initTopAppsChart = () => {
  if (!topAppsChart.value) return
  
  if (topAppsChartInstance.value) {
    topAppsChartInstance.value.dispose()
  }
  
  topAppsChartInstance.value = echarts.init(topAppsChart.value)
  fetchTopAppsData()
}

// 初始化流量安全分类图表
const initTrafficClassChart = () => {
  if (!trafficClassChart.value) return
  
  if (trafficClassChartInstance.value) {
    trafficClassChartInstance.value.dispose()
  }
  
  trafficClassChartInstance.value = echarts.init(trafficClassChart.value)
  fetchTrafficClassData()
}

// 获取本地主机流量数据
const fetchTopHostsData = async () => {
  try {
    topHostsLoading.value = true
    topHostsError.value = null
    
    await dashboardStore.fetchTopHostsChart()
    if (dashboardStore.topHostsChart) {
      updateTopHostsChart(dashboardStore.topHostsChart as any)
    }
    topHostsLoading.value = false
  } catch (error) {
    topHostsLoading.value = false
    topHostsError.value = '数据加载失败'
    console.error('Failed to fetch host data:', error)
  }
}

// 更新本地主机流量图表
const updateTopHostsChart = (data: any[]) => {
  if (!topHostsChartInstance.value || !data || data.length === 0) return
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 5,
      left: 'center',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 11 }
    },
    series: [
      {
        name: '主机流量占比',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        label: {
          show: true,
          position: 'inside',
          formatter: '{d}%',
          fontSize: 13,
          fontWeight: 'bold'
        },
        data: data,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    ],
    color: ['#1976D2', '#FF9800', '#4CAF50', '#E53935', '#9C27B0', '#607D8B']
  }
  
  topHostsChartInstance.value.setOption(option)
}

// 获取应用协议分布数据
const fetchTopAppsData = async () => {
  try {
    topAppsLoading.value = true
    topAppsError.value = null
    
    await dashboardStore.fetchTopAppsChart()
    if (dashboardStore.topAppsChart) {
      updateTopAppsChart(dashboardStore.topAppsChart as any)
    }
    topAppsLoading.value = false
  } catch (error) {
    topAppsLoading.value = false
    topAppsError.value = '数据加载失败'
    console.error('Failed to fetch app data:', error)
  }
}

// 更新应用协议分布图表
const updateTopAppsChart = (data: any[]) => {
  if (!topAppsChartInstance.value || !data || data.length === 0) return
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 5,
      left: 'center',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 11 }
    },
    series: [
      {
        name: '应用流量占比',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        label: {
          show: true,
          position: 'inside',
          formatter: '{d}%',
          fontSize: 13,
          fontWeight: 'bold'
        },
        data: data,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    ],
    color: ['#1976D2', '#FF9800', '#4CAF50', '#E53935', '#9C27B0', '#607D8B']
  }
  
  topAppsChartInstance.value.setOption(option)
}

// 获取流量安全分类数据
const fetchTrafficClassData = async () => {
  try {
    trafficClassLoading.value = true
    trafficClassError.value = null
    
    await dashboardStore.fetchTrafficClassChart()
    if (dashboardStore.trafficClassChart) {
      updateTrafficClassChart(dashboardStore.trafficClassChart as any)
    }
    trafficClassLoading.value = false
  } catch (error) {
    trafficClassLoading.value = false
    trafficClassError.value = '数据加载失败'
    console.error('Failed to fetch traffic class data:', error)
  }
}

// 更新流量安全分类图表
const updateTrafficClassChart = (data: any[]) => {
  if (!trafficClassChartInstance.value || !data || data.length === 0) return
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: 5,
      left: 'center',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { fontSize: 11 }
    },
    series: [
      {
        name: '流量分类',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        label: {
          show: true,
          position: 'inside',
          formatter: '{d}%',
          fontSize: 13,
          fontWeight: 'bold'
        },
        data: data,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    ],
    color: ['#4CAF50', '#FF9800', '#1976D2', '#E53935', '#9C27B0']
  }
  
  trafficClassChartInstance.value.setOption(option)
}

// 获取主机列表数据
const fetchTopHostsList = async () => {
  await dashboardStore.fetchTopHostsList()
  topHosts.value = dashboardStore.topHostsList
}

// 获取前缀分布数据
// const fetchTopPrefixesData = async () => {
//   await dashboardStore.fetchTopPrefixesChart()
// //   topPrefixes.value = dashboardStore.topPrefixesChart
// }

// 窗口大小调整处理
const handleResize = () => {
  if (topHostsChartInstance.value) topHostsChartInstance.value.resize()
  if (topAppsChartInstance.value) topAppsChartInstance.value.resize()
  if (trafficClassChartInstance.value) trafficClassChartInstance.value.resize()
}

// 组件挂载时
onMounted(() => {
    dashboardStore.fetchAllData()
  initCharts()
  fetchTopHostsList()
//   fetchTopPrefixesData()
  
  // 更新时间
  setInterval(() => {
    currentTime.value = new Date().toLocaleString()
  }, 1000)
  
  window.addEventListener('resize', handleResize)
})

// 组件卸载前
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  
  // 销毁图表实例
  if (topHostsChartInstance.value) {
    topHostsChartInstance.value.dispose()
    topHostsChartInstance.value = null
  }
  if (topAppsChartInstance.value) {
    topAppsChartInstance.value.dispose()
    topAppsChartInstance.value = null
  }
  if (trafficClassChartInstance.value) {
    trafficClassChartInstance.value.dispose()
    trafficClassChartInstance.value = null
  }
})
</script>

<style scoped>
.v-card {
    transition: all 0.3s ease;
}
.v-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.dashboard-card {
    overflow: hidden;
    position: relative;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 12px !important;
}

.dashboard-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 12px 24px rgba(0, 150, 136, 0.3) !important;
}

.card-content {
    height: 100%;
    padding: 20px;
    padding-top: 12px !important;
}

.card-text-container {
    flex: 1;
}

.progress-container {
    min-width: 100px;
    height: 100%;
    position: absolute;
    right: 16px;
    top: 0;
    bottom: 0;
}

.stat-container {
    width: 100%;
    background-color: rgba(0, 121, 107, 0.2);
    border-radius: 8px;
    padding: 12px 16px;
    min-width: 100px;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    line-height: 1;
    margin-bottom: 4px;
}

.stat-label {
    font-size: 0.85rem;
    opacity: 0.9;
    margin-bottom: 4px;
}

.trend-dialog {
    z-index: 1000;
}

.list-card {
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.list-card:hover {
    box-shadow: 0 4px 12px rgba(0, 121, 107, 0.1);
}

.host-row {
    background-color: rgba(0, 0, 0, 0.02);
}

.prefix-row {
    background-color: rgba(0, 0, 0, 0.02);
}

.flow-row {
    transition: background-color 0.3s ease;
}

.flow-row:hover {
    background-color: rgba(0, 150, 136, 0.05);
}

.flow-cell {
    max-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.flow-address {
    display: flex;
    align-items: center;
}

.flow-arrow {
    margin-right: 8px;
    color: #00897B;
    font-weight: bold;
}

.asn-info {
    display: flex;
    align-items: center;
    color: #616161;
    font-size: 0.9rem;
}

/* 图表容器样式 */
div[ref="topHostsChart"],
div[ref="topAppsChart"],
div[ref="trafficClassChart"] {
  min-height: 280px;
  position: relative;
}

@media (max-width: 600px) {
    .text-h6 {
        font-size: 1rem !important;
    }
    .text-h4 {
        font-size: 1.5rem !important;
    }
    .v-progress-circular {
        transform: scale(0.8);
    }
}
</style>