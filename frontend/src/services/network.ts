import request from './request'
import type { 
  TrafficRecord, 
  TrafficFilterParams, 
  PaginationParams,
  HostInfo,
  HostFilterParams,
  AsDistributionData,
  CountryDistributionData,
  RemoteHost,
  PaginatedResponse,
  SimpleResponse
} from '@/types/api'

// ========== 网络流量相关API ==========
export const networkApi = {
  // 获取网络流量列表
  getTrafficList(params: PaginationParams & TrafficFilterParams): Promise<PaginatedResponse<TrafficRecord>> {
    return request.get('/network/traffic', { params })
  },

  // 获取流量详情
  getFlowDetail(id: string): Promise<SimpleResponse<TrafficRecord>> {
    return request.get(`/network/traffic/flow/${id}`)
  },

  // 获取进站流量
  getInboundTraffic(params: PaginationParams & TrafficFilterParams): Promise<PaginatedResponse<TrafficRecord>> {
    return request.get('/network/traffic/inbound', { params })
  },

  // 获取出站流量
  getOutboundTraffic(params: PaginationParams & TrafficFilterParams): Promise<PaginatedResponse<TrafficRecord>> {
    return request.get('/network/traffic/outbound', { params })
  },

  // 获取危险流量
  getDangerousTraffic(params: PaginationParams & TrafficFilterParams): Promise<PaginatedResponse<TrafficRecord>> {
    return request.get('/network/traffic/dangerous', { params })
  },

  // 获取风险流量
  getRiskTraffic(params: PaginationParams & TrafficFilterParams): Promise<PaginatedResponse<TrafficRecord>> {
    return request.get('/network/traffic/risk', { params })
  },

  // 获取流量趋势数据
  getTrafficTrend(params: { startTime?: string; endTime?: string }): Promise<SimpleResponse<any[]>> {
    return request.get('/network/traffic/trend', { params })
  },

  // 获取出站目标国家分布
  getOutboundCountryDistribution(params?: { pageSize?: number }): Promise<SimpleResponse<CountryDistributionData[]>> {
    return request.get('/network/traffic/outbound/country-distribution', { params })
  }
}

// ========== 主机相关API ==========
export const hostsApi = {
  // AS分布分析
  getAsDistribution(): Promise<PaginatedResponse<AsDistributionData>> {
    return request.get('/as-distribution')
  },

  // 国家分布分析
  getCountryDistribution(): Promise<PaginatedResponse<CountryDistributionData>> {
    return request.get('/country-distribution')
  },

  // 基于主机的流量分析
  getHostBasedTraffic(params: PaginationParams & HostFilterParams): Promise<PaginatedResponse<HostInfo>> {
    return request.get('/host', { params })
  },

  // 获取主机详情
  getHostDetail(address: string): Promise<SimpleResponse<HostInfo>> {
    return request.get(`/host/${address}`)
  },

  // 获取远程主机
  getRemoteHosts(params: PaginationParams): Promise<PaginatedResponse<RemoteHost>> {
    return request.get('/remote-host', { params })
  }
}

// ========== 地址分析API ==========
export const addressApi = {
  // 模式分析 (后端唯一提供的地址相关接口)
  getPatternAnalysis(params: any): Promise<PaginatedResponse<any>> {
    return request.get('/address/pattern-analysis', { params })
  }
}

// ========== 统一导出 ==========
export const networkServices = {
  ...networkApi,
  ...hostsApi,
  ...addressApi
}

export default networkServices
