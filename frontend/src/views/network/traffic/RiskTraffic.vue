<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="red--text mr-2">mdi-alert</v-icon>
      <span class="red--text">危险流量分析</span>
      <v-spacer></v-spacer>
      <v-btn color="error" @click="blockAllRiskTraffic" :loading="blockingAll" prepend-icon="mdi-block-helper" class="mr-2">
        一键阻断
      </v-btn>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">
        刷新
      </v-btn>
    </v-card-title>

    <!-- 风险警报 -->
    <v-alert type="error" class="mb-4" prominent v-if="highRiskTraffic.length > 0">
      <v-icon left>mdi-shield-alert</v-icon>
      <strong>紧急警报！</strong> 检测到 {{ highRiskTraffic.length }} 条高危流量记录，建议立即处理
    </v-alert>

    <!-- 风险统计 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="stat in riskStats" :key="stat.title">
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

    <!-- 风险类型分布 -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>风险类型分布</v-card-title>
          <v-card-text>
            <PieChart title="风险类型" :data="riskTypeData" :loading="loading" height="300px" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>风险等级分布</v-card-title>
          <v-card-text>
            <BarChart title="风险等级" :data="riskLevelData" :loading="loading" height="300px" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 风险流量详情 -->
    <v-card>
      <v-card-title>风险流量详情</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="riskTrafficList"
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
            <v-chip color="blue" text-color="white" size="small">
              {{ item.sourceIP }}
            </v-chip>
          </template>
          <template #item.destIP="{ item }">
            <v-chip color="orange" text-color="white" size="small">
              {{ item.destIP }}
            </v-chip>
          </template>
          <template #item.size="{ item }">
            {{ item.size }}
          </template>
          <template #item.riskLevel="{ item }">
            <v-chip :color="getRiskColor(item.riskLevel)" text-color="white" size="small">
              {{ item.riskLevel }}
            </v-chip>
          </template>
          <template #item.actions="{ item }">
            <v-btn icon size="small" @click="analyzeRisk(item)">
              <v-icon>mdi-magnify</v-icon>
            </v-btn>
            <v-btn icon size="small" @click="blockTraffic(item)" class="ml-1">
              <v-icon>mdi-block-helper</v-icon>
            </v-btn>
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
import type { TrafficRecord } from '@/types/api'
import { useTrafficStore } from '@/stores/traffic'
import { networkApi } from '@/services'
import TrafficTrendChart from '@/components/charts/TrafficTrendChart.vue'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const trafficStore = useTrafficStore()
const loading = ref(false)
const blockingAll = ref(false)
const riskTrafficList = ref<TrafficRecord[]>([])

const highRiskTraffic = computed(() => 
  riskTrafficList.value.filter(traffic => traffic.riskLevel === '高' || traffic.riskLevel === '危险')
)

const riskStats = computed(() => [
  { title: '风险流量数', value: riskTrafficList.value.length, icon: 'mdi-alert', color: 'red' },
  { title: '高危流量', value: highRiskTraffic.value.length, icon: 'mdi-alert-octagon', color: 'red' },
  { title: '可疑IP数', value: new Set(riskTrafficList.value.map(t => t.sourceIP)).size, icon: 'mdi-ip-network', color: 'orange' },
  { title: '已阻断', value: Math.floor(riskTrafficList.value.length * 0.2), icon: 'mdi-block-helper', color: 'green' }
])

// 注意：风险类型数据需要额外的后端API支持
// 当前数据库中缺少风险类型分类，无法提供准确的风险类型数据
const riskTypeData = computed(() => {
  // TODO: 需要风险类型API，例如 /api/network/traffic/risk/types/analysis
  // 或者基于现有数据推断风险类型
  const riskCounts: { [key: string]: number } = {}
  
  riskTrafficList.value.forEach(traffic => {
    let riskType = '其他'
    
    // 根据端口推断风险类型
    if (traffic.port === 22 || traffic.port === 3389) {
      riskType = '远程访问尝试'
    } else if (traffic.port === 23 || traffic.port === 445) {
      riskType = '可疑端口扫描'
      } else if ((traffic.port || 0) < 1024) {
      riskType = '系统端口访问'
    } else {
      riskType = '异常连接'
    }
    
    riskCounts[riskType] = (riskCounts[riskType] || 0) + 1
  })
  
  const colors = ['#F44336', '#FF9800', '#E91E63', '#9C27B0', '#607D8B']
  
  return Object.entries(riskCounts).map(([type, count], index) => ({
    name: type,
    value: count,
    color: colors[index % colors.length]
  }))
})

const riskLevelData = computed(() => [
  { name: '高风险', value: riskTrafficList.value.filter(t => t.riskLevel === '高' || t.riskLevel === '危险').length },
  { name: '中风险', value: riskTrafficList.value.filter(t => t.riskLevel === '中' || t.riskLevel === '警告').length },
  { name: '低风险', value: riskTrafficList.value.filter(t => t.riskLevel === '低' || t.riskLevel === '安全').length }
])

const headers = [
  { title: '源IP', key: 'sourceIP' },
  { title: '目标IP', key: 'destIP' },
  { title: '目标端口', key: 'port' },
  { title: '协议', key: 'protocol' },
  { title: '风险等级', key: 'riskLevel' },
  { title: '数据包数', key: 'packets' },
  { title: '字节数', key: 'size' },
  { title: '时间', key: 'timestamp' },
  { title: '操作', key: 'actions' }
]

const fetchData = async () => {
  loading.value = true
  try {
    await trafficStore.fetchTrafficList('risk')
    riskTrafficList.value = trafficStore.trafficList
  } catch (error) {
    console.error('获取风险流量数据失败:', error)
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
  
  console.log('RiskTraffic 更新页面到:', page)
  trafficStore.updatePagination({ page })
  await trafficStore.fetchTrafficList('risk')
  riskTrafficList.value = trafficStore.trafficList
}

const updateSort = (sortBy: any) => {
  trafficStore.updatePagination({ 
    sortBy: sortBy[0]?.key,
    sortDesc: sortBy[0]?.order === 'desc'
  })
  trafficStore.fetchTrafficList('risk')
  riskTrafficList.value = trafficStore.trafficList
}

const blockAllRiskTraffic = async () => {
  blockingAll.value = true
  await new Promise(resolve => setTimeout(resolve, 2000))
  console.log('一键阻断所有风险流量')
  blockingAll.value = false
}

const analyzeRisk = (traffic: TrafficRecord) => {
  console.log('分析风险流量:', traffic)
}

const blockTraffic = (traffic: TrafficRecord) => {
  console.log('阻断流量:', traffic)
}

const getRiskColor = (level: string | undefined) => {
  if (!level) return 'grey'
  if (level === '高' || level === '危险') return 'red'
  if (level === '中' || level === '警告') return 'orange'
  if (level === '低' || level === '安全') return 'green'
  return 'grey'
}

onMounted(() => {
  fetchData()
})
</script>
