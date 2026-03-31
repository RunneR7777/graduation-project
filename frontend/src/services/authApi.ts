import request, { type ApiResponse } from './request'

// 认证 API
export const authApi = {
  // 用户登录获取Token
  login(username: string, password: string): Promise<ApiResponse<{
    token: string
    user: {
      username: string
      role: string
    }
  }>> {
    return request.get('/token', {
      params: { username, password }
    })
  },

  // 用户登出
  logout(): Promise<ApiResponse<any>> {
    return request.post('/auth/logout')
  },

  // 验证Token有效性
  verifyToken(): Promise<ApiResponse<{
    valid: boolean
    user?: any
  }>> {
    return request.get('/auth/verify')
  },

  // 刷新Token
  refreshToken(): Promise<ApiResponse<{
    token: string
  }>> {
    return request.post('/auth/refresh')
  }
}

