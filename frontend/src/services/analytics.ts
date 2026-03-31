import request, { type ApiResponse } from './request'
import type { 
  ChartData, 
  RiskHost, 
  PaginationParams,
  DashboardStats,
  TrafficTrendData,
  PortRisk,
  ApiEndpoint
} from '@/types/api'

// ========== 仪表盘API ==========
export const dashboardApi = {
  // 获取仪表盘统计数据
  getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    return request.get('/dashboard/stats')
  },

  // 获取主机流量分布饼图数据
  getTopHostsChart(): Promise<ApiResponse<ChartData>> {
    return request.get('/dashboard/top-hosts-chart')
  },

  // 获取应用协议分布饼图数据  
  getTopAppsChart(): Promise<ApiResponse<ChartData>> {
    return request.get('/dashboard/top-apps-chart')
  },

  // 获取流量安全分类饼图数据
  getTrafficClassChart(): Promise<ApiResponse<ChartData>> {
    return request.get('/dashboard/traffic-class-chart')
  },

  // 获取主机详细列表数据
  getTopHostsList(): Promise<ApiResponse<any[]>> {
    return request.get('/dashboard/top-hosts-list')
  },

  // 获取前缀分布数据
  getTopPrefixesChart(): Promise<ApiResponse<ChartData>> {
    return request.get('/dashboard/top-prefixes-chart')
  },

  // 获取流量趋势数据
  getTrafficTrend(params?: { startTime?: string; endTime?: string }): Promise<ApiResponse<TrafficTrendData[]>> {
    return request.get('/dashboard/traffic-trend', { params })
  }
}

// ========== 风险评估API ==========
export const riskApi = {
  // 获取风险主机列表
  getRiskHosts(params: PaginationParams & any): Promise<ApiResponse<{
    items: RiskHost[]
    total: number
  }>> {
    return request.get('/risk-hosts', { params })
  },

  // 获取端口风险评估
  getPortRisks(params: PaginationParams): Promise<ApiResponse<{
    items: PortRisk[]
    total: number
  }>> {
    return request.get('/risk/ports', { params })
  },

  // 获取API端点风险评估
  getApiEndpoints(params: PaginationParams): Promise<ApiResponse<{
    items: ApiEndpoint[]
    total: number
  }>> {
    return request.get('/risk/api-endpoints', { params })
  }
}

// ========== 统一导出 ==========
export const analyticsServices = {
  ...dashboardApi,
  ...riskApi
}

export default analyticsServices

