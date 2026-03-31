<template>
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
        <v-row class="mr-8 ml-2 mt-n4">
            <v-col cols="12" sm="3" md="3" class="mb-4">
                <v-card
                    class="mx-auto dashboard-card"
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
                                    <span class="text-h6 font-weight-bold">128</span>
                                </div>
                                <div class="d-flex align-center">
                                    <span class="mr-2">危险流数量:</span>
                                    <span class="text-h6 font-weight-bold red--text text--lighten-3">12</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-center justify-center progress-container">
                            <v-progress-circular
                                :value="85"
                                size="80"
                                width="8"
                                :color="getProgressColor(85)"
                                background-color="rgba(0, 121, 107, 0.5)"
                            >
                                <span class="text-h6 font-weight-bold white--text">85</span>
                            </v-progress-circular>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
            
            <v-col cols="12" sm="3" md="3" class="mb-4">
                <v-card
                    class="mx-auto dashboard-card"
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
                                    <span class="text-h6 font-weight-bold">42</span>
                                </div>
                                <div class="d-flex align-center">
                                    <span class="mr-2">远程主机数:</span>
                                    <span class="text-h6 font-weight-bold">156</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-center justify-center progress-container">
                            <div class="text-center white--text stat-container">
                                <div class="stat-value red--text text--lighten-3">8</div>
                                <div class="stat-label">危险主机</div>
                                <v-chip x-small color="red lighten-4" text-color="red darken-4" class="mt-1">
                                    <v-icon x-small left>mdi-arrow-up</v-icon>12%
                                </v-chip>
                            </div>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
            
            <v-col cols="12" sm="3" md="3" class="mb-4">
                <v-card
                    class="mx-auto dashboard-card"
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
                                    <span class="text-h6 font-weight-bold">86</span>
                                </div>
                                <div class="d-flex align-center">
                                    <span class="mr-2">外部扫描地址:</span>
                                    <span class="text-h6 font-weight-bold">23</span>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex align-center justify-center progress-container">
                            <div class="text-center white--text stat-container">
                                <div class="stat-value">109</div>
                                <div class="stat-label">总计</div>
                                <v-chip x-small color="light-green lighten-4" text-color="light-green darken-4" class="mt-1">
                                    <v-icon x-small left>mdi-check-circle</v-icon>LIVE
                                </v-chip>
                            </div>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
            
            <v-col cols="12" sm="3" md="3" class="mb-4">
                <v-card
                    class="mx-auto dashboard-card"
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
                                    <span class="text-h6 font-weight-bold">238</span>
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
                                :value="72"
                                size="80"
                                width="8"
                                :color="getProgressColor(72)"
                                background-color="rgba(0, 121, 107, 0.5)"
                            >
                                <span class="text-h6 font-weight-bold white--text">72</span>
                            </v-progress-circular>
                        </div>
                    </v-card-title>
                </v-card>
            </v-col>
        </v-row>
        
        <!-- 流量分析卡片 -->
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
                                <v-card outlined class="list-card">
                                    <v-card-title class="subtitle-1">
                                        <v-icon left color="teal">mdi-server</v-icon>
                                        Top5主机
                                        <v-spacer></v-spacer>
                                        <v-select
                                            v-model="hostFilter"
                                            :items="hostFilterOptions"
                                            label="主机类型"
                                            dense
                                            outlined
                                            hide-details
                                            class="host-filter"
                                            style="max-width: 150px"
                                        ></v-select>
                                    </v-card-title>
                                    <v-card-text class="pt-0">
                                        <v-simple-table>
                                            <template v-slot:default>
                                                <thead>
                                                    <tr class="teal lighten-5">
                                                        <th>地址</th>
                                                        <th>ASN</th>
                                                        <th>流数</th>
                                                        <th>总字节数</th>
                                                        <th>流量占比</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr v-for="(host, index) in filteredTopHosts" :key="index" class="host-row">
                                                        <td>{{ host.address }}</td>
                                                        <td>
                                                            <div class="asn-info">
                                                                <v-icon small color="grey darken-1" class="mr-1">mdi-earth</v-icon>
                                                                {{ host.asnName }}
                                                            </div>
                                                        </td>
                                                        <td>{{ host.flows }}</td>
                                                        <td>{{ host.totalBytes }}</td>
                                                        <td>
                                                            <div class="d-flex align-center">
                                                                <v-progress-linear
                                                                    :value="host.activity"
                                                                    height="8"
                                                                    :color="getProgressColor(host.activity)"
                                                                    background-color="grey lighten-3"
                                                                    class="mr-2"
                                                                ></v-progress-linear>
                                                                <span class="text-caption">{{ host.activity }}%</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </template>
                                        </v-simple-table>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row>
                        
                        <!-- Top5前缀分布列表 -->
                        <v-row class="mt-4">
                            <v-col cols="12">
                                <v-card outlined class="list-card">
                                    <v-card-title class="subtitle-1">
                                        <v-icon left color="teal">mdi-ip-network</v-icon>
                                        Top5前缀分布
                                        <v-spacer></v-spacer>
                                        <v-chip small color="teal lighten-1" text-color="white">IPv6</v-chip>
                                    </v-card-title>
                                    <v-card-text class="pt-0">
                                        <v-simple-table>
                                            <template v-slot:default>
                                                <thead>
                                                    <tr class="teal lighten-5">
                                                        <th>前缀</th>
                                                        <th>类型</th>
                                                        <th>地址总数</th>
                                                        <th>活跃地址数</th>
                                                        <th>更新时间</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr v-for="(prefix, index) in topPrefixes" :key="index" class="prefix-row">
                                                        <td>{{ prefix.prefix }}</td>
                                                        <td>{{ prefix.type }}</td>
                                                        <td>
                                                            <v-tooltip bottom>
                                                                <template v-slot:activator="{ on, attrs }">
                                                                    <div v-bind="attrs" v-on="on" class="d-flex align-center">
                                                                        <div class="text-caption mr-2">{{ prefix.usageCount }}</div>
                                                                        <v-icon x-small color="teal">mdi-information-outline</v-icon>
                                                                    </div>
                                                                </template>
                                                                <span>该前缀理论上包含的地址总数</span>
                                                            </v-tooltip>
                                                        </td>
                                                        <td>{{ prefix.activeCount }}</td>
                                                        <td>{{ prefix.updateTime }}</td>
                                                    </tr>
                                                </tbody>
                                            </template>
                                        </v-simple-table>
                                    </v-card-text>
                                </v-card>
                            </v-col>
                        </v-row>
                        
                        <!-- 主要流量会话 -->
                        <v-row class="mt-4">
                            <v-col cols="12">
                                <v-card outlined class="list-card">
                                    <v-card-title class="subtitle-1">
                                        <v-icon left color="teal">mdi-connection</v-icon>
                                        主要流量会话
                                        <v-spacer></v-spacer>
                                        <v-chip small color="teal" text-color="white">实时</v-chip>
                                    </v-card-title>
                                    <v-card-text class="pt-0">
                                        <v-simple-table>
                                            <template v-slot:default>
                                                <thead>
                                                    <tr class="teal lighten-5">
                                                        <th width="30%">源IP</th>
                                                        <th width="30%">ASN</th>
                                                        <th width="30%">目标IP</th>
                                                        <th width="10%">状态</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    <tr v-for="(flow, index) in topFlows" :key="index" class="flow-row">
                                                        <td class="flow-cell">{{ flow.source }}</td>
                                                        <td>
                                                            <div class="asn-info">
                                                                <v-icon small color="grey darken-1" class="mr-1">mdi-earth</v-icon>
                                                                {{ flow.asn }}
                                                            </div>
                                                        </td>
                                                        <td class="flow-cell">
                                                            <div class="flow-address">
                                                                <div class="flow-arrow">→</div>
                                                                {{ flow.destination }}
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <v-chip x-small color="success" class="text-center">活跃</v-chip>
                                                        </td>
                                                    </tr>
                                                </tbody>
                                            </template>
                                        </v-simple-table>
                                        <div class="text-right grey--text caption d-flex justify-end align-center mt-2">
                                            <v-icon x-small class="mr-1">mdi-clock-outline</v-icon>
                                            {{ currentTime }} - 更新中
                                            <v-progress-circular
                                                indeterminate
                                                size="16"
                                                width="2"
                                                color="teal"
                                                class="ml-2"
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

<script>
import DashboardRiskTrend from "./DashboardRiskTrend";
import * as echarts from 'echarts/core';
import { PieChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import dashboardApi from '@/components/http/apis/dashboard_api';

echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  PieChart,
  CanvasRenderer
]);

export default {
    name: "Dashboard",
    components: {
        DashboardRiskTrend
    },
    data: () => ({
        showTrendDialog: false,
        spinShow: true,
        riskCards: [],
        hostFilter: 'all',
        hostFilterOptions: [
            { text: '所有主机', value: 'all' },
            { text: '本地主机', value: 'local' },
            { text: '远程主机', value: 'remote' }
        ],
        topHostsByRisk: [
            { ip: "192.168.1.105", location: "教学楼-3楼", riskCount: 18, riskLevel: "high" },
            { ip: "192.168.1.87", location: "行政楼-2楼", riskCount: 12, riskLevel: "high" },
            { ip: "192.168.2.45", location: "宿舍区-6号楼", riskCount: 9, riskLevel: "medium" },
            { ip: "192.168.3.201", location: "图书馆", riskCount: 7, riskLevel: "medium" },
            { ip: "192.168.4.18", location: "实验室-A区", riskCount: 5, riskLevel: "low" }
        ],
        topHostsByConnections: [
            { ip: "192.168.1.1", location: "网关", connections: 18243 },
            { ip: "192.168.1.10", location: "主服务器", connections: 7652 },
            { ip: "192.168.2.15", location: "文件服务器", connections: 3487 },
            { ip: "192.168.3.100", location: "数据库服务器", connections: 2156 },
            { ip: "192.168.4.50", location: "邮件服务器", connections: 1893 }
        ],
        topFlows: [
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
        ],
        currentTime: '04/03/2025 01:07:14',
        
        // 主机列表数据
        topHosts: [],
        topHostsListLoading: false,
        topHostsListError: null,
        
        // 新增的Top5前缀分布数据
        topPrefixes: [],
        topPrefixesLoading: false,
        topPrefixesError: null,
        topPrefixesFetchTimer: null,

        // TopHosts组件数据
        topHostsChart: null,
        hostData: [],
        topHostsLoading: false,
        topHostsError: null,
        topHostsFetchTimer: null,

        // TopApps组件数据
        topAppsChart: null,
        appData: [],
        topAppsLoading: false,
        topAppsError: null,
        topAppsFetchTimer: null,

        // TrafficClass组件数据
        trafficClassChart: null,
        trafficData: [],
        trafficClassLoading: false,
        trafficClassError: null,
        trafficClassFetchTimer: null
    }),
    mounted() {
        this.getDashboardData();
        this.initCharts();
        this.fetchAllChartData();
        this.fetchTopHostsList();
        this.fetchTopPrefixesData();
        
        // 每5分钟自动刷新一次数据
        this.topHostsFetchTimer = setInterval(this.fetchTopHostsData, 300000);
        this.topAppsFetchTimer = setInterval(this.fetchTopAppsData, 300000);
        this.trafficClassFetchTimer = setInterval(this.fetchTrafficClassData, 300000);
        this.topPrefixesFetchTimer = setInterval(this.fetchTopPrefixesData, 300000);
        
        window.addEventListener('resize', this.handleResize);
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize);
        
        if (this.topHostsFetchTimer) {
            clearInterval(this.topHostsFetchTimer);
        }
        if (this.topAppsFetchTimer) {
            clearInterval(this.topAppsFetchTimer);
        }
        if (this.trafficClassFetchTimer) {
            clearInterval(this.trafficClassFetchTimer);
        }
        if (this.topPrefixesFetchTimer) {
            clearInterval(this.topPrefixesFetchTimer);
        }
        
        if (this.topHostsChart) {
            this.topHostsChart.dispose();
            this.topHostsChart = null;
        }
        if (this.topAppsChart) {
            this.topAppsChart.dispose();
            this.topAppsChart = null;
        }
        if (this.trafficClassChart) {
            this.trafficClassChart.dispose();
            this.trafficClassChart = null;
        }
    },
    methods: {
        goToPath(path){
            this.$router.push(path);
        },
        async getDashboardData() {
            // 添加模拟数据
            const mockData = {
                high_risk_count: 15,
                port_risk_count: 238,
                privacy_level: 68
            };
            this.updateRiskCards(mockData);
        },
        updateRiskCards(data) {
            this.riskCards = [
                {
                    type: 'high-risk-addr',
                    text: "IPv6高风险地址",
                    activeCount: data.high_risk_count,
                    totalCount: 28642,
                    percentage: (data.high_risk_count / 28642) * 100,
                    source: "校园网核心区域",
                    icon: "mdi-ip-network",
                    path: "/address/address-monitoring",
                    color: "teal darken-1"
                },
                {
                    type: 'port-risk',
                    text: "暴露高危端口",
                    value: data.port_risk_count,
                    topPorts: [
                        {name: "22(SSH)", count: Math.floor(data.port_risk_count * 0.32)},
                        {name: "3389(RDP)", count: Math.floor(data.port_risk_count * 0.22)}
                    ],
                    icon: "mdi-lan-connect",
                    path: "/risk/ports",
                    color: "teal darken-1"
                },
                {
                    type: 'privacy-level',
                    text: "随机化地址占比",
                    safePercentage: data.privacy_level,
                    trend: "提升12%",
                    trendIcon: "mdi-arrow-up",
                    trendColor: "green-darken-1",
                    icon: "mdi-shield-check",
                    path: "/network/ipv6",
                    color: "teal darken-1"
                }
            ];
        },
        riskLevelColor(level) {
            const colors = {
                high: "red",
                medium: "orange",
                low: "blue"
            };
            return colors[level] || "grey";
        },
        riskLevelIcon(level) {
            const icons = {
                high: "mdi-alert-circle",
                medium: "mdi-alert",
                low: "mdi-information"
            };
            return icons[level] || "mdi-help-circle";
        },
        handleDialogChange(val) {
            if (val && this.$refs.riskTrend) {
                // 对话框打开时，完全重新初始化图表
                setTimeout(() => {
                    if (this.$refs.riskTrend.chart) {
                        this.$refs.riskTrend.chart.dispose();
                    }
                    this.$refs.riskTrend.initChart();
                    
                    // 确保数据被加载
                    setTimeout(() => {
                        if (!this.$refs.riskTrend.chart || 
                            !this.$refs.riskTrend.chartOptions.series[0].data || 
                            this.$refs.riskTrend.chartOptions.series[0].data.length === 0) {
                            this.$refs.riskTrend.fetchTrendData();
                        }
                        
                        // 再次延迟调整大小，确保渲染完成
                        setTimeout(() => {
                            this.$refs.riskTrend.resizeChart();
                        }, 200);
                    }, 200);
                }, 300);
            }
        },
        handleResize() {
            this.resizeAllCharts();
        },
        getProgressColor(value) {
            if (value >= 90) return 'green lighten-1';
            if (value >= 70) return 'light-green lighten-1';
            if (value >= 50) return 'yellow lighten-1';
            if (value >= 30) return 'orange lighten-1';
            return 'red lighten-1';
        },
        initCharts() {
            this.initTopHostsChart();
            this.initTopAppsChart();
            this.initTrafficClassChart();
        },
        fetchAllChartData() {
            this.fetchTopHostsData();
            this.fetchTopAppsData();
            this.fetchTrafficClassData();
        },
        resizeAllCharts() {
            if (this.topHostsChart) this.topHostsChart.resize();
            if (this.topAppsChart) this.topAppsChart.resize();
            if (this.trafficClassChart) this.trafficClassChart.resize();
        },
        // 新增方法，获取主机列表数据
        async fetchTopHostsList() {
            try {
                this.topHostsListLoading = true;
                this.topHostsListError = null;
                
                try {
                    const response = await dashboardApi.getTopHostsList();
                    console.log('TopHostsList API response:', response);
                    
                    // 处理不同的响应格式
                    if (response.data && response.data.data) {
                        this.topHosts = response.data.data;
                    } else if (response.data) {
                        // 如果后端直接返回 {'data': [...]}
                        this.topHosts = response.data;
                    }
                    
                    if (!this.topHosts || this.topHosts.length === 0) {
                        throw new Error('未获取到主机列表数据');
                    }
                } catch (apiError) {
                    console.error('API调用失败，使用模拟数据:', apiError);
                    // 提供模拟数据避免列表为空
                    this.topHosts = [
                        { address: '2001:da8:215:3c0a:1552:a5f7:e564:c6d9', name: '主服务器', flows: 128, duration: '24h 12m', throughput: '12.5 Mbps', totalBytes: '156.8 GB', type: 'local' },
                        { address: '2001:da8:215:8f01:ddde:77e:b226:cebd', name: '数据库服务器', flows: 96, duration: '23h 45m', throughput: '8.2 Mbps', totalBytes: '98.3 GB', type: 'local' },
                        { address: '2409:8a38:a617:d030:788d', name: '文件服务器', flows: 84, duration: '22h 30m', throughput: '7.8 Mbps', totalBytes: '87.2 GB', type: 'remote' },
                        { address: '2001:da8:215:3c0a:e542:bdc:a479:c443', name: '网关', flows: 76, duration: '24h 00m', throughput: '6.5 Mbps', totalBytes: '78.1 GB', type: 'local' },
                        { address: '2001:da8:201d:1108:578', name: '备份服务器', flows: 62, duration: '18h 20m', throughput: '5.2 Mbps', totalBytes: '62.4 GB', type: 'remote' }
                    ];
                }
                
                this.topHostsListLoading = false;
            } catch (error) {
                this.topHostsListLoading = false;
                this.topHostsListError = '主机列表数据加载失败';
                console.error('Failed to fetch host list data:', error);
            }
        },
        initTopHostsChart() {
            this.topHostsChart = echarts.init(this.$refs.topHostsChart);
            window.addEventListener('resize', this.resizeTopHostsChart);
        },
        resizeTopHostsChart() {
            if (this.topHostsChart) {
                this.topHostsChart.resize();
            }
        },
        async fetchTopHostsData() {
            try {
                this.topHostsLoading = true;
                this.topHostsError = null;
                
                try {
                    const response = await dashboardApi.getTopHostsChart();
                    console.log('TopHosts API response:', response);
                    
                    // 处理不同的响应格式
                    if (response.data && response.data.data) {
                        this.hostData = response.data.data;
                    } else if (response.data) {
                        // 如果后端直接返回 {'data': [...]}
                        this.hostData = response.data;
                    }
                    
                    if (this.hostData && this.hostData.length > 0) {
                        this.updateTopHostsChart();
                    } else {
                        throw new Error('未获取到数据');
                    }
                } catch (apiError) {
                    console.error('API调用失败，使用模拟数据:', apiError);
                    // 提供模拟数据避免图表不显示
                    this.hostData = [
                        { value: 35, name: '192.168.1.105' },
                        { value: 25, name: '192.168.1.87' },
                        { value: 15, name: '192.168.2.45' },
                        { value: 12, name: '192.168.3.201' },
                        { value: 8, name: '192.168.4.18' },
                        { value: 5, name: 'Other' }
                    ];
                    this.updateTopHostsChart();
                }
                
                this.topHostsLoading = false;
            } catch (error) {
                this.topHostsLoading = false;
                this.topHostsError = '数据加载失败';
                console.error('Failed to fetch host data:', error);
            }
        },
        updateTopHostsChart() {
            if (!this.hostData || this.hostData.length === 0) {
                return;
            }
            
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
                    textStyle: {
                        fontSize: 11
                    },
                    formatter: function(name) {
                        if (name.length > 15) {
                            return name.substring(0, 15) + '...';
                        }
                        return name;
                    }
                },
                series: [
                    {
                        name: '主机流量占比',
                        type: 'pie',
                        radius: ['45%', '70%'],
                        center: ['50%', '45%'],
                        avoidLabelOverlap: true,
                        label: {
                            show: true,
                            position: 'inside',
                            formatter: '{d}%',
                            fontSize: 13,
                            fontWeight: 'bold'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: 16,
                                fontWeight: 'bold'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: this.hostData,
                        itemStyle: {
                            borderRadius: 5,
                            borderColor: '#fff',
                            borderWidth: 2
                        }
                    }
                ],
                color: ['#1976D2', '#FF9800', '#4CAF50', '#E53935', '#9C27B0', '#607D8B']
            };

            this.topHostsChart.setOption(option);
        },
        initTopAppsChart() {
            this.topAppsChart = echarts.init(this.$refs.topAppsChart);
            window.addEventListener('resize', this.resizeTopAppsChart);
        },
        resizeTopAppsChart() {
            if (this.topAppsChart) {
                this.topAppsChart.resize();
            }
        },
        async fetchTopAppsData() {
            try {
                this.topAppsLoading = true;
                this.topAppsError = null;
                
                try {
                    const response = await dashboardApi.getTopAppsChart();
                    console.log('TopApps API response:', response);
                    
                    // 处理不同的响应格式
                    if (response.data && response.data.data) {
                        this.appData = response.data.data;
                    } else if (response.data) {
                        // 如果后端直接返回 {'data': [...]}
                        this.appData = response.data;
                    }
                    
                    if (this.appData && this.appData.length > 0) {
                        this.updateTopAppsChart();
                    } else {
                        throw new Error('未获取到数据');
                    }
                } catch (apiError) {
                    console.error('API调用失败，使用模拟数据:', apiError);
                    // 提供模拟数据避免图表不显示
                    this.appData = [
                        { value: 30, name: 'HTTP' },
                        { value: 25, name: 'HTTPS/TLS' }, 
                        { value: 15, name: 'DNS' },
                        { value: 10, name: 'SSH' },
                        { value: 8, name: 'SMTP' },
                        { value: 12, name: 'Other' }
                    ];
                    this.updateTopAppsChart();
                }
                
                this.topAppsLoading = false;
            } catch (error) {
                this.topAppsLoading = false;
                this.topAppsError = '数据加载失败';
                console.error('Failed to fetch app data:', error);
            }
        },
        updateTopAppsChart() {
            if (!this.appData || this.appData.length === 0) {
                return;
            }
            
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
                    textStyle: {
                        fontSize: 11
                    },
                    formatter: function(name) {
                        if (name.length > 15) {
                            return name.substring(0, 15) + '...';
                        }
                        return name;
                    }
                },
                series: [
                    {
                        name: '应用流量占比',
                        type: 'pie',
                        radius: ['45%', '70%'],
                        center: ['50%', '45%'],
                        avoidLabelOverlap: true,
                        label: {
                            show: true,
                            position: 'inside',
                            formatter: '{d}%',
                            fontSize: 13,
                            fontWeight: 'bold'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: 16,
                                fontWeight: 'bold'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: this.appData,
                        itemStyle: {
                            borderRadius: 5,
                            borderColor: '#fff',
                            borderWidth: 2
                        }
                    }
                ],
                color: ['#1976D2', '#FF9800', '#4CAF50', '#E53935', '#9C27B0', '#607D8B']
            };

            this.topAppsChart.setOption(option);
        },
        initTrafficClassChart() {
            this.trafficClassChart = echarts.init(this.$refs.trafficClassChart);
            window.addEventListener('resize', this.resizeTrafficClassChart);
        },
        resizeTrafficClassChart() {
            if (this.trafficClassChart) {
                this.trafficClassChart.resize();
            }
        },
        async fetchTrafficClassData() {
            try {
                this.trafficClassLoading = true;
                this.trafficClassError = null;
                
                try {
                    const response = await dashboardApi.getTrafficClassChart();
                    if (response.data && response.data.data) {
                        this.trafficData = response.data.data;
                        this.updateTrafficClassChart();
                    } else {
                        throw new Error('未获取到数据');
                    }
                } catch (apiError) {
                    console.error('API调用失败，使用模拟数据:', apiError);
                    // 提供模拟数据避免图表不显示
                    this.trafficData = [
                        { value: 65, name: '安全流量' },
                        { value: 15, name: '危险流量' },
                        { value: 20, name: '未知流量' }
                    ];
                    this.updateTrafficClassChart();
                }
                
                this.trafficClassLoading = false;
            } catch (error) {
                this.trafficClassLoading = false;
                this.trafficClassError = '数据加载失败';
                console.error('Failed to fetch traffic class data:', error);
            }
        },
        updateTrafficClassChart() {
            if (!this.trafficData || this.trafficData.length === 0) {
                return;
            }
            
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
                    textStyle: {
                        fontSize: 11
                    },
                    formatter: function(name) {
                        if (name.length > 15) {
                            return name.substring(0, 15) + '...';
                        }
                        return name;
                    }
                },
                series: [
                    {
                        name: '流量分类',
                        type: 'pie',
                        radius: ['45%', '70%'],
                        center: ['50%', '45%'],
                        avoidLabelOverlap: true,
                        label: {
                            show: true,
                            position: 'inside',
                            formatter: '{d}%',
                            fontSize: 13,
                            fontWeight: 'bold'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: 16,
                                fontWeight: 'bold'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: this.trafficData,
                        itemStyle: {
                            borderRadius: 5,
                            borderColor: '#fff',
                            borderWidth: 2
                        }
                    }
                ],
                color: ['#4CAF50', '#FF9800', '#1976D2', '#E53935', '#9C27B0']
            };

            this.trafficClassChart.setOption(option);
        },
        async fetchTopPrefixesData() {
            try {
                this.topPrefixesLoading = true;
                this.topPrefixesError = null;
                
                const response = await dashboardApi.getTopPrefixesChart();
                console.log('TopPrefixes API response:', response);
                
                if (response.data && response.data.data) {
                    this.topPrefixes = response.data.data;
                } else if (response.data) {
                    // 如果后端直接返回 {'data': [...]}
                    this.topPrefixes = response.data;
                } else {
                    throw new Error('未获取到数据');
                }
                
                if (!this.topPrefixes || this.topPrefixes.length === 0) {
                    throw new Error('前缀数据为空');
                }
                
                this.topPrefixesLoading = false;
            } catch (error) {
                this.topPrefixesLoading = false;
                this.topPrefixesError = '数据加载失败';
                console.error('Failed to fetch top prefixes data:', error);
                
                // 提供模拟数据避免列表为空
                this.topPrefixes = [
                    {
                        prefix: '2001:da8::/32',
                        type: '全局单播',
                        generation: 'EUI-64',
                        activeCount: 156,
                        activeRate: '85%',
                        matchCriteria: '精确匹配',
                        updateTime: new Date().toLocaleString()
                    },
                    {
                        prefix: '240::/8',
                        type: '全局单播',
                        generation: '随机',
                        activeCount: 98,
                        activeRate: '72%',
                        matchCriteria: '精确匹配',
                        updateTime: new Date().toLocaleString()
                    },
                    {
                        prefix: '2001:da8:215:3c0a::/64',
                        type: '全局单播',
                        generation: 'EUI-64',
                        activeCount: 87,
                        activeRate: '68%',
                        matchCriteria: '精确匹配',
                        updateTime: new Date().toLocaleString()
                    },
                    {
                        prefix: '2001:da8:215:8f01::/64',
                        type: '全局单播',
                        generation: '随机',
                        activeCount: 65,
                        activeRate: '62%',
                        matchCriteria: '精确匹配',
                        updateTime: new Date().toLocaleString()
                    },
                    {
                        prefix: '2409:8a38::/32',
                        type: '全局单播',
                        generation: '随机',
                        activeCount: 45,
                        activeRate: '58%',
                        matchCriteria: '精确匹配',
                        updateTime: new Date().toLocaleString()
                    }
                ];
            }
        }
    },
    computed: {
        filteredTopHosts() {
            // 确保返回顶部5个主机，即使是经过筛选的
            if (this.hostFilter === 'all') {
                return this.topHosts.slice(0, 5);
            }
            
            // 先按照主机类型筛选，然后返回最多5个结果
            const filtered = this.topHosts.filter(host => host.type === this.hostFilter);
            return filtered.slice(0, 5);
        }
    }
}
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
}

.v-card-title {
    padding: 16px !important;
}

.v-card-title .d-flex.align-center.mb-4 {
    margin-bottom: 24px !important;
}

.v-card-title .text-body-1 {
    margin-top: 0 !important;
}

.v-card-title .d-flex.align-center.justify-center {
    margin-top: 0 !important;
    height: 100% !important;
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

/* 添加进度环容器样式 */
.progress-container {
    height: 100%;
    position: absolute;
    right: 16px;
    top: 0;
    bottom: 0;
}

/* 添加卡片内容样式 */
.card-content {
    height: 100%;
    padding-top: 12px !important;
}

.list-card {
    border-radius: 8px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.list-card:hover {
    box-shadow: 0 4px 12px rgba(0, 121, 107, 0.1);
}

.list-card .v-card__title {
    padding: 16px !important;
}

.list-card .v-card__title .d-flex.align-center.mb-4 {
    margin-bottom: 24px !important;
}

.list-card .v-card__title .text-body-1 {
    margin-top: 0 !important;
}

.list-card .v-card__title .d-flex.align-center.justify-center {
    margin-top: 0 !important;
    height: 100% !important;
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

.flow-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 8px;
}

.flow-dot-1 {
    background-color: #00897B;
}

.flow-dot-2 {
    background-color: #26A69A;
}

.flow-dot-3 {
    background-color: #4DB6AC;
}

.flow-dot-4 {
    background-color: #80CBC4;
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

.rank-indicator {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    color: white;
}

.rank-1 {
    background-color: #00897B;
}

.rank-2 {
    background-color: #26A69A;
}

.rank-3 {
    background-color: #4DB6AC;
}

.rank-4 {
    background-color: #80CBC4;
}

.rank-5 {
    background-color: #B2DFDB;
    color: #00695C;
}

/* 表头样式 */
.v-data-table thead th {
    font-weight: bold !important;
    color: #00695C !important;
}

/* 进度条样式 */
.v-progress-linear {
    border-radius: 4px;
    overflow: hidden;
}

/* 添加统计数据容器样式 */
.stat-container {
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

/* 图表容器样式 */
div[ref="topHostsChart"],
div[ref="topAppsChart"],
div[ref="trafficClassChart"] {
  min-height: 280px;
  position: relative;
}
</style>