<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-chart-bar</v-icon>
      <span class="teal--text">IPv6地址统计</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">
        刷新
      </v-btn>
    </v-card-title>

    <!-- 统计概览 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="stat in overallStats" :key="stat.title">
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

    <!-- 前缀统计表格 -->
    <v-card>
      <v-card-title>前缀统计详情</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="statisticsList"
          :loading="loading"
          class="elevation-1"
        >
          <template #item.prefix="{ item }">
            <code>{{ item.prefix }}</code>
          </template>
          <template #item.active_rate="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear
                :model-value="item.active_rate"
                :color="item.active_rate > 80 ? 'green' : item.active_rate > 50 ? 'orange' : 'red'"
                height="6"
                class="mr-2"
                style="width: 60px;"
              ></v-progress-linear>
              <span>{{ item.active_rate.toFixed(1) }}%</span>
            </div>
          </template>
          <template #item.risk_level="{ item }">
            <v-chip :color="getRiskColor(item.risk_level)" text-color="white" size="small">
              {{ getRiskText(item.risk_level) }}
            </v-chip>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { AddressStatistics } from '@/types/api'

const loading = ref(false)
const statisticsList = ref<AddressStatistics[]>([])

const overallStats = computed(() => [
  { title: '总前缀数', value: statisticsList.value.length, icon: 'mdi-ip-network', color: 'blue' },
  { title: '总地址数', value: statisticsList.value.reduce((sum, s) => sum + s.total_addresses, 0), icon: 'mdi-counter', color: 'green' },
  { title: '活跃地址', value: statisticsList.value.reduce((sum, s) => sum + s.active_addresses, 0), icon: 'mdi-check-circle', color: 'teal' },
  { title: '可疑地址', value: statisticsList.value.reduce((sum, s) => sum + s.suspicious_addresses, 0), icon: 'mdi-alert', color: 'orange' }
])

const headers = [
  { title: '前缀', key: 'prefix' },
  { title: '总地址数', key: 'total_addresses' },
  { title: '活跃地址', key: 'active_addresses' },
  { title: '活跃率', key: 'active_rate' },
  { title: '可疑地址', key: 'suspicious_addresses' },
  { title: '风险等级', key: 'risk_level' },
  { title: '最后更新', key: 'last_updated' }
]

const fetchData = async () => {
  loading.value = true
  
  statisticsList.value = [
    { prefix: '2001:db8::/32', total_addresses: 1024, active_addresses: 856, active_rate: 83.6, suspicious_addresses: 12, risk_level: 'low', last_updated: new Date().toISOString() },
    { prefix: '2001:db8:1::/48', total_addresses: 512, active_addresses: 234, active_rate: 45.7, suspicious_addresses: 8, risk_level: 'medium', last_updated: new Date().toISOString() },
    { prefix: '2001:db8:2::/48', total_addresses: 256, active_addresses: 198, active_rate: 77.3, suspicious_addresses: 3, risk_level: 'low', last_updated: new Date().toISOString() }
  ]
  
  loading.value = false
}

const refreshData = () => {
  fetchData()
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

onMounted(() => {
  fetchData()
})
</script>
