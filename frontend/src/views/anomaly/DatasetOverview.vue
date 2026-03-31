<template>
  <div class="dataset-overview">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <v-icon>mdi-chart-box</v-icon>
        数据集概览
      </h1>
      <p class="page-description">
        查看和分析IPv6异常检测数据集的详细信息
      </p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
      <div class="mt-4">正在加载数据集信息...</div>
    </div>

    <!-- 数据集概览内容 -->
    <div v-else-if="datasetInfo" class="overview-content">
      <!-- 基本信息卡片 -->
      <v-card class="info-card" elevation="2">
        <v-card-title class="card-header">
          <v-icon>mdi-information</v-icon>
          <span>数据集基本信息</span>
        </v-card-title>
        <v-card-text>
          <div class="info-grid">
            <div class="info-item">
              <div class="info-label">文件名</div>
              <div class="info-value">{{ datasetInfo.name }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">文件大小</div>
              <div class="info-value">{{ formatFileSize(datasetInfo.size) }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">数据包数量</div>
              <div class="info-value">{{ datasetInfo.packet_count?.toLocaleString() || '0' }}</div>
            </div>
            <div class="info-item">
              <div class="info-label">修改时间</div>
              <div class="info-value">{{ formatDateTime(datasetInfo.modified) }}</div>
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- 数据统计卡片 -->
      <v-card v-if="analysisResult" class="stats-card" elevation="2">
        <v-card-title class="card-header">
          <v-icon>mdi-chart-line</v-icon>
          <span>数据统计</span>
        </v-card-title>
        <v-card-text>
          <div class="stats-grid">
            <v-card class="stat-item" color="primary" variant="flat">
              <v-card-text class="text-center">
                <div class="text-h4">{{ analysisResult.total_packets?.toLocaleString() || '0' }}</div>
                <div class="text-subtitle-1">总数据包数</div>
              </v-card-text>
            </v-card>
            <v-card class="stat-item" color="success" variant="flat">
              <v-card-text class="text-center">
                <div class="text-h4">{{ analysisResult.normal_packets?.toLocaleString() || '0' }}</div>
                <div class="text-subtitle-1">正常数据包</div>
              </v-card-text>
            </v-card>
            <v-card class="stat-item" color="error" variant="flat">
              <v-card-text class="text-center">
                <div class="text-h4">{{ analysisResult.abnormal_packets?.toLocaleString() || '0' }}</div>
                <div class="text-subtitle-1">异常数据包</div>
              </v-card-text>
            </v-card>
            <v-card class="stat-item" color="warning" variant="flat">
              <v-card-text class="text-center">
                <div class="text-h4">{{ analysisResult.anomaly_rate || '0%' }}</div>
                <div class="text-subtitle-1">异常率</div>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>
      </v-card>

      <!-- 异常类型分布 -->
      <v-card v-if="analysisResult?.anomaly_distribution && Object.keys(analysisResult.anomaly_distribution).length > 0" class="distribution-card" elevation="2">
        <v-card-title class="card-header">
          <v-icon>mdi-chart-pie</v-icon>
          <span>异常类型分布</span>
        </v-card-title>
        <v-card-text>
          <div class="distribution-grid">
            <v-card
              v-for="(count, type) in analysisResult.anomaly_distribution"
              :key="type"
              class="distribution-item"
              :color="getAnomalyTypeColor(type)"
              variant="flat"
            >
              <v-card-text class="text-center">
                <div class="text-h5">{{ count }}</div>
                <div class="text-subtitle-2">类型{{ type }}</div>
              </v-card-text>
            </v-card>
          </div>
        </v-card-text>
      </v-card>

      <!-- 数据预览 -->
      <v-card class="preview-card" elevation="2">
        <v-card-title class="card-header">
          <v-icon>mdi-table</v-icon>
          <span>数据预览</span>
        </v-card-title>
        <v-card-text>
          <div v-if="analysisResult?.sample_data && analysisResult.sample_data.length > 0">
            <v-data-table
              :headers="previewHeaders"
              :items="analysisResult.sample_data"
              :items-per-page="10"
              class="preview-table"
              density="compact"
            >
              <template v-slot:item="{ item }: { item: any }">
                <tr>
                  <td v-for="header in previewHeaders" :key="header.key" class="text-caption">
                    <code>{{ item[header.key] }}</code>
                  </td>
                </tr>
              </template>
            </v-data-table>
            <div class="mt-2 text-caption text-grey">
              显示前10条数据记录，共{{ analysisResult.total_packets?.toLocaleString() }}条
            </div>
          </div>
          <div v-else-if="analysisResult?.abnormal_details && analysisResult.abnormal_details.length > 0">
            <v-data-table
              :headers="detailHeaders"
              :items="analysisResult.abnormal_details.slice(0, 10)"
              :items-per-page="5"
              class="preview-table"
            >
              <template v-slot:item.anomaly_type="{ item }: { item: any }">
                <v-chip :color="getAnomalyTagColor(item.anomaly_type)" size="small">
                  类型{{ item.anomaly_type }}
                </v-chip>
              </template>
              <template v-slot:item.source_address="{ item }: { item: any }">
                <code>{{ item.source_address }}</code>
              </template>
              <template v-slot:item.destination_address="{ item }: { item: any }">
                <code>{{ item.destination_address }}</code>
              </template>
            </v-data-table>
          </div>
          <div v-else class="no-preview">
            <v-alert type="info">
              暂无数据预览
            </v-alert>
          </div>
        </v-card-text>
      </v-card>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <v-btn @click="refreshData" :loading="loading" color="primary">
          <v-icon>mdi-refresh</v-icon>
          刷新数据
        </v-btn>
        <v-btn @click="downloadDataset" color="success">
          <v-icon>mdi-download</v-icon>
          下载数据集
        </v-btn>
        <v-btn @click="goToManagement" color="info">
          <v-icon>mdi-cog</v-icon>
          数据集管理
        </v-btn>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-container">
      <v-alert type="error" prominent>
        <v-row align="center">
          <v-col class="grow">
            <div class="text-h6">加载失败</div>
            <div>无法加载数据集信息，请检查网络连接或联系管理员</div>
          </v-col>
          <v-col class="shrink">
            <v-btn @click="refreshData" color="error" variant="outlined">
              重试
            </v-btn>
          </v-col>
        </v-row>
      </v-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import message from '@/utils/message'
import axios from 'axios'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const datasetInfo = ref<any>(null)
const analysisResult = ref<any>(null)

// 表格头部
const previewHeaders = ref<any[]>([])
const detailHeaders = [
  { title: '序号', key: 'index', width: '80px' },
  { title: '异常类型', key: 'anomaly_type', width: '100px' },
  { title: '源地址', key: 'source_address', minWidth: '150px' },
  { title: '目标地址', key: 'destination_address', minWidth: '150px' },
  { title: '流量类别', key: 'traffic_class', width: '100px' },
  { title: '流标签', key: 'flow_label', width: '100px' },
  { title: '负载长度', key: 'payload_length', width: '100px' },
  { title: '下一个头部', key: 'next_header', width: '100px' },
  { title: '跳数限制', key: 'hop_limit', width: '100px' }
]

// 页面挂载时加载数据
onMounted(() => {
  loadDatasetInfo()
})

// 方法
const loadDatasetInfo = async () => {
  loading.value = true
  try {
    // 获取数据集列表
    const response = await axios.get('/api/dataset/analysis')
    if (response.data.status && response.data.status.code === 200) {
      const datasets = response.data.data.datasets || []
      const defaultDataset = datasets.find((d: any) => d.is_default)
      
      if (defaultDataset) {
        datasetInfo.value = defaultDataset
        
        // 分析数据集
        await analyzeDataset(defaultDataset.name)
      } else {
        message.warning('未找到默认数据集')
      }
    } else {
      message.error(response.data.status?.message || '获取数据集列表失败')
    }
  } catch (error: any) {
    console.error('加载数据集信息失败:', error)
    message.error('加载数据集信息失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const analyzeDataset = async (filename: string) => {
  try {
    console.log('开始分析数据集:', filename)
    const response = await axios.post('/api/dataset/analysis', {
      filename: filename
    })
    
    console.log('分析响应:', response.data)
    
    if (response.data.status && response.data.status.code === 200) {
      analysisResult.value = response.data.data
      console.log('设置的分析结果:', analysisResult.value)
      
      // 如果有样本数据，设置预览表格头部
      if (analysisResult.value.sample_data && analysisResult.value.sample_data.length > 0) {
        const sampleItem = analysisResult.value.sample_data[0]
        previewHeaders.value = Object.keys(sampleItem).map(key => ({
          title: key,
          key: key,
          sortable: false,
          width: '120px'
        }))
        console.log('设置的预览表格头部:', previewHeaders.value)
      }
    } else {
      console.error('分析失败:', response.data)
      message.error(response.data.status?.message || '分析数据集失败')
    }
  } catch (error: any) {
    console.error('分析数据集失败:', error)
    message.error('分析数据集失败: ' + (error.response?.data?.message || error.message))
  }
}

const refreshData = () => {
  loadDatasetInfo()
}

const downloadDataset = () => {
  if (datasetInfo.value) {
    window.open(`/api/dataset/${datasetInfo.value.name}`, '_blank')
  }
}

const goToManagement = () => {
  router.push('/anomaly/dataset')
}

const formatFileSize = (bytes: any) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateString: any) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const getAnomalyTypeColor = (type: any) => {
  const colors = [
    'grey', 'orange', 'red', 'green', 'blue', 'purple', 'deep-orange', 'brown'
  ]
  return colors[parseInt(type) % colors.length]
}

const getAnomalyTagColor = (type: any) => {
  const colors = ['grey', 'orange', 'red', 'green', 'blue', 'purple', 'deep-orange', 'brown']
  return colors[parseInt(type) % colors.length]
}
</script>

<style scoped>
.dataset-overview {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.page-description {
  color: #606266;
  font-size: 16px;
  margin: 0;
}

.loading-container,
.error-container {
  text-align: center;
  padding: 60px 20px;
}

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card,
.stats-card,
.distribution-card,
.preview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.info-item {
  text-align: center;
}

.info-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.info-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.distribution-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.distribution-item {
  text-align: center;
}

.preview-table {
  border-radius: 8px;
  overflow: hidden;
}

.no-preview {
  text-align: center;
  padding: 20px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

code {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .distribution-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
  }
}
</style>
