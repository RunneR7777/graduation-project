<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="red--text mr-2">mdi-shield-alert</v-icon>
      <span class="red--text">危险主机分析</span>
      <v-spacer></v-spacer>
      <v-btn color="error" @click="blockAllRiskHosts" :loading="blockingAll" prepend-icon="mdi-block-helper" class="mr-2">
        一键阻断
      </v-btn>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">
        刷新
      </v-btn>
    </v-card-title>

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

    <!-- 风险警报 -->
    <v-alert v-if="highRiskHosts.length > 0" type="error" class="mb-4" prominent>
      <v-icon left>mdi-alert-circle</v-icon>
      <strong>紧急警报！</strong> 发现 {{ highRiskHosts.length }} 个高风险主机，建议立即处理
    </v-alert>

    <!-- 高风险主机列表 -->
    <v-card class="mb-4" v-if="highRiskHosts.length > 0">
      <v-card-title class="red--text">
        <v-icon class="red--text mr-2">mdi-alert-octagon</v-icon>
        高风险主机 (风险评分 ≥ 80)
      </v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item v-for="host in highRiskHosts" :key="host.ipAddress">
            <template v-slot:prepend>
              <v-avatar color="red" size="32">
                <v-icon color="white">mdi-alert</v-icon>
              </v-avatar>
            </template>
            <v-list-item-title>{{ host.ipAddress }}</v-list-item-title>
            <v-list-item-subtitle>
              风险评分: {{ host.riskScore }} | 国家: {{ host.location }}
            </v-list-item-subtitle>
            <template v-slot:append>
              <v-btn color="error" size="small" @click="blockHost(host)">
                <v-icon>mdi-block-helper</v-icon>
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>

    <!-- 所有风险主机列表 -->
    <v-card>
      <v-card-title>所有风险主机</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="riskHostsList"
          :loading="loading"
          class="elevation-1"
        >
          <template #item.ipAddress="{ item }">
            <v-chip :color="getIpColor(item.ipAddress)" text-color="white" size="small">
              {{ item.ipAddress }}
            </v-chip>
          </template>
          <template #item.risk_score="{ item }">
            <v-chip :color="getRiskColor(item.risk_score)" text-color="white" size="small">
              {{ item.risk_score }}
            </v-chip>
          </template>
          <template #item.location="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="16" class="mr-2">
                <img :src="getFlagUrl(getCountryCode(item.location))" :alt="item.location" />
              </v-avatar>
              {{ item.location }}
            </div>
          </template>
          <template #item.actions="{ item }">
            <v-btn icon size="small" @click="showHostDetail(item)">
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn icon size="small" @click="blockHost(item)" class="ml-1">
              <v-icon>mdi-block-helper</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { HostInfo } from '@/types/api'
import { analyticsApi } from '@/services'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const loading = ref(false)
const blockingAll = ref(false)
const riskHostsList = ref<RiskHost[]>([])

const highRiskHosts = computed(() => 
  riskHostsList.value.filter(host => host.riskScore >= 4)
)

const riskStats = computed(() => [
  { title: '总风险主机', value: riskHostsList.value.length, icon: 'mdi-shield-alert', color: 'red' },
  { title: '高风险主机', value: highRiskHosts.value.length, icon: 'mdi-alert-octagon', color: 'red' },
  { title: '中风险主机', value: riskHostsList.value.filter(h => h.riskLevel >= 3 && h.riskLevel < 4).length, icon: 'mdi-alert', color: 'orange' },
  { title: '低风险主机', value: riskHostsList.value.filter(h => h.riskLevel < 3).length, icon: 'mdi-check-circle', color: 'green' }
])

const countryChartData = computed(() => {
  const countryCount: Record<string, number> = {}
  riskHostsList.value.forEach(host => {
    countryCount[host.location] = (countryCount[host.location] || 0) + 1
  })
  return Object.entries(countryCount).map(([country, count]) => ({ name: country, value: count }))
})

const countryBarData = computed(() => countryChartData.value.slice(0, 10))

const headers = [
  { title: 'IP地址', key: 'ipAddress' },
  { title: '风险评分', key: 'riskScore' },
  { title: '风险类型', key: 'riskType' },
  { title: '国家', key: 'location' },
  { title: '流数量', key: 'flows' },
  { title: '发送字节', key: 'sentBytes' },
  { title: '接收字节', key: 'receivedBytes' },
  { title: '最后活跃', key: 'lastSeen' },
  { title: '操作', key: 'actions' }
]

const fetchData = async () => {
  try {
    loading.value = true
    
    // 调用后端真实API
    const response = await analyticsApi.getRiskHosts({
      page: 1,
      itemsPerPage: 100
    })
    
    if (response.data && response.data.data) {
          riskHostsList.value = response.data.data.items || []
    }
  } catch (error) {
    console.error('获取风险主机数据失败:', error)
    // 失败时使用空数组
    riskHostsList.value = []
  } finally {
    loading.value = false
  }
}

// 辅助函数：从location提取国家代码
const getCountryCode = (location: string): string => {
  const countryCodeMap: Record<string, string> = {
    'China': 'CN',
    'United States': 'US',
    'Japan': 'JP',
    'Germany': 'DE',
    'United Kingdom': 'GB',
    'France': 'FR',
    'Russia': 'RU',
    'Korea': 'KR',
    'India': 'IN'
  }
  return countryCodeMap[location] || 'UN'
}

const refreshData = () => fetchData()

const blockAllRiskHosts = async () => {
  blockingAll.value = true
  await new Promise(resolve => setTimeout(resolve, 2000))
  console.log('一键阻断所有风险主机')
  blockingAll.value = false
}

const blockHost = (host: HostInfo) => {
  console.log('阻断主机:', host.address)
}

const showHostDetail = (host: HostInfo) => {
  console.log('查看主机详情:', host.address)
}

const getIpColor = (ip: string) => {
  if (ip.includes(':')) return 'blue'
  return 'orange'
}

const getRiskColor = (score: number) => {
  if (score >= 4) return 'red'
  if (score >= 3) return 'orange'
  return 'green'
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFlagUrl = (countryCode: string) => {
  return `https://flagcdn.com/16x12/${countryCode.toLowerCase()}.png`
}

onMounted(() => {
  fetchData()
})
</script>
