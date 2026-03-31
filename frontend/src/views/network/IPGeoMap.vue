<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-earth</v-icon>
      <span class="teal--text">IP地理位置分布图</span>
      <v-spacer></v-spacer>
      <v-btn-toggle v-model="viewMode" mandatory class="mr-4">
        <v-btn value="map" size="small">
          <v-icon>mdi-map</v-icon>
          地图视图
        </v-btn>
        <v-btn value="chart" size="small">
          <v-icon>mdi-chart-bar</v-icon>
          图表视图
        </v-btn>
      </v-btn-toggle>
      <v-btn color="primary" @click="refreshData" :loading="loading" prepend-icon="mdi-refresh">
        刷新
      </v-btn>
    </v-card-title>

    <!-- 统计概览 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="stat in geoStats" :key="stat.title">
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

    <!-- 地图视图 -->
    <v-card v-if="viewMode === 'map'">
      <v-card-title>全球IP地理分布地图</v-card-title>
      <v-card-text>
        <div style="height: 500px;" class="d-flex align-center justify-center">
          <div class="text-center">
            <v-icon size="64" color="teal">mdi-map-marker</v-icon>
            <p class="mt-4">互动地图组件</p>
            <p class="text-grey">将集成地图组件显示IP地理位置分布</p>
            <v-btn color="teal" class="mt-4" @click="loadMapData">
              加载地图数据
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 图表视图 -->
    <v-row v-if="viewMode === 'chart'">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>国家分布</v-card-title>
          <v-card-text>
            <PieChart title="IP国家分布" :data="countryData" :loading="loading" height="350px" />
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>洲际分布</v-card-title>
          <v-card-text>
            <BarChart title="洲际IP数量" :data="continentData" :loading="loading" height="350px" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 地理位置详情 -->
    <v-card class="mt-4">
      <v-card-title>IP地理位置详情</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="geoHeaders"
          :items="geoLocationList"
          :loading="loading"
          class="elevation-1"
        >
          <template #item.country="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="16" class="mr-2">
                <img :src="getFlagUrl(item.country_code)" :alt="item.country" />
              </v-avatar>
              {{ item.country }}
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
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const loading = ref(false)
const viewMode = ref('map')
const geoLocationList = ref<any[]>([])

const geoStats = computed(() => [
  { title: 'IP总数', value: 1234, icon: 'mdi-ip-network', color: 'blue' },
  { title: '涉及国家', value: 28, icon: 'mdi-earth', color: 'green' },
  { title: '风险地区', value: 5, icon: 'mdi-alert-circle', color: 'red' },
  { title: '新增位置', value: 12, icon: 'mdi-plus-circle', color: 'orange' }
])

const countryData = computed(() => [
  { name: '中国', value: 456 },
  { name: '美国', value: 234 },
  { name: '日本', value: 123 },
  { name: '德国', value: 89 },
  { name: '英国', value: 67 }
])

const continentData = computed(() => [
  { name: '亚洲', value: 678 },
  { name: '北美洲', value: 345 },
  { name: '欧洲', value: 234 },
  { name: '南美洲', value: 56 },
  { name: '大洋洲', value: 23 }
])

const geoHeaders = [
  { title: 'IP地址', key: 'ip' },
  { title: '国家', key: 'country' },
  { title: '城市', key: 'city' },
  { title: '纬度', key: 'latitude' },
  { title: '经度', key: 'longitude' },
  { title: '风险等级', key: 'risk_level' }
]

const loadMapData = () => {
  console.log('加载地图数据')
}

const fetchData = async () => {
  loading.value = true
  
  geoLocationList.value = [
    { ip: '8.8.8.8', country: '美国', country_code: 'US', city: '山景城', latitude: 37.4056, longitude: -122.0775, risk_level: 'low' },
    { ip: '1.1.1.1', country: '美国', country_code: 'US', city: '旧金山', latitude: 37.7749, longitude: -122.4194, risk_level: 'low' },
    { ip: '114.114.114.114', country: '中国', country_code: 'CN', city: '北京', latitude: 39.9042, longitude: 116.4074, risk_level: 'medium' }
  ]
  
  loading.value = false
}

const refreshData = () => fetchData()

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

const getFlagUrl = (countryCode: string) => {
  return `https://flagcdn.com/16x12/${countryCode.toLowerCase()}.png`
}

onMounted(() => {
  fetchData()
})
</script>
