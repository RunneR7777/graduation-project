import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { networkApi } from '@/services'
import type { TrafficRecord, TrafficFilterParams, PaginationParams } from '@/types/api'

export const useTrafficStore = defineStore('traffic', () => {
  // 状态
  const trafficList = ref<TrafficRecord[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  const pagination = ref<PaginationParams>({
    page: 1,
    itemsPerPage: 10, // 保持数据结构兼容，但固定为10
    sortBy: 'timestamp',
    sortDesc: true
  })
  
  const filters = ref<TrafficFilterParams>({
    srcIp: '',
    dstIp: '',
    protocol: '',
    startTime: '',
    endTime: '',
    riskLevel: ''
  })

  // 计算属性
  const totalPages = computed(() => {
    return Math.ceil(total.value / pagination.value.itemsPerPage)
  })

  const hasData = computed(() => {
    return trafficList.value.length > 0
  })

  // 操作
  const fetchTrafficList = async (type: 'all' | 'inbound' | 'outbound' | 'risk' = 'all') => {
    try {
      loading.value = true
      error.value = null
      
      const params = {
        ...pagination.value,
        ...filters.value
      }
      
      let response: any
      switch (type) {
        case 'inbound':
          response = await networkApi.getInboundTraffic(params)
          break
        case 'outbound':
          response = await networkApi.getOutboundTraffic(params)
          break
        case 'risk':
          response = await networkApi.getRiskTraffic(params)
          break
        default:
          response = await networkApi.getTrafficList(params)
      }
      
      if (response.data && response.data.data) {
        trafficList.value = response.data.data.items || []
        total.value = response.data.data.total || 0
      }
    } catch (err: any) {
      error.value = err.message || '获取流量数据失败'
      console.error('获取流量数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  const fetchFlowDetail = async (id: string) => {
    try {
      const response: any = await networkApi.getFlowDetail(id)
      return response.data && response.data.data ? response.data.data : null
    } catch (err: any) {
      error.value = err.message || '获取流量详情失败'
      console.error('获取流量详情失败:', err)
      return null
    }
  }

  const updatePagination = (newPagination: Partial<PaginationParams>) => {
    // 禁止修改 itemsPerPage，固定为10
    const { itemsPerPage, ...allowedParams } = newPagination
    pagination.value = { ...pagination.value, ...allowedParams }
  }

  const updateFilters = (newFilters: Partial<TrafficFilterParams>) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1 // 重置到第一页
  }

  const clearFilters = () => {
    filters.value = {
      srcIp: '',
      dstIp: '',
      protocol: '',
      startTime: '',
      endTime: '',
      riskLevel: ''
    }
    pagination.value.page = 1
  }

  const refreshData = (type: 'all' | 'inbound' | 'outbound' | 'risk' = 'all') => {
    return fetchTrafficList(type)
  }

  return {
    // 状态
    trafficList,
    total,
    loading,
    error,
    pagination,
    filters,
    
    // 计算属性
    totalPages,
    hasData,
    
    // 操作
    fetchTrafficList,
    fetchFlowDetail,
    updatePagination,
    updateFilters,
    clearFilters,
    refreshData
  }
})

