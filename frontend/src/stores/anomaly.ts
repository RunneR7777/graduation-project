import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAnomalyStore = defineStore('anomaly', () => {
  // 状态
  const loading = ref(false)
  const datasets = ref<any[]>([])
  const detectionResult = ref<any>(null)
  const modelInfo = ref<any>(null)

  // 计算属性
  const hasResults = computed(() => detectionResult.value !== null)
  const anomalyCount = computed(() => detectionResult.value?.abnormal_packets || 0)
  const normalCount = computed(() => detectionResult.value?.normal_packets || 0)
  const totalPackets = computed(() => detectionResult.value?.total_packets || 0)
  const anomalyRate = computed(() => {
    if (totalPackets.value === 0) return '0%'
    const rate = (anomalyCount.value / totalPackets.value) * 100
    return `${rate.toFixed(2)}%`
  })

  // 异常类型分布
  const anomalyDistribution = computed(() => {
    if (!detectionResult.value?.abnormal_details) return []
    
    const distribution: Record<number, number> = {}
    detectionResult.value.abnormal_details.forEach((item: any) => {
      if (!distribution[item.anomaly_type]) {
        distribution[item.anomaly_type] = 0
      }
      distribution[item.anomaly_type]++
    })
    
    const total = Object.values(distribution).reduce((sum, count) => sum + count, 0)
    
    return Object.entries(distribution).map(([type, count]) => ({
      anomaly_type: parseInt(type),
      count,
      percentage: ((count / total) * 100).toFixed(1)
    }))
  })

  // 动作
  const fetchDatasets = async () => {
    loading.value = true
    try {
      const response = await axios.get('/api/dataset/analysis')
      if (response.data.status && response.data.status.code === 200) {
        datasets.value = response.data.data.datasets || []
      }
    } catch (error) {
      console.error('获取数据集列表失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const uploadAndDetect = async (file: File) => {
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await axios.post('/api/anomaly/detection', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      if (response.data.code === 200) {
        detectionResult.value = response.data.data
      }
    } catch (error) {
      console.error('异常检测失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const analyzeDataset = async (filename: string) => {
    loading.value = true
    try {
      const response = await axios.post('/api/dataset/analysis', {
        filename: filename
      })
      
      if (response.data.status && response.data.status.code === 200) {
        return response.data.data
      }
    } catch (error) {
      console.error('数据集分析失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const getModelInfo = async () => {
    try {
      const response = await axios.get('/api/anomaly/detection')
      if (response.data.code === 200) {
        modelInfo.value = response.data.data
      }
    } catch (error) {
      console.error('获取模型信息失败:', error)
      throw error
    }
  }

  const clearResults = () => {
    detectionResult.value = null
  }

  const downloadDataset = (filename: string) => {
    window.open(`/api/dataset/${filename}`, '_blank')
  }

  const deleteDataset = async (filename: string) => {
    try {
      const response = await axios.delete(`/api/dataset/${filename}`)
      if (response.data.code === 200) {
        await fetchDatasets() // 重新获取列表
      }
    } catch (error) {
      console.error('删除数据集失败:', error)
      throw error
    }
  }

  // 工具方法
  const getAnomalyTypeColor = (type: number) => {
    const colors = [
      '#909399', // 灰色
      '#E6A23C', // 橙色
      '#F56C6C', // 红色
      '#67C23A', // 绿色
      '#409EFF', // 蓝色
      '#9C27B0', // 紫色
      '#FF9800', // 深橙色
      '#795548'  // 棕色
    ]
    return colors[type % colors.length]
  }

  const getAnomalyTagType = (type: number) => {
    const types = ['', 'warning', 'danger', 'success', 'primary', 'info', 'warning', 'danger']
    return types[type % types.length] || 'info'
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return {
    // 状态
    loading,
    datasets,
    detectionResult,
    modelInfo,
    
    // 计算属性
    hasResults,
    anomalyCount,
    normalCount,
    totalPackets,
    anomalyRate,
    anomalyDistribution,
    
    // 动作
    fetchDatasets,
    uploadAndDetect,
    analyzeDataset,
    getModelInfo,
    clearResults,
    downloadDataset,
    deleteDataset,
    
    // 工具方法
    getAnomalyTypeColor,
    getAnomalyTagType,
    formatFileSize
  }
})
