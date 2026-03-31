// 通用分页参数
export interface PaginationParams {
  page: number
  itemsPerPage: number
  sortBy?: string
  sortDesc?: boolean
}

/**
 * 标准API响应格式（匹配后端Response类）
 * 后端格式: {status: {code: number, message: string}, data: T}
 */
export interface ApiResponse<T = any> {
  status: {
    code: number      // HTTP状态码 (200=成功, 4xx=客户端错误, 5xx=服务器错误)
    message: string   // 响应消息
  }
  data: T            // 实际数据
}

// 分页数据响应格式
export interface PaginatedResponse<T = any> {
  status: {
    code: number
    message: string
  }
  data: {
    items: T[]
    total: number
    page: number
    itemsPerPage: number
  }
}

// 简单数据响应格式（非分页）
export interface SimpleResponse<T = any> {
  status: {
    code: number
    message: string
  }
  data: T
}

// 流量记录类型（支持多种接口格式）
export interface TrafficRecord {
  id: string
  protocol: string  // 协议
  
  // 所有流量接口字段
  lastSeen?: string  // 时间戳
  duration?: string  // 持续时间（格式："0:00:00"）
  score?: number     // 评分
  flow?: {
    source: string      // 源地址:端口
    destination: string // 目标地址:端口
  }
  throughput?: string   // 吞吐量
  totalBytes?: string   // 总字节数（格式："48 B"）
  type?: string         // 流量类型（如"正常流量"、"加密流量"）
  
  // 进站/出站/危险流量接口字段
  sourceIP?: string       // 源IP
  destIP?: string         // 目标IP
  port?: number           // 端口
  size?: string           // 数据大小
  packets?: number        // 数据包数
  timestamp?: string      // 时间戳
  riskLevel?: string      // 风险等级
  riskReasons?: string[]  // 风险原因列表
}

// 主机信息类型（匹配后端 /api/host 返回格式）
export interface HostInfo {
  address: string          // IP地址
  flows: number            // 流数量
  alerts: string           // 警报信息
  score: string            // 评分
  cves: string             // CVE信息
  seenSince: string        // 首次见到时间
  sentPercentage: number   // 发送百分比
  throughput: string       // 吞吐量（如"1167.00 Kbps"）
  totalBytes: string       // 总字节数（如"1.14 MB"）
  random: boolean          // 是否随机
  riskLevel: string        // 风险等级（中文："低"/"中"/"高"）
  asn: string              // ASN号
  asnName: string          // ASN名称
  prefix: string           // 前缀
  orgName: string          // 组织名称
  country: string          // 国家
}

// 仪表盘统计数据
export interface DashboardStats {
  total_flows: number
  active_hosts: number
  risk_alerts: number
  ipv6_addresses: number
}

// 图表数据类型（ECharts格式）
export interface ChartData {
  name: string
  value: number
  color?: string
}

// 流量趋势数据
export interface TrafficTrendData {
  time: string
  inbound: number
  outbound: number
  risk: number
}

// AS分布数据（匹配后端 /api/as-distribution 返回格式）
export interface AsDistributionData {
  asNumber: string         // AS号（字符串）
  name: string             // AS名称
  hosts: number            // 主机数量
  seenSince: string        // 首次发现时间
  sentPercentage: number   // 发送百分比
  throughput: string       // 吞吐量
  traffic: string          // 流量（格式化字符串）
  trafficBytes?: number    // 流量原始字节数
}

// 国家分布数据（匹配后端 /api/country-distribution 返回格式）
export interface CountryDistributionData {
  code: string             // 国家代码
  name: string             // 国家名称
  hosts: number            // 主机数量
  seenSince: string        // 首次发现时间
  sentPercentage: number   // 发送百分比
  throughput: string       // 吞吐量
  traffic: string          // 流量（格式化字符串）
  trafficBytes?: number    // 流量原始字节数
}

// 远程主机类型（匹配后端 /api/remote-host 返回格式）
export interface RemoteHost {
  address: string          // IP地址
  lastSeen: string         // 最后发现时间
  activity: number         // 活跃度
  sentPercentage: number   // 发送百分比
  asn: string              // ASN号
  asnName: string          // ASN名称
  prefix: string           // 前缀
  orgName: string          // 组织名称
  country: string          // 国家
}

// 地址分析数据
export interface AddressAnalysisData {
  address: string
  type: 'ipv4' | 'ipv6'
  first_seen: string
  last_seen: string
  activity_count: number
  risk_level: 'low' | 'medium' | 'high'
}

// ChatAI消息类型
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  type?: 'text' | 'chart' | 'table'
}

// MCP消息响应数据类型
export interface MCPMessageResponse {
  ai_response: string
  timestamp: string
  query_info?: {
    intent: string
    query_type: string
    sql_query: string
    explanation?: string
  }
  follow_up_questions?: string[]
  visualization_type?: string
  raw_data?: any
  has_chart?: boolean
  chart_config?: EChartsConfig
}

// ECharts配置类型
export interface EChartsConfig {
  title?: any
  tooltip?: any
  legend?: any
  xAxis?: any
  yAxis?: any
  series?: any[]
  [key: string]: any
}

// MCP状态响应数据类型
export interface MCPStatusResponse {
  mcp_available: boolean
  services?: string[]
  database_connected?: boolean
}

// 筛选参数
export interface TrafficFilterParams {
  srcIp?: string
  dstIp?: string
  protocol?: string
  startTime?: string
  endTime?: string
  riskLevel?: string
}

export interface HostFilterParams {
  ipVersion?: string
  country?: string
  asNumber?: number
  riskLevel?: string
}

// IPv6地址类型
export interface IPv6Address {
  address: string
  status: 'active' | 'inactive' | 'suspicious' | 'unknown'
  response_time: number
  detection_count: number
  success_rate: number
  last_seen: string
}

// 地址模式类型
export interface AddressPattern {
  id: string
  name: string
  type: 'sequential' | 'frequent' | 'association' | 'clustering'
  support: number
  confidence: number
  count: number
  anomaly_score: number
  description: string
  example_addresses: string[]
}

// 地址统计类型
export interface AddressStatistics {
  prefix: string
  total_addresses: number
  active_addresses: number
  active_rate: number
  suspicious_addresses: number
  risk_level: 'low' | 'medium' | 'high'
  last_updated: string
}

// 风险主机类型（匹配后端 /api/risk-hosts 返回格式）
export interface RiskHost {
  ipAddress: string        // IP地址
  hostname: string         // 主机名
  location: string         // 位置/国家
  riskType: string         // 风险类型（中文）
  riskLevel: number        // 风险等级（数字1-5）
  firstSeen: string        // 首次发现时间
  lastSeen: string         // 最后发现时间
  flows: number            // 流数量
  sentBytes: number        // 发送字节数
  receivedBytes: number    // 接收字节数
  riskReasons: string[]    // 风险原因列表
  riskScore: number        // 风险评分
}

// 端口风险类型
export interface PortRisk {
  port: number
  protocol: string
  service: string
  version: string
  risk_level: 'low' | 'medium' | 'high'
  risk_score: number
  status: string
  last_scan: string
  description: string
  recommendation: string
}

// API端点类型
export interface ApiEndpoint {
  id: string
  path: string
  method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  category: string
  description: string
  status: 'active' | 'deprecated' | 'inactive'
  avgResponseTime: number
  successRate: number
  parameters: ApiParameter[]
  responseExample: string
  statusCodes: ApiStatusCode[]
}

export interface ApiParameter {
  name: string
  type: string
  required: boolean
  description: string
}

export interface ApiStatusCode {
  code: number
  description: string
}
