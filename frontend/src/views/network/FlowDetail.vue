<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-information</v-icon>
      <span class="teal--text">流量详情 #{{ flowId }}</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">刷新</v-btn>
    </v-card-title>

    <!-- 流量基本信息 -->
    <v-card class="mb-4" v-if="flowDetail">
      <v-card-title>基本信息</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="6">
            <strong>源IP:</strong> 
            <v-chip color="blue" text-color="white" size="small" class="ml-2">
              {{ flowDetail.src_ip }}
            </v-chip>
          </v-col>
          <v-col cols="6">
            <strong>目标IP:</strong>
            <v-chip color="orange" text-color="white" size="small" class="ml-2">
              {{ flowDetail.dst_ip }}
            </v-chip>
          </v-col>
          <v-col cols="6">
            <strong>源端口:</strong> {{ flowDetail.src_port }}
          </v-col>
          <v-col cols="6">
            <strong>目标端口:</strong> {{ flowDetail.dst_port }}
          </v-col>
          <v-col cols="6">
            <strong>协议:</strong> {{ flowDetail.protocol }}
          </v-col>
          <v-col cols="6">
            <strong>风险等级:</strong>
            <v-chip :color="getRiskColor(flowDetail.risk_level)" text-color="white" size="small">
              {{ getRiskText(flowDetail.risk_level) }}
            </v-chip>
          </v-col>
          <v-col cols="6">
            <strong>字节数:</strong> {{ formatBytes(flowDetail.bytes) }}
          </v-col>
          <v-col cols="6">
            <strong>数据包数:</strong> {{ flowDetail.packets }}
          </v-col>
          <v-col cols="6">
            <strong>持续时间:</strong> {{ flowDetail.duration }}秒
          </v-col>
          <v-col cols="6">
            <strong>时间:</strong> {{ formatTime(flowDetail.timestamp) }}
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 流量分析图表 -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>流量时间分布</v-card-title>
          <v-card-text>
            <BarChart title="流量时间分布" :data="timeDistributionData" :loading="loading" height="300px" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>协议分析</v-card-title>
          <v-card-text>
            <PieChart title="协议分布" :data="protocolData" :loading="loading" height="300px" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 相关流量 -->
    <v-card>
      <v-card-title>相关流量记录</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="relatedHeaders"
          :items="relatedFlows"
          :loading="loading"
          class="elevation-1"
        >
          <template #item.src_ip="{ item }">
            <v-chip color="blue" text-color="white" size="small">
              {{ item.src_ip }}
            </v-chip>
          </template>
          <template #item.dst_ip="{ item }">
            <v-chip color="orange" text-color="white" size="small">
              {{ item.dst_ip }}
            </v-chip>
          </template>
          <template #item.bytes="{ item }">
            {{ formatBytes(item.bytes) }}
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import type { TrafficRecord } from '@/types/api'
import { networkApi } from '@/services'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const route = useRoute()
const loading = ref(false)
const flowDetail = ref<TrafficRecord | null>(null)
const relatedFlows = ref<TrafficRecord[]>([])

const flowId = computed(() => route.params.id as string)

const timeDistributionData = computed(() => [
  { name: '0-6时', value: 45 },
  { name: '6-12时', value: 123 },
  { name: '12-18时', value: 234 },
  { name: '18-24时', value: 156 }
])

const protocolData = computed(() => [
  { name: 'TCP', value: 68 },
  { name: 'UDP', value: 25 },
  { name: 'ICMP', value: 7 }
])

const relatedHeaders = [
  { title: '源IP', key: 'src_ip' },
  { title: '目标IP', key: 'dst_ip' },
  { title: '端口', key: 'dst_port' },
  { title: '协议', key: 'protocol' },
  { title: '字节数', key: 'bytes' },
  { title: '时间', key: 'timestamp' }
]

const fetchData = async () => {
  if (!flowId.value) return
  
  loading.value = true
  try {
    const response = await networkApi.getFlowDetail(flowId.value)
    flowDetail.value = response.data
  } catch (error) {
    console.error('获取流量详情失败:', error)
    // 使用模拟数据
    flowDetail.value = {
      id: flowId.value,
      src_ip: '192.168.1.100',
      dst_ip: '8.8.8.8',
      src_port: 54321,
      dst_port: 443,
      protocol: 'TCP',
      bytes: 1048576,
      packets: 1024,
      duration: 120,
      timestamp: new Date().toISOString(),
      risk_level: 'medium'
    }
  } finally {
    loading.value = false
  }
}

const refreshData = () => fetchData()

const getRiskColor = (level: string | undefined) => {
  switch (level) {
    case 'high': return 'red'
    case 'medium': return 'orange'
    case 'low': return 'green'
    default: return 'grey'
  }
}

const getRiskText = (level: string | undefined) => {
  switch (level) {
    case 'high': return '高风险'
    case 'medium': return '中风险'
    case 'low': return '低风险'
    default: return '未知'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'green'
    case 'suspicious': return 'orange'
    case 'inactive': return 'grey'
    default: return 'red'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '活跃'
    case 'suspicious': return '可疑'
    case 'inactive': return '不活跃'
    default: return '未知'
  }
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
  fetchData()
})
</script>
