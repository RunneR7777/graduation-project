import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analyticsApi } from '@/services'
import type { ChartData } from '@/types/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态
  const topHostsChart = ref<ChartData | null>(null)
  const topAppsChart = ref<ChartData | null>(null)
  const trafficClassChart = ref<ChartData | null>(null)
  const topHostsList = ref<any[]>([])
  const topPrefixesChart = ref<ChartData | null>(null)
  
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 操作
  const fetchTopHostsChart = async () => {
    try {
      const response: any = await analyticsApi.getTopHostsChart()
      if (response.data && response.data.data) {
        topHostsChart.value = response.data.data
      }
    } catch (err: any) {
      console.error('获取主机图表数据失败:', err)
    }
  }

  const fetchTopAppsChart = async () => {
    try {
      const response: any = await analyticsApi.getTopAppsChart()
      if (response.data && response.data.data) {
        topAppsChart.value = response.data.data
      }
    } catch (err: any) {
      console.error('获取应用图表数据失败:', err)
    }
  }

  const fetchTrafficClassChart = async () => {
    try {
      const response: any = await analyticsApi.getTrafficClassChart()
      if (response.data && response.data.data) {
        trafficClassChart.value = response.data.data
      }
    } catch (err: any) {
      console.error('获取流量分类图表数据失败:', err)
    }
  }

  const fetchTopHostsList = async () => {
    try {
      const response: any = await analyticsApi.getTopHostsList()
      if (response.data && response.data.data) {
        topHostsList.value = response.data.data
      }
    } catch (err: any) {
      console.error('获取主机列表数据失败:', err)
    }
  }

  const fetchTopPrefixesChart = async () => {
    // 暂时禁用前端调用
    // console.warn('fetchTopPrefixesChart is temporarily disabled')
    return
    /*
    try {
      const response: any = await analyticsApi.getTopPrefixesChart()
      if (response.data && response.data.data) {
        topPrefixesChart.value = response.data.data
      }
    } catch (err: any) {
      console.error('获取前缀图表数据失败:', err)
    }
    */
  }

  const fetchAllData = async () => {
    await Promise.all([
      fetchTopHostsChart(),
      fetchTopAppsChart(),
      fetchTrafficClassChart(),
      fetchTopHostsList()
      // fetchTopPrefixesChart()
    ])
  }

  return {
    // 状态
    topHostsChart,
    topAppsChart,
    trafficClassChart,
    topHostsList,
    topPrefixesChart,
    loading,
    error,
    
    // 操作
    fetchTopHostsChart,
    fetchTopAppsChart,
    fetchTrafficClassChart,
    fetchTopHostsList,
    fetchTopPrefixesChart,
    fetchAllData
  }
})

