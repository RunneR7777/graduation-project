<template>
  <div class="ml-4">
    <v-card-title>
      <v-list-item-action>
        <v-icon class="teal--text">mdi-fingerprint</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="teal--text">
          <span>生成模式分析</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-row class="mr-8 ml-2">
      <!-- 图表组件 -->
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-chart-pie</v-icon>
            地址生成方式分布
          </v-card-title>
          <v-card-text style="height: 350px">
            <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
            <div v-else ref="genMethodChart" style="width: 100%; height: 100%;"></div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-chart-bar</v-icon>
            前缀分布
          </v-card-title>
          <v-card-text style="height: 350px">
            <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
            <div v-else ref="prefixChart" style="width: 100%; height: 100%;"></div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 过滤器 -->
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-text>
            <v-row>
              <v-col cols="12" md="3">
                <v-select
                  v-model="selectedPrefix"
                  :items="prefixOptions"
                  label="前缀"
                  outlined
                  dense
                  @change="filterAddresses"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="selectedGenMethod"
                  :items="genMethodOptions"
                  label="生成方式"
                  outlined
                  dense
                  @change="filterAddresses"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="selectedStatus"
                  :items="statusOptions"
                  label="状态"
                  outlined
                  dense
                  @change="filterAddresses"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3" class="d-flex align-center">
                <v-text-field
                  v-model.number="days"
                  type="number"
                  min="1"
                  label="时间窗口(天)"
                  outlined
                  dense
                  class="mr-2"
                  @change="filterAddresses"
                ></v-text-field>
                <v-btn color="primary" @click="filterAddresses">
                  <v-icon left>mdi-filter</v-icon>
                  筛选
                </v-btn>
                <v-btn class="ml-2" text @click="resetFilters">
                  <v-icon left>mdi-refresh</v-icon>
                  重置
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 地址列表 -->
      <v-col cols="12">
        <v-card>
          <v-card-title>
            IPv6地址生成模式
            <v-spacer></v-spacer>
            <v-text-field
              v-model="search"
              append-icon="mdi-magnify"
              label="搜索"
              single-line
              hide-details
              dense
              outlined
            ></v-text-field>
          </v-card-title>
          
          <v-data-table
            :headers="headers"
            :items="addressesData"
            :search="search"
            :loading="loading"
            :items-per-page="10"
            hide-default-footer
            class="elevation-1"
            :server-items-length="totalItems"
            @update:options="fetchAddressesData"
          >
            <!-- 地址列 -->
            <template v-slot:item.address="{ item }">
              <v-chip
                small
                color="teal"
                text-color="white"
              >
                {{ item.address }}
              </v-chip>
            </template>
            
            <!-- 前缀列 -->
            <template v-slot:item.prefix="{ item }">
              <span>{{ item.prefix }}</span>
            </template>
            
            <!-- 接口标识列 -->
            <template v-slot:item.interfaceId="{ item }">
              <span class="font-weight-medium">{{ item.interfaceId }}</span>
            </template>
            
            <!-- MAC地址列 -->
            <template v-slot:item.macAddress="{ item }">
              <span v-if="item.macAddress">{{ item.macAddress }}</span>
              <span v-else class="grey--text">N/A</span>
            </template>
            
            <!-- 生成方式列 -->
            <template v-slot:item.generationMethod="{ item }">
              <v-chip
                small
                :color="getGenMethodColor(item.generationMethod)"
                text-color="white"
              >
                {{ item.generationMethod }}
              </v-chip>
            </template>
            
            <!-- 状态列 -->
            <template v-slot:item.status="{ item }">
              <v-chip
                small
                :color="getStatusColor(item.status)"
                text-color="white"
              >
                {{ item.status }}
              </v-chip>
            </template>
            
            <!-- 操作列 -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                small
                color="primary"
                text
                @click="viewAddressDetail(item)"
              >
                详情
              </v-btn>
              <v-btn
                small
                color="warning"
                text
                @click="monitorAddress(item)"
              >
                监控
              </v-btn>
            </template>
          </v-data-table>
          
          <!-- 自定义分页 -->
          <div class="d-flex justify-space-between align-center pa-4">
            <span class="text-caption">
              {{ ((currentPage - 1) * 10) + 1 }}-{{ Math.min(currentPage * 10, totalItems) }} of {{ totalItems }}
            </span>
            <v-pagination
              :model-value="currentPage"
              :length="Math.max(1, Math.ceil(totalItems / 10))"
              color="primary"
              @update:model-value="updatePage"
              :total-visible="7"
            ></v-pagination>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { networkApi } from '@/services'
import * as echarts from 'echarts/core'
import { PieChart, BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

// 注册必要的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  PieChart,
  BarChart,
  CanvasRenderer
])

const router = useRouter()

// 响应式数据
const search = ref('')
const loading = ref(false)
const selectedPrefix = ref('all')
const selectedGenMethod = ref('all')
const selectedStatus = ref('all')
const days = ref(365)
const addressesData = ref<any[]>([])
const totalItems = ref(0)
const currentPage = ref(1)
const stats = ref<any>(null)
const prefixTopList = ref<any[]>([])
const genMethodChart = ref<any>(null)
const prefixChart = ref<any>(null)
// ECharts 实例
const genMethodChartInstance = ref<any>(null)
const prefixChartInstance = ref<any>(null)

// 选项数据
const prefixOptions = [
  { text: '全部前缀', value: 'all' },
  { text: '2001:da8:215::', value: '2001:da8:215::' },
  { text: '2001:da8:216::', value: '2001:da8:216::' },
  { text: '2001:da8:217::', value: '2001:da8:217::' }
]

const genMethodOptions = [
  { text: '全部生成方式', value: 'all' },
  { text: 'EUI-64', value: 'EUI-64' },
  { text: '随机生成', value: '随机生成' },
  { text: 'CGA', value: 'CGA' },
  { text: '静态配置', value: '静态配置' },
  { text: '临时地址', value: '临时地址' },
  { text: '低字节', value: '低字节' },
  { text: '嵌入IPv4', value: '嵌入IPv4' },
  { text: 'ISATAP', value: 'ISATAP' }
]

const statusOptions = [
  { text: '全部状态', value: 'all' },
  { text: '活跃', value: '活跃' },
  { text: '非活跃', value: '非活跃' },
  { text: '可疑', value: '可疑' }
]

const headers = [
  { text: 'IPv6地址', value: 'address', width: '250' },
  { text: '前缀', value: 'prefix', width: '150' },
  { text: '接口标识', value: 'interfaceId', width: '150' },
  { text: 'MAC地址', value: 'macAddress', width: '150' },
  { text: '生成方式', value: 'generationMethod', width: '120' },
  { text: '状态', value: 'status', width: '100' },
  { text: '最后活跃时间', value: 'lastActive', width: '150' },
  { text: '操作', value: 'actions', sortable: false }
]

// 方法
const updateScrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const updatePage = async (page: number) => {
  // 防止重复调用
  if (page === currentPage.value) {
    return
  }
  
  console.log('PatternAnalysis 更新页面到:', page)
  currentPage.value = page
  await fetchAddressesData()
  updateScrollToTop()
}

const fetchAddressesData = async () => {
  if (loading.value) return
  
  loading.value = true
  
  const params = {
    page: currentPage.value,
    itemsPerPage: 10,
    prefix: selectedPrefix.value,
    genMethod: selectedGenMethod.value,
    status: selectedStatus.value,
    days: days.value
  }
  
  try {
    const response = await networkApi.getPatternAnalysis(params)
    if (response.data && response.data.data) {
      addressesData.value = response.data.data.items || []
      totalItems.value = response.data.data.total || 0
      stats.value = response.data.data.stats || {}
      prefixTopList.value = response.data.data.topPrefixes || []
    }
  } catch (error) {
    console.error('获取IPv6地址模式分析数据失败:', error)
    addressesData.value = []
    totalItems.value = 0
    stats.value = {}
  } finally {
    loading.value = false
    await nextTick()
    renderGenMethodChart()
    renderPrefixChart()
  }
}

const generateMockAddressData = () => {
  return Array.from({ length: 20 }, (_, i) => ({
    address: `2001:da8:215::${(i + 1).toString(16)}`,
    prefix: '2001:da8:215::',
    interfaceId: `::${(i + 1).toString(16)}`,
    macAddress: i % 3 === 0 ? `00:1b:44:11:3a:${(i + 10).toString(16)}` : null,
    generationMethod: ['EUI-64', '随机生成', 'CGA', '静态配置'][i % 4],
    status: ['活跃', '非活跃', '可疑'][i % 3],
    lastActive: new Date(Date.now() - Math.random() * 86400000).toISOString()
  }))
}

const generateMockStats = () => ({
  iidTypes: {
    'EUI-64': { count: 45 },
    '随机生成': { count: 32 },
    'CGA': { count: 23 },
    '静态配置': { count: 18 },
    '临时地址': { count: 12 },
    '低字节': { count: 8 },
    '嵌入IPv4': { count: 5 },
    'ISATAP': { count: 3 }
  }
})

const renderGenMethodChart = () => {
  if (!stats.value || !stats.value.iidTypes || !genMethodChart.value) return
  
  // 如果已存在实例，先销毁
  if (genMethodChartInstance.value) {
    genMethodChartInstance.value.dispose()
  }
  
  const chart = echarts.init(genMethodChart.value)
  genMethodChartInstance.value = chart
  
  const data = Object.entries(stats.value.iidTypes).map(([name, info]: [string, any]) => ({
    name,
    value: info.count
  }))
  
  const colorMap = {
    'EUI-64': '#009688',
    '随机生成': '#2196F3',
    'CGA': '#673AB7',
    '静态配置': '#FF9800',
    '临时地址': '#4CAF50',
    '低字节': '#F44336',
    '嵌入IPv4': '#3F51B5',
    'ISATAP': '#00BCD4',
    '其他类型': '#9E9E9E'
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      data: data.map(item => item.name)
    },
    series: [
      {
        name: '生成方式',
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: data,
        color: Object.values(colorMap)
      }
    ]
  }
  
  chart.setOption(option)
}

const renderPrefixChart = () => {
  if (!prefixChart.value) return
  
  // 如果已存在实例，先销毁
  if (prefixChartInstance.value) {
    prefixChartInstance.value.dispose()
  }
  
  const chart = echarts.init(prefixChart.value)
  prefixChartInstance.value = chart
  
  let prefixData = []
  if (prefixTopList.value && prefixTopList.value.length > 0) {
    prefixData = prefixTopList.value.map((item: any) => ({
      prefix: item.prefix,
      count: item.count,
      percentage: item.percentage
    }))
  } else {
    if (!addressesData.value || !addressesData.value.length) return
    const prefixCounts: Record<string, number> = {}
    addressesData.value.forEach(item => {
      const prefix = item.prefix
      prefixCounts[prefix] = (prefixCounts[prefix] || 0) + 1
    })
    prefixData = Object.entries(prefixCounts)
      .map(([prefix, count]) => ({ 
        prefix, 
        count,
        percentage: Math.round(count / addressesData.value.length * 100 * 100) / 100
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any) => {
        const item = prefixData[params[0].dataIndex]
        return `${item.prefix}<br/>数量: ${item.count}<br/>占比: ${item.percentage}%`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: prefixData.map(item => {
        let shortPrefix = item.prefix.replace('::', '')
        return shortPrefix.length > 12 ? shortPrefix.substring(0, 12) + '...' : shortPrefix
      }),
      axisLabel: { rotate: 45, interval: 0 }
    },
    yAxis: { type: 'value', name: '地址数量' },
    series: [
      {
        name: '地址数量',
        type: 'bar',
        barWidth: '60%',
        data: prefixData.map(item => item.count),
        itemStyle: { color: '#009688' }
      }
    ]
  }
  
  chart.setOption(option)
}

const filterAddresses = () => {
  currentPage.value = 1
  fetchAddressesData()
}

const resetFilters = () => {
  selectedPrefix.value = 'all'
  selectedGenMethod.value = 'all'
  selectedStatus.value = 'all'
  days.value = 7
  currentPage.value = 1
  fetchAddressesData()
}

const getGenMethodColor = (method: string) => {
  const colorMap = {
    'EUI-64': 'teal',
    '随机生成': 'blue',
    'CGA': 'purple',
    '静态配置': 'orange',
    '临时地址': 'green',
    '低字节': 'red',
    '嵌入IPv4': 'indigo',
    'ISATAP': 'cyan'
  }
  return (colorMap as any)[method] || 'grey'
}

const getStatusColor = (status: string) => {
  const colorMap = {
    '活跃': 'green',
    '非活跃': 'grey',
    '可疑': 'orange'
  }
  return (colorMap as any)[status] || 'grey'
}

const viewAddressDetail = (item: any) => {
  router.push({
    path: '/address/active-detection',
    query: { ipAddress: item.address }
  })
}

const monitorAddress = (item: any) => {
  console.log(`已开始监控地址: ${item.address}`)
}

onMounted(() => {
  fetchAddressesData()
})

onBeforeUnmount(() => {
  // 销毁 ECharts 实例
  if (genMethodChartInstance.value) {
    genMethodChartInstance.value.dispose()
    genMethodChartInstance.value = null
  }
  if (prefixChartInstance.value) {
    prefixChartInstance.value.dispose()
    prefixChartInstance.value = null
  }
})
</script>

<style scoped>
.v-data-table {
  background: white !important;
}
</style>
