<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="red--text mr-2">mdi-shield-alert</v-icon>
      <span class="red--text">端口风险分析</span>
      <v-spacer></v-spacer>
      <v-btn
        color="success"
        @click="exportData"
        :loading="exportLoading"
        prepend-icon="mdi-download"
        class="mr-2"
      >
        导出报告
      </v-btn>
      <v-btn
        color="primary"
        @click="refreshData"
        :loading="loading"
        prepend-icon="mdi-refresh"
      >
        重新扫描
      </v-btn>
    </v-card-title>

    <!-- 风险统计卡片 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="blue" size="32" class="mr-3">mdi-lan-connect</v-icon>
              <div>
                <div class="text-h6">{{ portStats.totalPorts }}</div>
                <div class="text-subtitle2 text-grey">扫描端口总数</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="green" size="32" class="mr-3">mdi-lan-check</v-icon>
              <div>
                <div class="text-h6">{{ portStats.openPorts }}</div>
                <div class="text-subtitle2 text-grey">开放端口</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="orange" size="32" class="mr-3">mdi-alert</v-icon>
              <div>
                <div class="text-h6">{{ portStats.riskPorts }}</div>
                <div class="text-subtitle2 text-grey">风险端口</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="red" size="32" class="mr-3">mdi-shield-alert</v-icon>
              <div>
                <div class="text-h6">{{ portStats.highRiskPorts }}</div>
                <div class="text-subtitle2 text-grey">高危端口</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 风险警报 -->
    <v-alert 
      v-if="portStats.highRiskPorts > 0"
      type="error" 
      class="mb-4"
      prominent
    >
      <v-icon left>mdi-alert-circle</v-icon>
      <strong>高危警报！</strong> 发现 {{ portStats.highRiskPorts }} 个高危端口，建议立即处理
    </v-alert>

    <!-- 筛选器 -->
    <v-card class="mb-4">
      <v-card-title>端口筛选</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.riskLevel"
              :items="riskLevelOptions"
              label="风险等级"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.protocol"
              :items="protocolOptions"
              label="协议"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.portRange"
              label="端口范围 (如: 80-8080)"
              clearable
              @input="debouncedSearch"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.service"
              label="服务名称"
              clearable
              @input="debouncedSearch"
            ></v-text-field>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 端口风险列表 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="portRiskList"
          :loading="loading"
          :items-length="total"
          :items-per-page="pagination.itemsPerPage"
          :page="pagination.page"
          loading-text="加载数据中..."
          no-data-text="暂无风险端口"
          class="elevation-1"
          @update:page="updatePage"
          @update:items-per-page="updateItemsPerPage"
          @update:sort-by="updateSort"
        >
          <template #item.port="{ item }">
            <v-chip
              :color="getPortColor(item.port)"
              text-color="white"
              size="small"
            >
              {{ item.port }}/{{ item.protocol }}
            </v-chip>
          </template>

          <template #item.service="{ item }">
            <div>
              <strong>{{ item.service }}</strong>
              <br>
              <small class="text-grey">{{ item.version || '版本未知' }}</small>
            </div>
          </template>

          <template #item.risk_level="{ item }">
            <v-chip
              :color="getRiskColor(item.risk_level)"
              text-color="white"
              size="small"
            >
              {{ getRiskText(item.risk_level) }}
            </v-chip>
          </template>

          <template #item.risk_score="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear
                :model-value="item.risk_score"
                :color="getRiskColor(item.risk_level)"
                height="6"
                class="mr-2"
                style="width: 60px;"
              ></v-progress-linear>
              <span>{{ item.risk_score }}</span>
            </div>
          </template>

          <template #item.status="{ item }">
            <v-chip
              :color="item.status === 'open' ? 'green' : 'grey'"
              text-color="white"
              size="small"
            >
              {{ item.status === 'open' ? '开放' : '关闭' }}
            </v-chip>
          </template>

          <template #item.last_scan="{ item }">
            {{ formatTime(item.last_scan) }}
          </template>

          <template #item.actions="{ item }">
            <v-btn
              icon
              size="small"
              @click="showPortDetail(item)"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="blockPort(item)"
              class="ml-1"
            >
              <v-icon>mdi-block-helper</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="scanPort(item)"
              class="ml-1"
            >
              <v-icon>mdi-radar</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 端口详情对话框 -->
    <v-dialog v-model="portDetailDialog" max-width="800">
      <v-card>
        <v-card-title>
          端口详情: {{ selectedPort?.port }}/{{ selectedPort?.protocol }}
        </v-card-title>
        <v-card-text v-if="selectedPort">
          <v-row>
            <v-col cols="6">
              <strong>端口:</strong> {{ selectedPort.port }}
            </v-col>
            <v-col cols="6">
              <strong>协议:</strong> {{ selectedPort.protocol }}
            </v-col>
            <v-col cols="6">
              <strong>服务:</strong> {{ selectedPort.service }}
            </v-col>
            <v-col cols="6">
              <strong>版本:</strong> {{ selectedPort.version || '未知' }}
            </v-col>
            <v-col cols="6">
              <strong>风险等级:</strong> 
              <v-chip :color="getRiskColor(selectedPort.risk_level)" text-color="white" size="small">
                {{ getRiskText(selectedPort.risk_level) }}
              </v-chip>
            </v-col>
            <v-col cols="6">
              <strong>风险评分:</strong> {{ selectedPort.risk_score }}
            </v-col>
            <v-col cols="6">
              <strong>状态:</strong> {{ selectedPort.status === 'open' ? '开放' : '关闭' }}
            </v-col>
            <v-col cols="6">
              <strong>最后扫描:</strong> {{ formatTime(selectedPort.last_scan) }}
            </v-col>
            <v-col cols="12">
              <strong>风险描述:</strong><br>
              {{ selectedPort.description }}
            </v-col>
            <v-col cols="12">
              <strong>安全建议:</strong><br>
              {{ selectedPort.recommendation }}
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn color="error" @click="blockPort(selectedPort!)">
            <v-icon left>mdi-block-helper</v-icon>
            阻断端口
          </v-btn>
          <v-btn color="warning" @click="scanPort(selectedPort!)">
            <v-icon left>mdi-radar</v-icon>
            重新扫描
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="portDetailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import type { PortRisk, PaginationParams } from '@/types/api'

// 响应式数据
const portRiskList = ref<PortRisk[]>([])
const total = ref(0)
const loading = ref(false)
const exportLoading = ref(false)
const portDetailDialog = ref(false)
const selectedPort = ref<PortRisk | null>(null)

const pagination = ref<PaginationParams>({
  page: 1,
  itemsPerPage: 10,
  sortBy: 'risk_score',
  sortDesc: true
})

const filters = reactive({
  riskLevel: '',
  protocol: '',
  portRange: '',
  service: ''
})

// 统计数据
const portStats = computed(() => ({
  totalPorts: portRiskList.value.length,
  openPorts: portRiskList.value.filter(p => p.status === 'open').length,
  riskPorts: portRiskList.value.filter(p => p.risk_level !== 'low').length,
  highRiskPorts: portRiskList.value.filter(p => p.risk_level === 'high').length
}))

// 选项数据
const riskLevelOptions = [
  { title: '低风险', value: 'low' },
  { title: '中风险', value: 'medium' },
  { title: '高风险', value: 'high' }
]

const protocolOptions = [
  { title: 'TCP', value: 'TCP' },
  { title: 'UDP', value: 'UDP' }
]

// 表格列定义
const headers = [
  { title: '端口', key: 'port', sortable: true },
  { title: '服务', key: 'service', sortable: true },
  { title: '风险等级', key: 'risk_level', sortable: true },
  { title: '风险评分', key: 'risk_score', sortable: true },
  { title: '状态', key: 'status', sortable: true },
  { title: '最后扫描', key: 'last_scan', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

// 防抖搜索
let searchTimeout: number | null = null
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    handleSearch()
  }, 500)
}

// 方法
const fetchPortRiskData = async () => {
  try {
    loading.value = true
    // TODO: 调用真实API
    // const response = await networkApi.getPortRiskList()
    portRiskList.value = generateMockPortRiskData()
    total.value = portRiskList.value.length
  } catch (error) {
    console.error('获取端口风险数据失败:', error)
  } finally {
    loading.value = false
  }
}

const generateMockPortRiskData = (): PortRisk[] => {
  const commonPorts = [
    { port: 22, service: 'SSH', protocol: 'TCP', risk: 'medium' },
    { port: 23, service: 'Telnet', protocol: 'TCP', risk: 'high' },
    { port: 80, service: 'HTTP', protocol: 'TCP', risk: 'low' },
    { port: 443, service: 'HTTPS', protocol: 'TCP', risk: 'low' },
    { port: 3389, service: 'RDP', protocol: 'TCP', risk: 'high' },
    { port: 21, service: 'FTP', protocol: 'TCP', risk: 'high' },
    { port: 25, service: 'SMTP', protocol: 'TCP', risk: 'medium' },
    { port: 53, service: 'DNS', protocol: 'UDP', risk: 'medium' },
    { port: 135, service: 'RPC', protocol: 'TCP', risk: 'high' },
    { port: 445, service: 'SMB', protocol: 'TCP', risk: 'high' }
  ]

  return commonPorts.map((p, i) => ({
    port: p.port,
    protocol: p.protocol,
    service: p.service,
    version: `v${Math.floor(Math.random() * 3) + 1}.${Math.floor(Math.random() * 10)}`,
    risk_level: p.risk as 'low' | 'medium' | 'high',
    risk_score: p.risk === 'high' ? 80 + Math.floor(Math.random() * 20) : 
                p.risk === 'medium' ? 40 + Math.floor(Math.random() * 40) :
                Math.floor(Math.random() * 40),
    status: Math.random() > 0.3 ? 'open' : 'closed',
    last_scan: new Date(Date.now() - Math.random() * 86400000).toISOString(),
    description: getPortDescription(p.port, p.service),
    recommendation: getPortRecommendation(p.port, p.service, p.risk as any)
  }))
}

const getPortDescription = (port: number, service: string): string => {
  const descriptions: Record<number, string> = {
    22: 'SSH远程登录服务，可能存在暴力破解风险',
    23: 'Telnet明文传输协议，存在严重安全隐患',
    80: 'HTTP Web服务，可能存在Web应用漏洞',
    443: 'HTTPS安全Web服务，相对安全',
    3389: 'Windows远程桌面，易受攻击',
    21: 'FTP文件传输，明文传输存在风险',
    25: 'SMTP邮件服务，可能被滥用',
    53: 'DNS域名解析服务',
    135: 'Windows RPC服务，存在多种漏洞',
    445: 'SMB文件共享，易受勒索软件攻击'
  }
  return descriptions[port] || `${service}服务端口`
}

const getPortRecommendation = (port: number, service: string, risk: string): string => {
  if (risk === 'high') {
    return '建议立即关闭此端口或加强访问控制，更新到最新版本，配置防火墙规则'
  } else if (risk === 'medium') {
    return '建议加强访问控制，定期更新版本，监控异常访问'
  } else {
    return '保持服务更新，定期安全检查'
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  fetchPortRiskData()
}

const updatePage = (page: number) => {
  pagination.value.page = page
  fetchPortRiskData()
}

const updateItemsPerPage = (itemsPerPage: number) => {
  pagination.value.itemsPerPage = itemsPerPage
  pagination.value.page = 1
  fetchPortRiskData()
}

const updateSort = (sortBy: any) => {
  pagination.value.sortBy = sortBy[0]?.key
  pagination.value.sortDesc = sortBy[0]?.order === 'desc'
  fetchPortRiskData()
}

const refreshData = () => {
  fetchPortRiskData()
}

const exportData = async () => {
  exportLoading.value = true
  try {
    console.log('导出端口风险报告')
  } finally {
    exportLoading.value = false
  }
}

const getPortColor = (port: number) => {
  if ([22, 23, 3389, 21, 135, 445].includes(port)) return 'red'
  if ([25, 53].includes(port)) return 'orange'
  return 'green'
}

const getRiskColor = (level: string) => {
  switch (level) {
    case 'high': return 'red'
    case 'medium': return 'orange'
    case 'low': return 'green'
    default: return 'grey'
  }
}

const getRiskText = (level: string) => {
  switch (level) {
    case 'high': return '高风险'
    case 'medium': return '中风险'
    case 'low': return '低风险'
    default: return '未知'
  }
}

const showPortDetail = (port: PortRisk) => {
  selectedPort.value = port
  portDetailDialog.value = true
}

const blockPort = (port: PortRisk) => {
  console.log('阻断端口:', port.port)
}

const scanPort = (port: PortRisk) => {
  console.log('扫描端口:', port.port)
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchPortRiskData()
})
</script>

<style scoped>
.v-chip {
  cursor: pointer;
}
</style>
