<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-earth</v-icon>
      <span class="teal--text">国家分布统计</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">刷新</v-btn>
    </v-card-title>

    <!-- 统计概览 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="stat in countryStats" :key="stat.title">
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

    <!-- 国家分布图表 -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>国家分布饼图</v-card-title>
          <v-card-text>
            <div v-if="countryList.length === 0 && !loading" class="text-center pa-8">
              <v-icon size="64" color="grey-lighten-1">mdi-earth-off</v-icon>
              <p class="text-grey mt-4">暂无国家分布数据</p>
              <p class="text-caption text-grey">请稍后再试或联系管理员</p>
            </div>
            <PieChart v-else title="国家分布" :data="countryChartData" :loading="loading" height="350px" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>主机数量排行</v-card-title>
          <v-card-text>
            <div v-if="countryList.length === 0 && !loading" class="text-center pa-8">
              <v-icon size="64" color="grey-lighten-1">mdi-chart-bar-off</v-icon>
              <p class="text-grey mt-4">暂无主机数量数据</p>
              <p class="text-caption text-grey">请稍后再试或联系管理员</p>
            </div>
            <BarChart v-else title="国家主机数量" :data="countryBarData" :loading="loading" height="350px" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 国家详细列表 -->
    <v-card>
      <v-card-title>国家详细信息</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="countryList"
          :loading="loading"
          :no-data-text="countryList.length === 0 && !loading ? '暂无国家分布数据' : '暂无数据'"
          class="elevation-1"
        >
          <template #item.name="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="20" class="mr-2">
                <img :src="getFlagUrl(item.code)" :alt="item.name" />
              </v-avatar>
              {{ item.name }}
            </div>
          </template>
          <template #item.sentPercentage="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear :model-value="item.sentPercentage" color="teal" height="6" class="mr-2" style="width: 60px;"></v-progress-linear>
              <span>{{ item.sentPercentage.toFixed(1) }}%</span>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { CountryDistributionData } from '@/types/api'
import { networkApi } from '@/services'
import { handlePaginatedResponse } from '@/utils/api'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const loading = ref(false)
const countryList = ref<CountryDistributionData[]>([])

const countryStats = computed(() => {
  const list = Array.isArray(countryList.value) ? countryList.value : []
  return [
    { title: '涉及国家', value: list.length, icon: 'mdi-earth', color: 'blue' },
    { title: '总主机数', value: list.reduce((sum, c) => sum + (c.hosts || 0), 0), icon: 'mdi-server-network', color: 'green' },
    { title: '主要国家', value: list.filter(c => (c.sentPercentage || 0) > 10).length, icon: 'mdi-flag', color: 'orange' },
    { title: '其他国家', value: list.filter(c => (c.sentPercentage || 0) <= 1).length, icon: 'mdi-dots-horizontal', color: 'grey' }
  ]
})

const countryChartData = computed(() => {
  const list = Array.isArray(countryList.value) ? countryList.value : []
  
  // 定义国家分布的颜色调色板
  const countryColorPalette = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
  ]
  
  return list.slice(0, 8).map((country, index) => ({
    name: country.name || 'Unknown',
    value: country.hosts || 0,
    // 使用索引来选择颜色，确保每个国家都有不同的颜色
    color: countryColorPalette[index % countryColorPalette.length]
  }))
})

const countryBarData = computed(() => {
  const list = Array.isArray(countryList.value) ? countryList.value : []
  return list.slice(0, 10).map(country => ({
    name: country.name || 'Unknown',
    value: country.hosts || 0
  }))
})

const headers = [
  { title: '国家', key: 'name' },
  { title: '主机数量', key: 'hosts' },
  { title: '发送流量百分比', key: 'sentPercentage' },
  { title: '吞吐量', key: 'throughput' },

]

const fetchData = async () => {
  try {
    loading.value = true
    const response = await networkApi.getCountryDistribution()
    console.log('CountryDistribution API response:', response)
    
    // 使用统一的API数据处理工具
    const items = handlePaginatedResponse<CountryDistributionData>(response)
    countryList.value = items
    
    // 如果数据为空，显示提示信息
    if (items.length === 0) {
      console.info('国家分布数据为空，可能是后端暂无数据')
    }
  } catch (error) {
    console.error('获取国家分布数据失败:', error)
    countryList.value = []
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData()
}

const getFlagUrl = (countryCode: string) => {
  return `https://flagcdn.com/20x15/${countryCode.toLowerCase()}.png`
}

onMounted(() => {
  fetchData()
})
</script>
