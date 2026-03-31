<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-download</v-icon>
      <span class="teal--text">进站流量分析</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">刷新</v-btn>
    </v-card-title>

    <!-- 进站流量统计 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="stat in inboundStats" :key="stat.title">
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

    <!-- 进站流量趋势 -->
    <v-card class="mb-4">
      <v-card-title>进站流量趋势</v-card-title>
      <v-card-text>
        <TrafficTrendChart :data="trendData" :loading="loading" mode="inbound" height="300px" />
      </v-card-text>
    </v-card>

    <!-- 进站流量详情 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="inboundTrafficList"
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
            <v-chip color="orange" text-color="white" size="small">
              {{ item.sourceIP }}
            </v-chip>
          </template>
          <template #item.destIP="{ item }">
            <v-chip color="green" text-color="white" size="small">
              {{ item.destIP }}
            </v-chip>
          </template>
          <template #item.size="{ item }">
            {{ item.size }}
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

const trafficStore = useTrafficStore()
const loading = ref(false)
const viewMode = ref('chart')
const inboundTrafficList = ref<TrafficRecord[]>([])

const inboundStats = computed(() => [
  { title: '进站流量数', value: inboundTrafficList.value.length, icon: 'mdi-download', color: 'blue' },
  { title: '外部源IP', value: new Set(inboundTrafficList.value.map(t => t.sourceIP)).size, icon: 'mdi-web', color: 'orange' },
  { title: '平均速率', value: getAverageThroughput(), icon: 'mdi-speedometer', color: 'green' },
  { title: '可疑流量', value: inboundTrafficList.value.filter(t => t.riskLevel === '高' || t.riskLevel === '中').length, icon: 'mdi-alert', color: 'red' }
])

const trendData = ref<TrafficTrendData[]>([])

const fetchTrendData = async () => {
  try {
    const response: any = await networkApi.getTrafficTrend({ type: 'inbound', hours: 24 })
    if (response.data && response.data.data) {
      trendData.value = response.data.data
    }
  } catch (error) {
    console.error('获取进站流量趋势数据失败:', error)
    trendData.value = []
  }
}

const headers = [
  { title: '源IP(外部)', key: 'sourceIP' },
  { title: '目标IP(内部)', key: 'destIP' },
  { title: '目标端口', key: 'port' },
  { title: '协议', key: 'protocol' },
  { title: '字节数', key: 'size' },
  { title: '风险等级', key: 'riskLevel' },
  { title: '时间', key: 'timestamp' }
]

const fetchData = async () => {
  loading.value = true
  try {
    await trafficStore.fetchTrafficList('inbound')
    inboundTrafficList.value = trafficStore.trafficList
    await fetchTrendData()
  } catch (error) {
    console.error('获取进站流量数据失败:', error)
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
  
  console.log('InboundTraffic 更新页面到:', page)
  trafficStore.updatePagination({ page })
  await trafficStore.fetchTrafficList('inbound')
  inboundTrafficList.value = trafficStore.trafficList
}

const updateSort = (sortBy: any) => {
  trafficStore.updatePagination({ 
    sortBy: sortBy[0]?.key,
    sortDesc: sortBy[0]?.order === 'desc'
  })
  trafficStore.fetchTrafficList('inbound')
  inboundTrafficList.value = trafficStore.trafficList
}

const getAverageThroughput = () => {
  if (inboundTrafficList.value.length === 0) return '0 Bps'
  
  const totalBytes = inboundTrafficList.value.reduce((sum, item) => {
    const bytes = item.size ? parseFloat(item.size.replace(/[^0-9.]/g, '')) : 0
    return sum + bytes
  }, 0)
  
  const avgBytesPerRecord = totalBytes / inboundTrafficList.value.length
  
  if (avgBytesPerRecord < 1024) return `${avgBytesPerRecord.toFixed(0)} Bps`
  if (avgBytesPerRecord < 1024 * 1024) return `${(avgBytesPerRecord / 1024).toFixed(1)} KBps`
  return `${(avgBytesPerRecord / 1024 / 1024).toFixed(1)} MBps`
}
const loadMapData = () => console.log('加载地图数据')

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
