<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-chart-pie</v-icon>
      <span class="teal--text">AS分布统计</span>
      <v-spacer></v-spacer>
      <v-btn
        color="success"
        @click="exportData"
        :loading="exportLoading"
        prepend-icon="mdi-download"
        class="mr-2"
      >
        导出
      </v-btn>
      <v-btn
        color="primary"
        @click="refreshData"
        :loading="loading"
        prepend-icon="mdi-refresh"
      >
        刷新
      </v-btn>
    </v-card-title>

    <!-- 统计概览 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="blue" size="32" class="mr-3">mdi-chart-pie</v-icon>
              <div>
                <div class="text-h6">{{ asStats.totalAS }}</div>
                <div class="text-subtitle2 text-grey">AS总数</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="green" size="32" class="mr-3">mdi-server-network</v-icon>
              <div>
                <div class="text-h6">{{ asStats.totalHosts }}</div>
                <div class="text-subtitle2 text-grey">关联主机</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="orange" size="32" class="mr-3">mdi-chart-line</v-icon>
              <div>
                <div class="text-h6">{{ formatBytes(asStats.totalTraffic) }}</div>
                <div class="text-subtitle2 text-grey">总流量</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="red" size="32" class="mr-3">mdi-shield-alert</v-icon>
              <div>
                <div class="text-h6">{{ asStats.riskAS }}</div>
                <div class="text-subtitle2 text-grey">风险AS</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 图表展示 -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>AS分布饼图</v-card-title>
          <v-card-text>
            <PieChart
              title="AS分布"
              :data="asChartData"
              :loading="loading"
              height="350px"
              @click="handleChartClick"
            />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>流量分布柱图</v-card-title>
          <v-card-text>
            <BarChart
              title="AS流量分布"
              :data="asTrafficData"
              :loading="loading"
              height="350px"
              @click="handleChartClick"
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- AS详细列表 -->
    <v-card>
      <v-card-title>AS详细信息</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="asDistributionList"
          :loading="loading"
          :items-length="total"
          :items-per-page="pagination.itemsPerPage"
          :page="pagination.page"
          loading-text="加载数据中..."
          no-data-text="暂无数据"
          class="elevation-1"
          @update:page="updatePage"
          @update:items-per-page="updateItemsPerPage"
          @update:sort-by="updateSort"
        >
          <template #item.asNumber="{ item }">
            <v-chip
              color="blue"
              text-color="white"
              size="small"
              @click="showASDetail(item)"
            >
              AS{{ item.asNumber }}
            </v-chip>
          </template>

          <template #item.sentPercentage="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear
                :model-value="item.sentPercentage"
                color="teal"
                height="6"
                class="mr-2"
                style="width: 60px;"
              ></v-progress-linear>
              <span>{{ item.sentPercentage.toFixed(1) }}%</span>
            </div>
          </template>

          <template #item.traffic="{ item }">
            {{ formatBytes(typeof item.traffic === 'string' ? parseInt(item.traffic) || 0 : item.traffic || 0) }}
          </template>

          <template #item.risk_level="{ item }">
            <v-chip
              :color="getRiskColor(item.risk_level)"
              text-color="white"
              size="small"
            >
              {{ getRiskText(item.risk_level) }}
            </v-chip>
          </template>

          <template #item.actions="{ item }">
            <v-btn
              icon
              size="small"
              @click="showASDetail(item)"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="analyzeAS(item)"
              class="ml-1"
            >
              <v-icon>mdi-chart-line</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- AS详情对话框 -->
    <v-dialog v-model="asDetailDialog" max-width="900">
      <v-card>
        <v-card-title>AS详情: AS{{ selectedAS?.asNumber }}</v-card-title>
        <v-card-text v-if="selectedAS">
          <v-row>
            <v-col cols="6">
              <strong>AS号:</strong> {{ selectedAS.asNumber }}
            </v-col>
            <v-col cols="6">
              <strong>AS名称:</strong> {{ selectedAS.name }}
            </v-col>
            <v-col cols="6">
              <strong>主机数量:</strong> {{ selectedAS.hosts }}
            </v-col>
            <v-col cols="6">
              <strong>发送流量百分比:</strong> {{ (selectedAS.percentage || 0).toFixed(2) }}%
            </v-col>
            <v-col cols="6">
              <strong>总流量:</strong> {{ formatBytes(typeof selectedAS.traffic === 'string' ? parseInt(selectedAS.traffic) || 0 : selectedAS.traffic || 0) }}
            </v-col>
            <v-col cols="6">
              <strong>风险等级:</strong>
              <v-chip :color="getRiskColor(selectedAS.risk_level)" text-color="white" size="small">
                {{ getRiskText(selectedAS.risk_level) }}
              </v-chip>
            </v-col>
          </v-row>
          
          <!-- AS相关主机列表 -->
          <v-divider class="my-4"></v-divider>
          <h4 class="mb-2">相关主机 (Top 10)</h4>
          <v-list>
            <v-list-item v-for="(host, index) in selectedAS.relatedHosts" :key="index">
              <template v-slot:prepend>
                <v-avatar color="primary" size="24">
                  {{ index + 1 }}
                </v-avatar>
              </template>
              <v-list-item-title>{{ host.ip }}</v-list-item-title>
              <v-list-item-subtitle>流量: {{ formatBytes(host.traffic) }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-btn color="primary" @click="analyzeAS(selectedAS!)">
            <v-icon left>mdi-chart-line</v-icon>
            深入分析
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="asDetailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { AsDistributionData, PaginationParams } from '@/types/api'
import { networkApi } from '@/services'
import { handlePaginatedResponse, getPaginationInfo } from '@/utils/api'
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const router = useRouter()

// 扩展AS分布数据类型
interface ExtendedAsDistribution extends AsDistributionData {
  percentage?: number
  risk_level: 'low' | 'medium' | 'high'
  relatedHosts: Array<{ ip: string; traffic: number }>
}

// 响应式数据
const asDistributionList = ref<ExtendedAsDistribution[]>([])
const total = ref(0)
const loading = ref(false)
const exportLoading = ref(false)
const asDetailDialog = ref(false)
const selectedAS = ref<ExtendedAsDistribution | null>(null)

const pagination = ref<PaginationParams>({
  page: 1,
  itemsPerPage: 10,
  sortBy: 'hosts',
  sortDesc: true
})

const filters = reactive({
  riskLevel: '',
  minHosts: null as number | null
})

// 统计数据
const asStats = computed(() => ({
  totalAS: asDistributionList.value.length,
  totalHosts: asDistributionList.value.reduce((sum, as) => sum + as.hosts, 0),
  totalTraffic: asDistributionList.value.reduce((sum, as) => sum + (typeof as.traffic === 'string' ? parseInt(as.traffic) || 0 : as.traffic || 0), 0),
  riskAS: asDistributionList.value.filter(as => as.risk_level === 'high').length
}))

// 图表数据
const asChartData = computed(() => {
  // 定义丰富的颜色调色板
  const colorPalette = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
  ]
  
  return asDistributionList.value.slice(0, 10).map((as, index) => ({
    name: `AS${as.asNumber}`,
    value: as.hosts,
    // 使用索引来选择颜色，确保每个AS都有不同的颜色
    color: colorPalette[index % colorPalette.length]
  }))
})

const asTrafficData = computed(() => 
  asDistributionList.value.slice(0, 10).map(as => ({
    name: `AS${as.asNumber}`,
    value: typeof as.traffic === 'string' ? parseInt(as.traffic) || 0 : as.traffic || 0
  }))
)

// 表格列定义
const headers = [
  { title: 'AS号', key: 'asNumber', sortable: true },
  { title: 'AS名称', key: 'name', sortable: true },
  { title: '主机数量', key: 'hosts', sortable: true },
  { title: '发送流量百分比', key: 'sentPercentage', sortable: true },
  { title: '流量', key: 'traffic', sortable: true },
  { title: '风险等级', key: 'risk_level', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

// 方法
const fetchASDistributionData = async () => {
  try {
    loading.value = true
    const response = await networkApi.getAsDistribution()
    console.log('ASDistribution API response:', response)
    
    // 使用统一的API数据处理工具
    const items = handlePaginatedResponse<AsDistributionData>(response)
    asDistributionList.value = enhanceASData(items)
    
    // 获取分页信息
    const paginationInfo = getPaginationInfo(response)
    total.value = paginationInfo.total || asDistributionList.value.length
  } catch (error) {
    console.error('获取AS分布数据失败:', error)
    asDistributionList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const enhanceASData = (data: any): ExtendedAsDistribution[] => {
  if (!Array.isArray(data)) {
    console.warn('enhanceASData: 输入数据不是数组:', data)
    return []
  }
  
  return data.map(as => ({
    ...as,
    // 使用后端返回的真实traffic字段，不再生成假数据
    // traffic字段已由后端API提供
    risk_level: (as.hosts || 0) > 100 ? 'high' : (as.hosts || 0) > 50 ? 'medium' : 'low' as any,
    // relatedHosts需要单独的API来获取，暂时返回空数组
    // TODO: 实现获取关联主机的API endpoint
    relatedHosts: []
  }))
}

const handleSearch = () => {
  fetchASDistributionData()
}

const updatePage = (page: number) => {
  pagination.value.page = page
  fetchASDistributionData()
}

const updateItemsPerPage = (itemsPerPage: number) => {
  pagination.value.itemsPerPage = itemsPerPage
  pagination.value.page = 1
  fetchASDistributionData()
}

const updateSort = (sortBy: any) => {
  pagination.value.sortBy = sortBy[0]?.key
  pagination.value.sortDesc = sortBy[0]?.order === 'desc'
  fetchASDistributionData()
}

const refreshData = () => {
  fetchASDistributionData()
}

const exportData = async () => {
  exportLoading.value = true
  try {
    console.log('导出AS分布数据')
  } finally {
    exportLoading.value = false
  }
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

const handleChartClick = (params: any) => {
  console.log('图表点击:', params)
  // 根据点击的AS跳转到相关主机页面
}

const showASDetail = (as: ExtendedAsDistribution) => {
  selectedAS.value = as
  asDetailDialog.value = true
}

const analyzeAS = (as: ExtendedAsDistribution) => {
  router.push(`/hosts/remote-hosts?asNumber=${as.asNumber}`)
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  fetchASDistributionData()
})
</script>

<style scoped>
.v-chip {
  cursor: pointer;
}
</style>
