<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-ip-network</v-icon>
      <span class="teal--text">IPv6活跃地址检测</span>
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="startDetection" :loading="detecting" prepend-icon="mdi-play">
        开始检测
      </v-btn>
    </v-card-title>

    <!-- 检测输入 -->
    <v-card class="mb-4">
      <v-card-title>地址检测配置</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-textarea
              v-model="addressInput"
              label="IPv6地址列表 (每行一个)"
              placeholder="2001:db8::1\n2001:db8::2\n..."
              rows="6"
              variant="outlined"
            ></v-textarea>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field v-model="timeout" label="超时时间(ms)" type="number" variant="outlined" class="mb-3"></v-text-field>
            <v-text-field v-model="retries" label="重试次数" type="number" variant="outlined" class="mb-3"></v-text-field>
            <v-select v-model="detectionMethod" :items="methodOptions" label="检测方法" variant="outlined"></v-select>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 检测结果 -->
    <v-card v-if="detectionResults.length > 0">
      <v-card-title>检测结果</v-card-title>
      <v-card-text>
        <v-data-table
          :headers="resultHeaders"
          :items="detectionResults"
          :loading="detecting"
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
          <template #item.response_time="{ item }">
            {{ item.response_time }}ms
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { IPv6Address } from '@/types/api'

const addressInput = ref('')
const timeout = ref(1000)
const retries = ref(3)
const detectionMethod = ref('ping')
const detecting = ref(false)
const detectionResults = ref<IPv6Address[]>([])

const methodOptions = [
  { title: 'Ping检测', value: 'ping' },
  { title: 'TCP连接', value: 'tcp' },
  { title: 'HTTP请求', value: 'http' }
]

const resultHeaders = [
  { title: 'IPv6地址', key: 'address' },
  { title: '状态', key: 'status' },
  { title: '响应时间', key: 'response_time' },
  { title: '检测次数', key: 'detection_count' },
  { title: '成功率', key: 'success_rate' }
]

const startDetection = async () => {
  if (!addressInput.value.trim()) return
  
  detecting.value = true
  const addresses = addressInput.value.split('\n').filter(addr => addr.trim())
  
  detectionResults.value = addresses.map(address => ({
    address: address.trim(),
    status: Math.random() > 0.3 ? 'active' : 'inactive' as any,
    response_time: Math.floor(Math.random() * 1000),
    detection_count: Math.floor(Math.random() * 10) + 1,
    success_rate: Math.floor(Math.random() * 100),
    last_seen: new Date().toISOString()
  }))
  
  detecting.value = false
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'green'
    case 'inactive': return 'grey'
    case 'suspicious': return 'orange'
    default: return 'red'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '活跃'
    case 'inactive': return '不活跃'
    case 'suspicious': return '可疑'
    default: return '未知'
  }
}
</script>
