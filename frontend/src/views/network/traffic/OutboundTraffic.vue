<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-upload</v-icon>
      <span class="teal--text">出站流量分析</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">刷新</v-btn>
    </v-card-title>

    <!-- 出站流量统计 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="stat in outboundStats" :key="stat.title">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon :color="stat.color" size="32" class="mr-3">{{ stat.icon }}</v-icon>
              <div>
                <div class="text-h6">{{ stat.value }}</div>
                <div class="text-subtitle2 text-grey">{{ stat.title }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 出站流量趋势 -->
    <v-card class="mb-4">
      <v-card-title>出站流量趋势</v-card-title>
      <v-card-text>
        <TrafficTrendChart :data="trendData" :loading="loading" mode="outbound" height="300px" />
      </v-card-text>
    </v-card>

    <!-- 目标分布 -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>目标国家分布</v-card-title>
          <v-card-text>
            <PieChart title="出站目标国家" :data="targetCountryData" :loading="loading" height="300px" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>目标端口分布</v-card-title>
          <v-card-text>
            <BarChart title="常用目标端口" :data="targetPortData" :loading="loading" height="300px" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 出站流量详情 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="outboundTrafficList"
          :loading="loading"
          :items-length="trafficStore.total"
          :items-per-page="10"
          :page="trafficStore.pagination.page"
          hide-default-footer
          loading-text="加载数据中..."
          no-data-text="暂无数据"
          class="elevation-1"
          @update:sort-by="updateSort"
        >
          <template #item.sourceIP="{ item }">
            <v-chip color="green" text-color="white" size="small">
              {{ item.sourceIP }}
            </v-chip>
          </template>
          <template #item.destIP="{ item }">
            <v-chip color="orange" text-color="white" size="small">
              {{ item.destIP }}
            </v-chip>
          </template>
          <template #item.size="{ item }">
            {{ item.size || 'N/A' }}
          </template>
          <template #item.riskLevel="{ item }">
            <v-chip :color="getRiskColor(item.riskLevel || 'N/A')" size="small">
              {{ item.riskLevel || 'N/A' }}
            </v-chip>
          </template>
        </v-data-table>
        
        <!-- 自定义分页 -->
        <div class="d-flex justify-space-between align-center pa-4">
          <span class="text-caption">
            {{ ((trafficStore.pagination.page - 1) * 10) + 1 }}-{{ Math.min(trafficStore.pagination.page * 10, trafficStore.total) }} of {{ trafficStore.total }}
          </span>
          <v-pagination
            :model-value="trafficStore.pagination.page"
            :length="Math.max(1, Math.ceil(trafficStore.total / 10))"
            color="primary"
            @update:model-value="updatePage"
            :total-visible="7"
          ></v-pagination>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { TrafficRecord, TrafficTrendData } from '@/types/api'
import { useTrafficStore } from '@/stores/traffic'
import { networkApi } from '@/services'
import TrafficTrendChart from '@/components/charts/TrafficTrendChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const trafficStore = useTrafficStore()
const loading = ref(false)
const outboundTrafficList = ref<TrafficRecord[]>([])

const outboundStats = computed(() => [
  { title: '出站流量数', value: outboundTrafficList.value.length, icon: 'mdi-upload', color: 'blue' },
  { title: '外部目标IP', value: new Set(outboundTrafficList.value.map(t => t.destIP)).size, icon: 'mdi-web', color: 'orange' },
  { title: '平均速率', value: getAverageThroughput(), icon: 'mdi-speedometer', color: 'green' },
  { title: '异常连接', value: outboundTrafficList.value.filter(t => t.riskLevel === '高' || t.riskLevel === '中').length, icon: 'mdi-alert', color: 'red' }
])

const trendData = ref<TrafficTrendData[]>([])

const fetchTrendData = async () => {
  try {
    const response: any = await networkApi.getTrafficTrend({ type: 'outbound', hours: 24 })
    if (response.data && response.data.data) {
      trendData.value = response.data.data
    }
  } catch (error) {
    console.error('获取出站流量趋势数据失败:', error)
    trendData.value = []
  }
}

const targetCountryData = ref<any[]>([])

const fetchCountryData = async () => {
  try {
    const response: any = await networkApi.getOutboundCountryDistribution({ pageSize: 100 })
    if (response.data && response.data.data) {
      targetCountryData.value = response.data.data
    }
  } catch (error) {
    console.error('获取目标国家分布数据失败:', error)
    targetCountryData.value = []
  }
}

const targetPortData = computed(() => {
  // TODO: 从现有数据计算端口分布，或者创建端口分布API
  const portCounts: { [key: number]: number } = {}
  
  outboundTrafficList.value.forEach(traffic => {
    const port = traffic.port
    if (port) {
      portCounts[port] = (portCounts[port] || 0) + 1
    }
  })
  
  const portNames: { [key: number]: string } = {
    80: 'HTTP',
    443: 'HTTPS',
    53: 'DNS',
    22: 'SSH',
    25: 'SMTP',
    21: 'FTP',
    23: 'Telnet',
    3306: 'MySQL',
    5432: 'PostgreSQL',
    27017: 'MongoDB',
    3389: 'RDP',
    445: 'SMB',
    8080: 'HTTP-Alt',
    8443: 'HTTPS-Alt'
  }
  
  return Object.entries(portCounts)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5)
    .map(([port, count]) => ({
      name: `${port} (${portNames[Number(port)] || 'Unknown'})`,
      value: count
    }))
})

const headers = [
  { title: '源IP(内部)', key: 'sourceIP' },
  { title: '目标IP(外部)', key: 'destIP' },
  { title: '目标端口', key: 'port' },
  { title: '协议', key: 'protocol' },
  { title: '字节数', key: 'size' },
  { title: '风险等级', key: 'riskLevel' },
  { title: '时间', key: 'timestamp' }
]

const fetchData = async () => {
  loading.value = true
  try {
    await trafficStore.fetchTrafficList('outbound')
    outboundTrafficList.value = trafficStore.trafficList
    await Promise.all([
      fetchTrendData(),
      fetchCountryData()
    ])
  } catch (error) {
    console.error('获取出站流量数据失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshData = () => fetchData()

const updatePage = async (page: number) => {
  // 防止重复调用
  if (page === trafficStore.pagination.page) {
    return
  }
  
  console.log('OutboundTraffic 更新页面到:', page)
  trafficStore.updatePagination({ page })
  await trafficStore.fetchTrafficList('outbound')
  outboundTrafficList.value = trafficStore.trafficList
}

const updateSort = (sortBy: any) => {
  trafficStore.updatePagination({ 
    sortBy: sortBy[0]?.key,
    sortDesc: sortBy[0]?.order === 'desc'
  })
  trafficStore.fetchTrafficList('outbound')
  outboundTrafficList.value = trafficStore.trafficList
}

const getAverageThroughput = () => {
  if (outboundTrafficList.value.length === 0) return '0 Bps'
  
  const totalBytes = outboundTrafficList.value.reduce((sum, item: any) => {
    const bytes = item.size ? parseFloat(item.size.replace(/[^0-9.]/g, '')) : 0
    return sum + bytes
  }, 0)
  
  const avgBytesPerRecord = totalBytes / outboundTrafficList.value.length
  
  if (avgBytesPerRecord < 1024) return `${avgBytesPerRecord.toFixed(0)} Bps`
  if (avgBytesPerRecord < 1024 * 1024) return `${(avgBytesPerRecord / 1024).toFixed(1)} KBps`
  return `${(avgBytesPerRecord / 1024 / 1024).toFixed(1)} MBps`
}

const getRiskColor = (riskLevel: string) => {
  if (riskLevel === '危险') return 'red'
  if (riskLevel === '警告') return 'orange'
  if (riskLevel === '可接受') return 'blue'
  return 'green' // 安全
}

onMounted(() => {
  fetchData()
})
</script>
