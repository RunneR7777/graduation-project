<template>
  <div class="dataset-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <v-icon>mdi-folder</v-icon>
        数据集管理
      </h1>
      <p class="page-description">
        管理IPv6异常检测数据集，包括默认数据集和用户上传的自定义数据集
      </p>
    </div>

    <!-- 操作工具栏 -->
    <v-card class="toolbar-section" elevation="2">
      <v-card-text>
        <div class="toolbar-content">
          <div class="toolbar-left">
            <h3>数据集列表</h3>
          </div>
          <div class="toolbar-right">
            <input
              type="file"
              ref="uploadInput"
              style="display: none"
              accept=".csv"
              @change="handleUpload"
            />
            <v-btn @click="triggerUpload" :loading="uploading" color="success" class="mr-2">
              <v-icon>mdi-upload</v-icon>
              上传数据集
            </v-btn>
            <v-btn @click="refreshDatasets" :loading="loading" color="primary">
              <v-icon>mdi-refresh</v-icon>
              刷新
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 数据集列表 -->
    <v-card v-if="!loading" class="dataset-list" elevation="2">
      <v-data-table
        :headers="tableHeaders"
        :items="datasets"
        :loading="loading"
        class="elevation-1"
      >
        <template v-slot:item.name="{ item }">
          <div class="file-name">
            <v-icon>mdi-file-document</v-icon>
            <span>{{ item.name }}</span>
            <v-chip v-if="item.is_default" color="primary" size="small">默认</v-chip>
          </div>
        </template>
        
        <template v-slot:item.packet_count="{ item }">
          {{ item.packet_count?.toLocaleString() || '0' }}
        </template>
        
        <template v-slot:item.size="{ item }">
          {{ formatFileSize(item.size) }}
        </template>
        
        <template v-slot:item.modified="{ item }">
          {{ formatDateTime(item.modified) }}
        </template>
        
        <template v-slot:item.actions="{ item }">
          <v-btn size="small" @click="downloadDataset(item)" color="primary">
            <v-icon>mdi-download</v-icon>
            下载
          </v-btn>
          <v-btn 
            v-if="!item.is_default" 
            size="small" 
            @click="deleteDataset(item)"
            color="error"
          >
            <v-icon>mdi-delete</v-icon>
            删除
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- 无数据状态 -->
    <v-empty-state v-if="!loading && datasets.length === 0" 
                   title="暂无数据集"
                   icon="mdi-folder-open">
    </v-empty-state>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import message from '@/utils/message'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const uploading = ref(false)
const datasets = ref<any[]>([])
const uploadInput = ref<HTMLInputElement | null>(null)

// 表格头部
const tableHeaders = [
  { title: '文件名', key: 'name', minWidth: '200px' },
  { title: '数据包数量', key: 'packet_count', width: '120px', align: 'center' as const },
  { title: '文件大小', key: 'size', width: '120px', align: 'center' as const },
  { title: '修改时间', key: 'modified', width: '180px', align: 'center' as const },
  { title: '操作', key: 'actions', width: '300px', align: 'center' as const, sortable: false }
]

// 页面挂载时获取数据集列表
onMounted(() => {
  refreshDatasets()
})

// 方法
const refreshDatasets = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/dataset/analysis')
    if (response.data.status && response.data.status.code === 200) {
      datasets.value = response.data.data.datasets || []
      message.success('数据集列表刷新成功')
    } else {
      message.error(response.data.status?.message || '获取数据集列表失败')
    }
  } catch (error: any) {
    console.error('获取数据集列表失败:', error)
    message.error('获取数据集列表失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const triggerUpload = () => {
  if (uploadInput.value) {
    uploadInput.value.click()
  }
}

const handleUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  
  const file = target.files[0]
  if (!file.name.endsWith('.csv')) {
    message.error('仅支持 CSV 文件')
    // 清空选择，以便下次可以选择同一文件
    target.value = ''
    return
  }
  
  const formData = new FormData()
  formData.append('file', file)
  
  uploading.value = true
  try {
    const response = await axios.post('/api/dataset/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.data.status && response.data.status.code === 200) {
      message.success(response.data.status.message || '数据集上传成功')
      refreshDatasets()
    } else {
      message.error(response.data.status?.message || '数据集上传失败')
    }
  } catch (error: any) {
    console.error('上传数据集失败:', error)
    message.error('上传数据集失败: ' + (error.response?.data?.message || error.message))
  } finally {
    uploading.value = false
    // 清空选择
    target.value = ''
  }
}

const downloadDataset = (dataset: any) => {
  window.open(`/api/dataset/${dataset.name}`, '_blank')
}

const deleteDataset = async (dataset: any) => {
  try {
    const confirmed = confirm(`确定要删除数据集 "${dataset.name}" 吗？此操作不可恢复。`)
    if (!confirmed) return
    
    const response = await axios.delete(`/api/dataset/${dataset.name}`)
    if (response.data.status && response.data.status.code === 200) {
      message.success(response.data.status.message || '数据集删除成功')
      refreshDatasets()
    } else {
      message.error(response.data.status?.message || '删除数据集失败')
    }
  } catch (error: any) {
    console.error('删除数据集失败:', error)
    message.error('删除数据集失败: ' + (error.response?.data?.message || error.message))
  }
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
</script>

<style scoped>
.dataset-management {
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

.toolbar-section {
  margin-bottom: 20px;
}

.toolbar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left h3 {
  margin: 0;
  color: #303133;
}

.dataset-list {
  margin-bottom: 20px;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }
  
  .toolbar-content {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
}
</style>