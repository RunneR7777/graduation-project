<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-server-network</v-icon>
      <span class="teal--text">本地主机流量分析</span>
      <v-spacer></v-spacer>
      <v-btn
        color="success"
        @click="exportData"
        :loading="exportLoading"
        prepend-icon="mdi-download"
        class="mr-2"
      >
        导出
      </v-btn>
      <v-btn
        color="primary"
        @click="refreshData"
        :loading="loading"
        prepend-icon="mdi-refresh"
      >
        刷新
      </v-btn>
    </v-card-title>

    <!-- 筛选器 -->
    <v-card class="mb-4">
      <v-card-title>主机筛选</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.ipVersion"
              :items="ipVersionOptions"
              label="IP版本"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.localNetwork"
              :items="localNetworkOptions"
              label="本地网络"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.direction"
              :items="directionOptions"
              label="流量方向"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.hostPools"
              label="主机池"
              clearable
              @input="debouncedSearch"
            ></v-text-field>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="2">
            <v-btn 
              color="primary" 
              block
              @click="handleSearch"
              :loading="loading"
              prepend-icon="mdi-magnify"
            >
              搜索
            </v-btn>
          </v-col>
          <v-col cols="12" md="2">
            <v-btn 
              color="grey" 
              block
              @click="clearFilters"
              prepend-icon="mdi-filter-remove"
            >
              清除
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 统计卡片 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="blue" size="32" class="mr-3">mdi-server</v-icon>
              <div>
                <div class="text-h6">{{ hostStats.totalHosts }}</div>
                <div class="text-subtitle2 text-grey">总主机数</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="green" size="32" class="mr-3">mdi-server-plus</v-icon>
              <div>
                <div class="text-h6">{{ hostStats.activeHosts }}</div>
                <div class="text-subtitle2 text-grey">活跃主机</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="orange" size="32" class="mr-3">mdi-chart-line</v-icon>
              <div>
                <div class="text-h6">{{ formatBytes(hostStats.totalTraffic) }}</div>
                <div class="text-subtitle2 text-grey">总流量</div>
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
                <div class="text-h6">{{ hostStats.riskHosts }}</div>
                <div class="text-subtitle2 text-grey">风险主机</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 数据表格 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="hostList"
          :loading="loading"
          :items-length="total"
          :items-per-page="10"
          :page="pagination.page"
          hide-default-footer
          loading-text="加载数据中..."
          no-data-text="暂无数据"
          class="elevation-1"
          @update:sort-by="updateSort"
        >
          <template #item.address="{ item }">
            <v-chip
              :color="getIpColor(item.address)"
              text-color="white"
              size="small"
              @click="showHostDetail(item)"
            >
              {{ item.address }}
            </v-chip>
          </template>

          <template #item.totalBytes="{ item }">
            {{ item.totalBytes }}
          </template>

          <template #item.throughput="{ item }">
            {{ item.throughput }}
          </template>

          <template #item.riskLevel="{ item }">
            <v-chip
              :color="getRiskLevelColor(item.riskLevel)"
              text-color="white"
              size="small"
            >
              {{ item.riskLevel }}
            </v-chip>
          </template>

          <template #item.seenSince="{ item }">
            {{ item.seenSince }}
          </template>

          <template #item.actions="{ item }">
            <v-btn
              icon
              size="small"
              @click="showHostDetail(item)"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="analyzeHost(item)"
              class="ml-1"
            >
              <v-icon>mdi-chart-line</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="monitorHost(item)"
              class="ml-1"
            >
              <v-icon>mdi-monitor</v-icon>
            </v-btn>
          </template>
        </v-data-table>
        
        <!-- 自定义分页 -->
        <div class="d-flex justify-space-between align-center pa-4">
          <span class="text-caption">
            {{ ((pagination.page - 1) * 10) + 1 }}-{{ Math.min(pagination.page * 10, total) }} of {{ total }}
          </span>
          <v-pagination
            :model-value="pagination.page"
            :length="Math.max(1, Math.ceil(total / 10))"
            color="primary"
            @update:model-value="updatePage"
            :total-visible="7"
          ></v-pagination>
        </div>
      </v-card-text>
    </v-card>

    <!-- 主机详情对话框 -->
    <v-dialog v-model="hostDetailDialog" max-width="800">
      <v-card>
        <v-card-title>主机详情: {{ selectedHost?.address }}</v-card-title>
        <v-card-text v-if="selectedHost">
          <v-row>
            <v-col cols="6">
              <strong>IP地址:</strong> {{ selectedHost.address }}
            </v-col>
            <v-col cols="6">
              <strong>流数量:</strong> {{ selectedHost.flows }}
            </v-col>
            <v-col cols="6">
              <strong>国家:</strong> {{ selectedHost.country || '未知' }}
            </v-col>
            <v-col cols="6">
              <strong>AS号:</strong> {{ selectedHost.asn || '未知' }}
            </v-col>
            <v-col cols="6">
              <strong>AS名称:</strong> {{ selectedHost.asnName || '未知' }}
            </v-col>
            <v-col cols="6">
              <strong>风险等级:</strong> {{ selectedHost.riskLevel }}
            </v-col>
            <v-col cols="6">
              <strong>总流量:</strong> {{ selectedHost.totalBytes }}
            </v-col>
            <v-col cols="6">
              <strong>吞吐量:</strong> {{ selectedHost.throughput }}
            </v-col>
            <v-col cols="12">
              <strong>首次发现:</strong> {{ selectedHost.seenSince }}
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="hostDetailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { HostInfo, HostFilterParams, PaginationParams } from '@/types/api'
import { networkApi } from '@/services'

const router = useRouter()

// 响应式数据
const hostList = ref<HostInfo[]>([])
const total = ref(0)
const loading = ref(false)
const exportLoading = ref(false)
const hostDetailDialog = ref(false)
const selectedHost = ref<HostInfo | null>(null)

const pagination = ref<PaginationParams>({
  page: 1,
  itemsPerPage: 10, // 保持数据结构兼容，但固定为10
  sortBy: 'seenSince',
  sortDesc: true
})

const filters = reactive({
  ipVersion: '',
  localNetwork: '',
  direction: '',
  hostPools: ''
})

// 统计数据
const hostStats = computed(() => ({
  totalHosts: hostList.value.length,
  activeHosts: hostList.value.filter(h => h.riskLevel === '低').length,
  totalTraffic: 0, // totalBytes现在是字符串，无法直接求和
  riskHosts: hostList.value.filter(h => h.riskLevel === '高').length
}))

// 选项数据
const ipVersionOptions = [
  { title: 'IPv4', value: 'ipv4' },
  { title: 'IPv6', value: 'ipv6' }
]

const localNetworkOptions = [
  { title: '192.168.0.0/16', value: '192.168.0.0/16' },
  { title: '10.0.0.0/8', value: '10.0.0.0/8' },
  { title: '172.16.0.0/12', value: '172.16.0.0/12' }
]

const directionOptions = [
  { title: '入站', value: 'inbound' },
  { title: '出站', value: 'outbound' },
  { title: '双向', value: 'bidirectional' }
]

// 表格列定义
const headers = [
  { title: 'IP地址', key: 'address', sortable: true },
  { title: '主机名', key: 'hostname', sortable: true },
  { title: '国家', key: 'country', sortable: true },
  { title: 'AS号', key: 'asn', sortable: true },
  { title: '入站流量', key: 'totalBytes', sortable: true },
  { title: '出站流量', key: 'traffic_out', sortable: true },
  { title: '风险评分', key: 'riskLevel', sortable: true },
  { title: '最后活跃', key: 'seenSince', sortable: true },
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
const fetchHostData = async () => {
  try {
    loading.value = true
    const params = {
      ...pagination.value,
      ...filters
    }
    const response: any = await networkApi.getHostBasedTraffic(params)
    if (response.data && response.data.data) {
      hostList.value = response.data.data.items || []
      total.value = response.data.data.total || 0
    }
  } catch (error) {
    console.error('获取主机数据失败:', error)
    hostList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  fetchHostData()
}

const clearFilters = () => {
  Object.assign(filters, {
    ipVersion: '',
    localNetwork: '',
    direction: '',
    hostPools: ''
  })
  handleSearch()
}

const updateScrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const updatePage = async (page: number) => {
  // 防止重复调用
  if (page === pagination.value.page) {
    return
  }
  
  console.log('HostBasedTraffic 更新页面到:', page)
  pagination.value.page = page
  await fetchHostData()
  updateScrollToTop()
}

const updateSort = (sortBy: any) => {
  pagination.value.sortBy = sortBy[0]?.key
  pagination.value.sortDesc = sortBy[0]?.order === 'desc'
  fetchHostData()
}

const refreshData = () => {
  fetchHostData()
}

const exportData = async () => {
  exportLoading.value = true
  try {
    // TODO: 实现数据导出功能
    console.log('导出主机数据')
  } finally {
    exportLoading.value = false
  }
}

const getIpColor = (ip: string) => {
  if (ip.includes(':')) return 'blue' // IPv6
  if (ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.')) {
    return 'green' // 内网IP
  }
  return 'orange' // 外网IP
}

const getRiskLevelColor = (level: string) => {
  if (level === '高') return 'red'
  if (level === '中') return 'orange'
  return 'green'
}

const showHostDetail = (host: HostInfo) => {
  selectedHost.value = host
  hostDetailDialog.value = true
}

const analyzeHost = (host: HostInfo) => {
  router.push(`/network/traffic?srcIp=${host.address}`)
}

const monitorHost = (host: HostInfo) => {
  // TODO: 实现主机监控功能
  console.log('监控主机:', host.address)
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchHostData()
})
</script>

<style scoped>
.v-chip {
  cursor: pointer;
}
</style>
