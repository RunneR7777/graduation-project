<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-server</v-icon>
      <span class="teal--text">远端主机分析</span>
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
      <v-card-title>远端主机筛选</v-card-title>
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
              v-model="filters.country"
              :items="countryOptions"
              label="国家"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.asNumber"
              label="AS号"
              type="number"
              clearable
              @input="debouncedSearch"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.riskLevel"
              :items="riskLevelOptions"
              label="风险等级"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
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
              <v-icon color="blue" size="32" class="mr-3">mdi-server-network</v-icon>
              <div>
                <div class="text-h6">{{ remoteStats.totalRemoteHosts }}</div>
                <div class="text-subtitle2 text-grey">远端主机总数</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="green" size="32" class="mr-3">mdi-earth</v-icon>
              <div>
                <div class="text-h6">{{ remoteStats.uniqueCountries }}</div>
                <div class="text-subtitle2 text-grey">涉及国家</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="orange" size="32" class="mr-3">mdi-chart-pie</v-icon>
              <div>
                <div class="text-h6">{{ remoteStats.uniqueAS }}</div>
                <div class="text-subtitle2 text-grey">AS数量</div>
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
                <div class="text-h6">{{ remoteStats.highActivityHosts }}</div>
                <div class="text-subtitle2 text-grey">高风险主机</div>
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
          :items="remoteHostList"
          :loading="loading"
          :items-length="total"
          :items-per-page="pagination.itemsPerPage"
          :page="pagination.page"
          loading-text="加载数据中..."
          no-data-text="暂无数据"
          class="elevation-1"
          @update:page="updatePage"
          @update:items-per-page="updateItemsPerPage"
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

          <template #item.country="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="16" class="mr-2">
                <img :src="getFlagUrl(item.country)" :alt="item.country" />
              </v-avatar>
              {{ item.country }}
            </div>
          </template>

          <template #item.activity="{ item }">
            <v-chip
              :color="getActivityColor(item.activity)"
              size="small"
            >
              {{ item.activity.toFixed(2) }}%
            </v-chip>
          </template>

          <template #item.lastSeen="{ item }">
            {{ item.lastSeen }}
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
              @click="blockHost(item)"
              class="ml-1"
            >
              <v-icon>mdi-block-helper</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 主机详情对话框 -->
    <v-dialog v-model="hostDetailDialog" max-width="800">
      <v-card>
        <v-card-title>远端主机详情: {{ selectedHost?.address }}</v-card-title>
        <v-card-text v-if="selectedHost">
          <v-row>
            <v-col cols="6">
              <strong>IP地址:</strong> {{ selectedHost.address }}
            </v-col>
            <v-col cols="6">
              <strong>主机名:</strong> {{ selectedHost.address || '未知' }}
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
              <strong>活跃度:</strong> {{ selectedHost.activity }}%
            </v-col>
            <v-col cols="6">
              <strong>发送百分比:</strong> {{ selectedHost.sentPercentage }}%
            </v-col>
            <v-col cols="6">
              <strong>前缀:</strong> {{ selectedHost.prefix }}
            </v-col>
            <v-col cols="12">
              <strong>最后活跃:</strong> {{ selectedHost.lastSeen }}
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn color="error" @click="blockHost(selectedHost!)">
            <v-icon left>mdi-block-helper</v-icon>
            阻断主机
          </v-btn>
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
import type { RemoteHost, HostFilterParams, PaginationParams } from '@/types/api'
import { networkApi } from '@/services'

const router = useRouter()

// 响应式数据
const remoteHostList = ref<RemoteHost[]>([])
const total = ref(0)
const loading = ref(false)
const exportLoading = ref(false)
const hostDetailDialog = ref(false)
const selectedHost = ref<RemoteHost | null>(null)

const pagination = ref<PaginationParams>({
  page: 1,
  itemsPerPage: 10,
  sortBy: 'seenSince',
  sortDesc: true
})

const filters = reactive({
  ipVersion: '',
  country: '',
  asNumber: null as number | null,
  riskLevel: ''
})

// 统计数据
const remoteStats = computed(() => {
  const uniqueCountries = new Set(remoteHostList.value.map(h => h.country).filter(Boolean))
  const uniqueAS = new Set(remoteHostList.value.map(h => h.asn).filter(Boolean))
  
  return {
    totalRemoteHosts: remoteHostList.value.length,
    uniqueCountries: uniqueCountries.size,
    uniqueAS: uniqueAS.size,
    highActivityHosts: remoteHostList.value.filter(h => h.activity > 50).length
  }
})

// 选项数据
const ipVersionOptions = [
  { title: 'IPv4', value: 'ipv4' },
  { title: 'IPv6', value: 'ipv6' }
]

const countryOptions = [
  { title: '中国', value: '中国' },
  { title: '美国', value: '美国' },
  { title: '日本', value: '日本' },
  { title: '德国', value: '德国' },
  { title: '英国', value: '英国' },
  { title: '俄罗斯', value: '俄罗斯' },
  { title: '韩国', value: '韩国' }
]

const riskLevelOptions = [
  { title: '低风险', value: 'low' },
  { title: '中风险', value: 'medium' },
  { title: '高风险', value: 'high' }
]

// 表格列定义
const headers = [
  { title: 'IP地址', key: 'address', sortable: true },
  { title: '国家', key: 'country', sortable: true },
  { title: 'AS号', key: 'asn', sortable: true },
  { title: 'AS名称', key: 'asnName', sortable: true },
  { title: '活跃度', key: 'activity', sortable: true },
  { title: '最后活跃', key: 'lastSeen', sortable: true },
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
const fetchRemoteHostData = async () => {
  try {
    loading.value = true
    const params = {
      ...pagination.value,
      ...filters
    }
    const response = await networkApi.getRemoteHosts(params)
    if (response.data && (response.data as any).data) {
      remoteHostList.value = (response.data as any).data.items || []
      total.value = (response.data as any).data.total || 0
    }
  } catch (error) {
    console.error('获取远端主机数据失败:', error)
    remoteHostList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}



const handleSearch = () => {
  pagination.value.page = 1
  fetchRemoteHostData()
}

const clearFilters = () => {
  Object.assign(filters, {
    ipVersion: '',
    country: '',
    asNumber: null,
    riskLevel: ''
  })
  handleSearch()
}

const updatePage = (page: number) => {
  pagination.value.page = page
  fetchRemoteHostData()
}

const updateItemsPerPage = (itemsPerPage: number) => {
  pagination.value.itemsPerPage = itemsPerPage
  pagination.value.page = 1
  fetchRemoteHostData()
}

const updateSort = (sortBy: any) => {
  pagination.value.sortBy = sortBy[0]?.key
  pagination.value.sortDesc = sortBy[0]?.order === 'desc'
  fetchRemoteHostData()
}

const refreshData = () => {
  fetchRemoteHostData()
}

const exportData = async () => {
  exportLoading.value = true
  try {
    console.log('导出远端主机数据')
  } finally {
    exportLoading.value = false
  }
}

const getIpColor = (ip: string) => {
  if (ip.includes(':')) return 'blue' // IPv6
  return 'orange' // 外网IP
}

const getActivityColor = (activity: number) => {
  if (activity >= 50) return 'red'
  if (activity >= 10) return 'orange'
  if (activity > 0) return 'green'
  return 'grey'
}

const getFlagUrl = (country: string) => {
  // 简单的国旗映射，实际项目中可以使用国旗图标库
  const flagMap: Record<string, string> = {
    '中国': 'https://flagcdn.com/16x12/cn.png',
    '美国': 'https://flagcdn.com/16x12/us.png',
    '日本': 'https://flagcdn.com/16x12/jp.png',
    '德国': 'https://flagcdn.com/16x12/de.png',
    '英国': 'https://flagcdn.com/16x12/gb.png',
    '俄罗斯': 'https://flagcdn.com/16x12/ru.png',
    '韩国': 'https://flagcdn.com/16x12/kr.png'
  }
  return flagMap[country] || 'https://flagcdn.com/16x12/xx.png'
}

const showHostDetail = (host: RemoteHost) => {
  selectedHost.value = host
  hostDetailDialog.value = true
}

const analyzeHost = (host: RemoteHost) => {
  router.push(`/network/traffic?srcIp=${host.address}`)
}

const blockHost = (host: RemoteHost) => {
  // TODO: 实现主机阻断功能
  console.log('阻断主机:', host.address)
}


onMounted(() => {
  fetchRemoteHostData()
})
</script>

<style scoped>
.v-chip {
  cursor: pointer;
}
</style>
