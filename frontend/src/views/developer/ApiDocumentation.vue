<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-api</v-icon>
      <span class="teal--text">RESTful API 文档</span>
      <v-spacer></v-spacer>
      <v-btn
        color="success"
        @click="testAllAPIs"
        :loading="testingAll"
        prepend-icon="mdi-play"
        class="mr-2"
      >
        测试所有API
      </v-btn>
      <v-btn
        color="primary"
        @click="refreshApiStatus"
        :loading="loading"
        prepend-icon="mdi-refresh"
      >
        刷新状态
      </v-btn>
    </v-card-title>

    <!-- API状态概览 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="blue" size="32" class="mr-3">mdi-api</v-icon>
              <div>
                <div class="text-h6">{{ apiStats.totalEndpoints }}</div>
                <div class="text-subtitle2 text-grey">API总数</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="green" size="32" class="mr-3">mdi-check-circle</v-icon>
              <div>
                <div class="text-h6">{{ apiStats.activeEndpoints }}</div>
                <div class="text-subtitle2 text-grey">活跃API</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="orange" size="32" class="mr-3">mdi-clock</v-icon>
              <div>
                <div class="text-h6">{{ apiStats.avgResponseTime }}ms</div>
                <div class="text-subtitle2 text-grey">平均响应时间</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon color="green" size="32" class="mr-3">mdi-percent</v-icon>
              <div>
                <div class="text-h6">{{ apiStats.successRate }}%</div>
                <div class="text-subtitle2 text-grey">成功率</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 筛选器 -->
    <v-card class="mb-4">
      <v-card-title>API筛选</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.category"
              :items="categoryOptions"
              label="API分类"
              clearable
              @update:model-value="filterAPIs"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.method"
              :items="methodOptions"
              label="请求方法"
              clearable
              @update:model-value="filterAPIs"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.status"
              :items="statusOptions"
              label="状态"
              clearable
              @update:model-value="filterAPIs"
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.search"
              label="搜索API"
              clearable
              @input="debouncedSearch"
              prepend-icon="mdi-magnify"
            ></v-text-field>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- API列表 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="filteredAPIs"
          :loading="loading"
          loading-text="加载API数据中..."
          no-data-text="暂无API数据"
          class="elevation-1"
        >
          <template #item.method="{ item }">
            <v-chip
              :color="getMethodColor(item.method)"
              text-color="white"
              size="small"
            >
              {{ item.method }}
            </v-chip>
          </template>

          <template #item.path="{ item }">
            <code class="api-path">{{ item.path }}</code>
          </template>

          <template #item.status="{ item }">
            <v-chip
              :color="getStatusColor(item.status)"
              text-color="white"
              size="small"
            >
              {{ getStatusText(item.status) }}
            </v-chip>
          </template>

          <template #item.avgResponseTime="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear
                :model-value="Math.min(item.avgResponseTime / 10, 100)"
                :color="item.avgResponseTime > 1000 ? 'red' : item.avgResponseTime > 500 ? 'orange' : 'green'"
                height="6"
                class="mr-2"
                style="width: 60px;"
              ></v-progress-linear>
              <span>{{ item.avgResponseTime }}ms</span>
            </div>
          </template>

          <template #item.successRate="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear
                :model-value="item.successRate"
                :color="item.successRate > 95 ? 'green' : item.successRate > 90 ? 'orange' : 'red'"
                height="6"
                class="mr-2"
                style="width: 60px;"
              ></v-progress-linear>
              <span>{{ item.successRate }}%</span>
            </div>
          </template>

          <template #item.actions="{ item }">
            <v-btn
              icon
              size="small"
              @click="showApiDetail(item)"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="testApi(item)"
              class="ml-1"
              :loading="testingApis.includes(item.id)"
            >
              <v-icon>mdi-play</v-icon>
            </v-btn>
            <v-btn
              icon
              size="small"
              @click="copyApiUrl(item)"
              class="ml-1"
            >
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- API详情对话框 -->
    <v-dialog v-model="apiDetailDialog" max-width="1000">
      <v-card>
        <v-card-title>
          API详情: {{ selectedApi?.method }} {{ selectedApi?.path }}
        </v-card-title>
        <v-card-text v-if="selectedApi">
          <v-tabs v-model="detailTab">
            <v-tab value="info">基本信息</v-tab>
            <v-tab value="params">参数</v-tab>
            <v-tab value="response">响应示例</v-tab>
            <v-tab value="test">接口测试</v-tab>
          </v-tabs>
          
          <v-window v-model="detailTab" class="mt-4">
            <v-window-item value="info">
              <v-row>
                <v-col cols="6">
                  <strong>请求方法:</strong> {{ selectedApi.method }}
                </v-col>
                <v-col cols="6">
                  <strong>API路径:</strong> <code>{{ selectedApi.path }}</code>
                </v-col>
                <v-col cols="6">
                  <strong>分类:</strong> {{ selectedApi.category }}
                </v-col>
                <v-col cols="6">
                  <strong>状态:</strong> 
                  <v-chip :color="getStatusColor(selectedApi.status)" text-color="white" size="small">
                    {{ getStatusText(selectedApi.status) }}
                  </v-chip>
                </v-col>
                <v-col cols="6">
                  <strong>平均响应时间:</strong> {{ selectedApi.avgResponseTime }}ms
                </v-col>
                <v-col cols="6">
                  <strong>成功率:</strong> {{ selectedApi.successRate }}%
                </v-col>
                <v-col cols="12">
                  <strong>描述:</strong><br>
                  {{ selectedApi.description }}
                </v-col>
              </v-row>
            </v-window-item>

            <v-window-item value="params">
              <v-data-table
                :headers="paramHeaders"
                :items="selectedApi.parameters"
                hide-default-footer
                disable-pagination
              >
                <template #item.required="{ item }">
                  <v-chip
                    :color="item.required ? 'red' : 'grey'"
                    text-color="white"
                    size="small"
                  >
                    {{ item.required ? '必需' : '可选' }}
                  </v-chip>
                </template>
              </v-data-table>
            </v-window-item>

            <v-window-item value="response">
              <v-card variant="outlined">
                <v-card-text>
                  <pre><code>{{ selectedApi.responseExample }}</code></pre>
                </v-card-text>
              </v-card>
            </v-window-item>

            <v-window-item value="test">
              <div>
                <h4 class="mb-3">API测试</h4>
                <v-text-field
                  v-model="testUrl"
                  label="测试URL"
                  readonly
                  variant="outlined"
                  class="mb-3"
                ></v-text-field>
                <v-textarea
                  v-model="testParams"
                  label="请求参数 (JSON格式)"
                  variant="outlined"
                  rows="4"
                  class="mb-3"
                ></v-textarea>
                <v-btn
                  color="primary"
                  @click="executeApiTest"
                  :loading="testingApis.includes(selectedApi.id)"
                  block
                >
                  执行测试
                </v-btn>
                
                <!-- 测试结果 -->
                <div v-if="testResult" class="mt-4">
                  <h4>测试结果:</h4>
                  <v-card variant="outlined" class="mt-2">
                    <v-card-text>
                      <pre><code>{{ JSON.stringify(testResult, null, 2) }}</code></pre>
                    </v-card-text>
                  </v-card>
                </div>
              </div>
            </v-window-item>
          </v-window>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="apiDetailDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import type { ApiEndpoint, ApiParameter } from '@/types/api'

// 响应式数据
const apiList = ref<ApiEndpoint[]>([])
const filteredAPIs = ref<ApiEndpoint[]>([])
const loading = ref(false)
const testingAll = ref(false)
const testingApis = ref<string[]>([])
const apiDetailDialog = ref(false)
const selectedApi = ref<ApiEndpoint | null>(null)
const detailTab = ref('info')
const testUrl = ref('')
const testParams = ref('{}')
const testResult = ref<any>(null)

const filters = reactive({
  category: '',
  method: '',
  status: '',
  search: ''
})

// 统计数据
const apiStats = computed(() => ({
  totalEndpoints: apiList.value.length,
  activeEndpoints: apiList.value.filter(api => api.status === 'active').length,
  avgResponseTime: Math.floor(apiList.value.reduce((sum, api) => sum + api.avgResponseTime, 0) / apiList.value.length) || 0,
  successRate: Math.floor(apiList.value.reduce((sum, api) => sum + api.successRate, 0) / apiList.value.length) || 0
}))

// 选项数据
const categoryOptions = [
  { title: '网络分析', value: 'network' },
  { title: '主机管理', value: 'hosts' },
  { title: '地址分析', value: 'address' },
  { title: '风险评估', value: 'risk' },
  { title: '仪表盘', value: 'dashboard' },
  { title: 'ChatAI', value: 'chatai' }
]

const methodOptions = [
  { title: 'GET', value: 'GET' },
  { title: 'POST', value: 'POST' },
  { title: 'PUT', value: 'PUT' },
  { title: 'DELETE', value: 'DELETE' }
]

const statusOptions = [
  { title: '活跃', value: 'active' },
  { title: '已弃用', value: 'deprecated' },
  { title: '不活跃', value: 'inactive' }
]

// 表格列定义
const headers = [
  { title: '方法', key: 'method', sortable: true },
  { title: 'API路径', key: 'path', sortable: true },
  { title: '分类', key: 'category', sortable: true },
  { title: '描述', key: 'description', sortable: false },
  { title: '状态', key: 'status', sortable: true },
  { title: '响应时间', key: 'avgResponseTime', sortable: true },
  { title: '成功率', key: 'successRate', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

const paramHeaders = [
  { title: '参数名', key: 'name' },
  { title: '类型', key: 'type' },
  { title: '必需', key: 'required' },
  { title: '描述', key: 'description' }
]

// 防抖搜索
let searchTimeout: number | null = null
const debouncedSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    filterAPIs()
  }, 500)
}

// 方法
const fetchApiData = async () => {
  try {
    loading.value = true
    // TODO: 调用真实API获取接口列表
    apiList.value = generateMockApiData()
    filteredAPIs.value = apiList.value
  } catch (error) {
    console.error('获取API数据失败:', error)
  } finally {
    loading.value = false
  }
}

const generateMockApiData = (): ApiEndpoint[] => {
  return [
    {
      id: '1',
      path: '/api/network/traffic',
      method: 'GET',
      category: 'network',
      description: '获取网络流量列表',
      status: 'active',
      avgResponseTime: 245,
      successRate: 98.5,
      parameters: [
        { name: 'page', type: 'number', required: false, description: '页码' },
        { name: 'pageSize', type: 'number', required: false, description: '每页数量' },
        { name: 'srcIp', type: 'string', required: false, description: '源IP筛选' }
      ],
      responseExample: `{
  "success": true,
  "data": {
    "items": [...],
    "total": 1234
  }
}`,
      statusCodes: [
        { code: 200, description: '请求成功' },
        { code: 400, description: '参数错误' },
        { code: 500, description: '服务器错误' }
      ]
    },
    {
      id: '2',
      path: '/api/dashboard/stats',
      method: 'GET',
      category: 'dashboard',
      description: '获取仪表盘统计数据',
      status: 'active',
      avgResponseTime: 156,
      successRate: 99.2,
      parameters: [],
      responseExample: `{
  "success": true,
  "data": {
    "total_flows": 1234,
    "active_hosts": 56,
    "risk_alerts": 12
  }
}`,
      statusCodes: [
        { code: 200, description: '请求成功' }
      ]
    },
    {
      id: '3',
      path: '/api/hosts/remote-host',
      method: 'GET',
      category: 'hosts',
      description: '获取远程主机列表',
      status: 'active',
      avgResponseTime: 320,
      successRate: 97.8,
      parameters: [
        { name: 'ipVersion', type: 'string', required: false, description: 'IP版本' },
        { name: 'country', type: 'string', required: false, description: '国家筛选' }
      ],
      responseExample: `{
  "success": true,
  "data": {
    "items": [...],
    "total": 156
  }
}`,
      statusCodes: [
        { code: 200, description: '请求成功' },
        { code: 400, description: '参数错误' }
      ]
    },
    {
      id: '4',
      path: '/api/chatai/mcp/message',
      method: 'POST',
      category: 'chatai',
      description: '发送消息到ChatAI',
      status: 'active',
      avgResponseTime: 1250,
      successRate: 94.5,
      parameters: [
        { name: 'message', type: 'string', required: true, description: '用户消息' },
        { name: 'context', type: 'object', required: false, description: '上下文信息' }
      ],
      responseExample: `{
  "success": true,
  "data": {
    "response": "分析结果...",
    "charts": [...]
  }
}`,
      statusCodes: [
        { code: 200, description: '请求成功' },
        { code: 400, description: '消息格式错误' },
        { code: 500, description: 'AI服务错误' }
      ]
    }
  ]
}

const filterAPIs = () => {
  let filtered = apiList.value

  if (filters.category) {
    filtered = filtered.filter(api => api.category === filters.category)
  }
  
  if (filters.method) {
    filtered = filtered.filter(api => api.method === filters.method)
  }
  
  if (filters.status) {
    filtered = filtered.filter(api => api.status === filters.status)
  }
  
  if (filters.search) {
    const search = filters.search.toLowerCase()
    filtered = filtered.filter(api => 
      api.path.toLowerCase().includes(search) ||
      api.description.toLowerCase().includes(search)
    )
  }

  filteredAPIs.value = filtered
}

const refreshApiStatus = () => {
  fetchApiData()
}

const testAllAPIs = async () => {
  testingAll.value = true
  try {
    for (const api of apiList.value) {
      await testApi(api, false)
    }
  } finally {
    testingAll.value = false
  }
}

const testApi = async (api: ApiEndpoint, showResult = true) => {
  testingApis.value.push(api.id)
  try {
    // TODO: 实现真实API测试
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    if (showResult) {
      testResult.value = {
        status: 200,
        message: 'API测试成功',
        data: { test: 'success' },
        responseTime: Math.floor(Math.random() * 500) + 100
      }
    }
  } catch (error) {
    if (showResult) {
      testResult.value = {
        status: 500,
        message: 'API测试失败',
        error: error
      }
    }
  } finally {
    testingApis.value = testingApis.value.filter(id => id !== api.id)
  }
}

const showApiDetail = (api: ApiEndpoint) => {
  selectedApi.value = api
  testUrl.value = `http://localhost:5001${api.path}`
  testParams.value = '{}'
  testResult.value = null
  apiDetailDialog.value = true
}

const copyApiUrl = (api: ApiEndpoint) => {
  const url = `http://localhost:5001${api.path}`
  navigator.clipboard.writeText(url)
  console.log('API URL已复制:', url)
}

const executeApiTest = () => {
  if (selectedApi.value) {
    testApi(selectedApi.value)
  }
}

const getMethodColor = (method: string) => {
  switch (method) {
    case 'GET': return 'blue'
    case 'POST': return 'green'
    case 'PUT': return 'orange'
    case 'DELETE': return 'red'
    default: return 'grey'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'green'
    case 'deprecated': return 'orange'
    case 'inactive': return 'red'
    default: return 'grey'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '活跃'
    case 'deprecated': return '已弃用'
    case 'inactive': return '不活跃'
    default: return '未知'
  }
}

onMounted(() => {
  fetchApiData()
})
</script>

<style scoped>
.api-path {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

pre {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
