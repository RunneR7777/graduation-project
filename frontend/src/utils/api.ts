import type { ApiResponse, PaginatedResponse, SimpleResponse } from '@/types/api'

/**
 * 统一的API数据处理工具
 * 基于后端统一响应格式: {status: {code, message}, data: ...}
 */

/**
 * 处理分页数据响应
 * @param response API响应 (PaginatedResponse<T> 或 Axios 响应)
 * @returns 数据数组
 */
export function handlePaginatedResponse<T>(response: any): T[] {
  if (!response) {
    console.warn('API响应为空:', response)
    return []
  }

  // 处理 Axios 响应格式: { data: { status: {...}, data: { items: [...], total, page, itemsPerPage } }, status: 200, ... }
  if (response.data && response.data.data && response.data.data.items && Array.isArray(response.data.data.items)) {
    return response.data.data.items
  }

  // 处理直接响应格式: { status: {...}, data: { items: [...], total, page, itemsPerPage } }
  if (response.data && response.data.items && Array.isArray(response.data.items)) {
    return response.data.items
  }

  // 处理简单数组格式: { data: [...] }
  if (response.data && Array.isArray(response.data)) {
    return response.data
  }

  console.warn('无法识别的分页API响应格式:', response)
  return []
}

/**
 * 处理简单数据响应（非分页）
 * @param response API响应 (SimpleResponse<T> 或 Axios 响应)
 * @returns 数据
 */
export function handleSimpleResponse<T>(response: any): T | null {
  if (!response) {
    console.warn('API响应为空:', response)
    return null
  }

  // 处理 Axios 响应格式: { data: { status: {...}, data: {...} }, status: 200, ... }
  if (response.data && response.data.data) {
    return response.data.data
  }

  // 处理直接响应格式: { status: {...}, data: {...} }
  if (response.data) {
    return response.data
  }

  return null
}

/**
 * 获取分页信息
 * @param response API响应 (PaginatedResponse<T> 或 Axios 响应)
 * @returns 分页信息
 */
export function getPaginationInfo(response: any): { total: number; page: number; itemsPerPage: number } {
  if (!response) {
    return { total: 0, page: 1, itemsPerPage: 10 }
  }

  // 处理 Axios 响应格式: { data: { status: {...}, data: { items: [...], total, page, itemsPerPage } }, status: 200, ... }
  if (response.data && response.data.data) {
    return {
      total: response.data.data.total || 0,
      page: response.data.data.page || 1,
      itemsPerPage: response.data.data.itemsPerPage || 10
    }
  }

  // 处理直接响应格式: { status: {...}, data: { items: [...], total, page, itemsPerPage } }
  if (response.data) {
    return {
      total: response.data.total || 0,
      page: response.data.page || 1,
      itemsPerPage: response.data.itemsPerPage || 10
    }
  }

  return { total: 0, page: 1, itemsPerPage: 10 }
}

/**
 * 检查API响应是否成功
 * @param response API响应 (ApiResponse<T> 或 Axios 响应)
 * @returns 是否成功
 */
export function isApiSuccess(response: any): boolean {
  if (!response) return false
  
  // 处理 Axios 响应格式: { data: { status: { code: 200, message: "..." } }, status: 200, ... }
  if (response.data && response.data.status) {
    return response.data.status.code === 200
  }
  
  // 处理直接响应格式: { status: { code: 200, message: "..." } }
  if (response.status) {
    return response.status.code === 200
  }

  // 处理 HTTP 状态码
  if (typeof response.status === 'number') {
    return response.status >= 200 && response.status < 300
  }
  
  return false
}

/**
 * 获取API错误信息
 * @param response API响应 (ApiResponse<T> 或 Axios 响应)
 * @returns 错误信息
 */
export function getApiErrorMessage(response: any): string {
  if (!response) return '未知错误'
  
  // 处理 Axios 响应格式: { data: { status: { code: 500, message: "error message" } }, status: 200, ... }
  if (response.data && response.data.status) {
    return response.data.status.message || '未知错误'
  }
  
  // 处理直接响应格式: { status: { code: 500, message: "error message" } }
  if (response.status) {
    return response.status.message || '未知错误'
  }

  // 处理 Axios 错误
  if (response.message) {
    return response.message
  }
  
  return '未知错误'
}

/**
 * 统一的API数据处理函数（兼容旧版本）
 * @param response API响应
 * @returns 数据数组
 */
export function handleListResponse<T>(response: PaginatedResponse<T>): T[] {
  return handlePaginatedResponse<T>(response)
}