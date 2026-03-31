<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-chart-timeline-variant</v-icon>
      <span class="teal--text">所有流量</span>
      <v-spacer></v-spacer>
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
      <v-card-title>流量筛选</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.srcIp"
              label="源IP"
              prepend-icon="mdi-ip-network"
              clearable
              @input="debouncedSearch"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.dstIp"
              label="目标IP"
              prepend-icon="mdi-ip-network"
              clearable
              @input="debouncedSearch"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="2">
            <v-select
              v-model="filters.protocol"
              :items="protocolOptions"
              label="协议"
              clearable
              @update:model-value="handleSearch"
            ></v-select>
          </v-col>
          <v-col cols="12" md="2">
            <v-text-field
              v-model="filters.startTime"
              type="datetime-local"
              label="开始时间"
              @change="handleSearch"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="2">
            <v-text-field
              v-model="filters.endTime"
              type="datetime-local"
              label="结束时间"
              @change="handleSearch"
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

    <!-- 流量趋势图 -->
    <v-card class="mb-4">
      <v-card-title>流量趋势</v-card-title>
      <v-card-text>
        <TrafficTrendChart :data="trendData" :loading="loading" mode="all" height="300px" />
      </v-card-text>
    </v-card>

    <!-- 数据表格 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="trafficList"
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
          <template #item.flow.source="{ item }">
            <v-chip
              color="blue"
              text-color="white"
              size="small"
            >
              {{ item.flow?.source || 'N/A' }}
            </v-chip>
          </template>
          <template #item.flow.destination="{ item }">
            <v-chip
              color="orange"
              text-color="white"
              size="small"
            >
              {{ item.flow?.destination || 'N/A' }}
            </v-chip>
          </template>

          <template #item.type="{ item }">
            <v-chip
              :color="getTypeColor(item.type)"
              text-color="white"
              size="small"
            >
              {{ item.type || 'N/A' }}
            </v-chip>
          </template>

          <template #item.lastSeen="{ item }">
            {{ formatTime(item.lastSeen) }}
          </template>

          <template #item.actions="{ item }">
            <v-btn
              icon
              size="small"
              @click="viewDetail(item)"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="analyzeFlow(item)"
              class="ml-1"
            >
              <v-icon>mdi-chart-line</v-icon>
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

    <!-- IP详情对话框 -->
    <v-dialog v-model="ipDetailDialog" max-width="600">
      <v-card>
        <v-card-title>IP详情: {{ selectedIp }}</v-card-title>
        <v-card-text>
          <p>IP地址详细信息和活动记录...</p>
          <!-- TODO: 实现IP详情内容 -->
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="ipDetailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 流量详情对话框 -->
    <v-dialog v-model="trafficDetailDialog" max-width="800">
      <v-card>
        <v-card-title>流量详情</v-card-title>
        <v-card-text v-if="selectedTraffic">
          <v-row>
            <v-col cols="12">
              <strong>源地址:</strong> {{ selectedTraffic.flow?.source || 'N/A' }}
            </v-col>
            <v-col cols="12">
              <strong>目标地址:</strong> {{ selectedTraffic.flow?.destination || 'N/A' }}
            </v-col>
            <v-col cols="6">
              <strong>协议:</strong> {{ selectedTraffic.protocol }}
            </v-col>
            <v-col cols="6">
              <strong>字节数:</strong> {{ selectedTraffic.totalBytes }}
            </v-col>
            <v-col cols="6">
              <strong>吞吐量:</strong> {{ selectedTraffic.throughput || '无' }}
            </v-col>
            <v-col cols="6">
              <strong>持续时间:</strong> {{ selectedTraffic.duration }}
            </v-col>
            <v-col cols="6">
              <strong>类型:</strong> {{ selectedTraffic.type }}
            </v-col>
            <v-col cols="6">
              <strong>评分:</strong> {{ selectedTraffic.score }}
            </v-col>
            <v-col cols="12">
              <strong>时间:</strong> {{ formatTime(selectedTraffic.lastSeen) }}
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="trafficDetailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useTrafficStore } from '@/stores/traffic'
import { networkApi } from '@/services'
import type { TrafficRecord, TrafficTrendData } from '@/types/api'
import TrafficTrendChart from '@/components/charts/TrafficTrendChart.vue'

const router = useRouter()
const trafficStore = useTrafficStore()

// 响应式数据
const ipDetailDialog = ref(false)
const trafficDetailDialog = ref(false)
const selectedIp = ref('')
const selectedTraffic = ref<TrafficRecord | null>(null)

// 筛选器
const filters = reactive({
  srcIp: '',
  dstIp: '',
  protocol: '',
  startTime: '',
  endTime: '',
})

// 协议选项
const protocolOptions = [
  { title: 'TCP', value: 'TCP' },
  { title: 'UDP', value: 'UDP' },
  { title: 'ICMP', value: 'ICMP' },
  { title: 'HTTP', value: 'HTTP' },
  { title: 'HTTPS', value: 'HTTPS' },
]

// 表格列定义
const headers = [
  { title: '源地址', key: 'flow.source', sortable: true },
  { title: '目标地址', key: 'flow.destination', sortable: true },
  { title: '协议', key: 'protocol', sortable: true },
  { title: '字节数', key: 'totalBytes', sortable: true },
  { title: '吞吐量', key: 'throughput', sortable: true },
  { title: '类型', key: 'type', sortable: true },
  { title: '时间', key: 'lastSeen', sortable: true },
  { title: '操作', key: 'actions', sortable: false },
]

// 计算属性
const trafficList = computed(() => trafficStore.trafficList)
const total = computed(() => trafficStore.total)
const loading = computed(() => trafficStore.loading)
const pagination = computed(() => trafficStore.pagination)


// 趋势数据
const trendData = ref<TrafficTrendData[]>([])

// 获取流量趋势数据
const fetchTrendData = async () => {
  try {
    const response: any = await networkApi.getTrafficTrend({ type: 'all', hours: 24 })
    if (response.data && response.data.data) {
      trendData.value = response.data.data
    }
  } catch (error) {
    console.error('获取流量趋势数据失败:', error)
    // 如果获取失败，使用空数据
    trendData.value = []
  }
}

// 防抖搜索
let searchTimeout: any = null
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    handleSearch()
  }, 500)
}

// 方法
const handleSearch = () => {
  trafficStore.updateFilters(filters)
  trafficStore.fetchTrafficList('all')
}

const clearFilters = () => {
  Object.assign(filters, {
    srcIp: '',
    dstIp: '',
    protocol: '',
    startTime: '',
    endTime: '',
  })
  trafficStore.clearFilters()
  trafficStore.fetchTrafficList('all')
}

const updateScrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const updatePage = async (page: number) => {
  // 防止重复调用
  if (page === trafficStore.pagination.page) {
    return
  }
  
  console.log('更新页面到:', page)
  trafficStore.updatePagination({ page })
  await trafficStore.fetchTrafficList('all')
  updateScrollToTop()
}

const updateSort = (sortBy: any) => {
  trafficStore.updatePagination({ 
    sortBy: sortBy[0]?.key,
    sortDesc: sortBy[0]?.order === 'desc'
  })
  trafficStore.fetchTrafficList('all')
}

const refreshData = () => {
  trafficStore.refreshData('all')
}

const getTypeColor = (type: string | undefined) => {
  if (!type) return 'grey'
  if (type.includes('正常')) return 'green'
  if (type.includes('加密')) return 'blue'
  if (type.includes('风险') || type.includes('危险')) return 'red'
  return 'grey'
}


const viewDetail = (traffic: TrafficRecord) => {
  selectedTraffic.value = traffic
  trafficDetailDialog.value = true
}

const analyzeFlow = (traffic: TrafficRecord) => {
  router.push(`/network/traffic/flow/${traffic.id}`)
}

const formatTime = (timestamp: string | undefined): string => {
  if (!timestamp) return 'N/A'
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 生命周期
onMounted(async () => {
  // 总是重新获取数据，确保格式正确
  await trafficStore.fetchTrafficList('all')
  // 获取流量趋势数据
  await fetchTrendData()
})
</script>

<style scoped>
.v-chip {
  cursor: pointer;
}
</style>
