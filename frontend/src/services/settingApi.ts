import request, { type ApiResponse } from './request'

// 设置 API
export const settingApi = {
  // 获取系统设置
  getSystemSettings(): Promise<ApiResponse<any>> {
    return request.get('/settings/system')
  },

  // 更新系统设置
  updateSystemSettings(data: any): Promise<ApiResponse<any>> {
    return request.put('/settings/system', data)
  },

  // 获取用户设置
  getUserSettings(): Promise<ApiResponse<any>> {
    return request.get('/settings/user')
  },

  // 更新用户设置
  updateUserSettings(data: any): Promise<ApiResponse<any>> {
    return request.put('/settings/user', data)
  },

  // 修改密码
  changePassword(data: {
    oldPassword: string
    newPassword: string
  }): Promise<ApiResponse<any>> {
    return request.post('/settings/password', data)
  },

  // 获取工具配置
  getToolsConfig(): Promise<ApiResponse<any>> {
    return request.get('/settings/tools')
  },

  // 更新工具配置
  updateToolsConfig(data: any): Promise<ApiResponse<any>> {
    return request.put('/settings/tools', data)
  }
}

