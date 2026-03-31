<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-ip-network</v-icon>
      <span class="teal--text">IPv6活跃地址分析</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">刷新</v-btn>
    </v-card-title>

    <!-- IPv6统计 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="stat in ipv6Stats" :key="stat.title">
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

    <!-- IPv6地址列表 -->
    <v-card>
      <v-card-title>IPv6活跃地址列表</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="ipv6List"
          :loading="loading"
          class="elevation-1"
        >
          <template #item.address="{ item }">
            <code>{{ item.address }}</code>
          </template>
          <template #item.status="{ item }">
            <v-chip :color="getStatusColor(item.status)" text-color="white" size="small">
              {{ getStatusText(item.status) }}
            </v-chip>
          </template>
          <template #item.success_rate="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear :model-value="item.success_rate" color="teal" height="6" class="mr-2" style="width: 60px;"></v-progress-linear>
              <span>{{ item.success_rate }}%</span>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { IPv6Address } from '@/types/api'

const loading = ref(false)
const ipv6List = ref<IPv6Address[]>([])

const ipv6Stats = computed(() => [
  { title: 'IPv6地址总数', value: ipv6List.value.length, icon: 'mdi-ip-network', color: 'blue' },
  { title: '活跃地址', value: ipv6List.value.filter(ip => ip.status === 'active').length, icon: 'mdi-check-circle', color: 'green' },
  { title: '可疑地址', value: ipv6List.value.filter(ip => ip.status === 'suspicious').length, icon: 'mdi-alert', color: 'orange' },
  { title: '不活跃地址', value: ipv6List.value.filter(ip => ip.status === 'inactive').length, icon: 'mdi-close-circle', color: 'grey' }
])

const headers = [
  { title: 'IPv6地址', key: 'address' },
  { title: '状态', key: 'status' },
  { title: '响应时间', key: 'response_time' },
  { title: '检测次数', key: 'detection_count' },
  { title: '成功率', key: 'success_rate' },
  { title: '最后活跃', key: 'last_seen' }
]

const fetchData = async () => {
  loading.value = true
  
  ipv6List.value = [
    { address: '2001:db8::1', status: 'active', response_time: 25, detection_count: 10, success_rate: 95, last_seen: new Date().toISOString() },
    { address: '2001:db8::2', status: 'suspicious', response_time: 156, detection_count: 8, success_rate: 62, last_seen: new Date().toISOString() },
    { address: '2001:db8::3', status: 'inactive', response_time: 0, detection_count: 5, success_rate: 0, last_seen: new Date(Date.now() - 86400000).toISOString() }
  ]
  
  loading.value = false
}

const refreshData = () => fetchData()

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

onMounted(() => {
  fetchData()
})
</script>
