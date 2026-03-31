import request, { type ApiResponse } from './request'
import type { MCPMessageResponse, MCPStatusResponse } from '@/types/api'

// 聊天会话类型定义
export interface ChatSession {
  id: number
  session_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_at?: string
  metadata?: any
}

// 聊天消息类型定义
export interface ChatMessage {
  id: number
  message_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  metadata?: any
}

// 聊天历史类型定义
export interface ChatHistory {
  session_id: string
  title: string
  created_at: string
  updated_at: string
  metadata?: any
  messages: ChatMessage[]
}

export type AnalysisMode = 'quick' | 'normal' | 'threat'

export interface SendMessagePayload {
  message: string
  chat_id?: string | null
  analysis_mode?: AnalysisMode
  stream?: boolean
  conversation_history?: Array<{ role: string; content: string }>
  context?: Record<string, any>
}

export const chataiApi = {
  // 发送消息到AI (支持模式切换与流式输出)
  sendMCPMessage(data: SendMessagePayload): Promise<ApiResponse<MCPMessageResponse>> {
    return request.post('/chatai/mcp/message', {
      analysis_mode: data.analysis_mode ?? 'normal',
      stream: data.stream ?? false,
      chat_id: data.chat_id,
      message: data.message,
      conversation_history: data.conversation_history,
      context: data.context
    })
  },

  // 获取流式请求的完整URL（SSE / fetch-event-source 使用）
  getStreamUrl(): string {
    const base = request.defaults.baseURL || import.meta.env.VITE_APP_API_BASE || '/api'
    return `${base.replace(/\/$/, '')}/chatai/mcp/message`
  },

  // 获取MCP状态 (后端提供)
  getMCPStatus(): Promise<ApiResponse<MCPStatusResponse>> {
    return request.get('/chatai/mcp/status')
  },

  // MCP查询 (后端提供)
  mcpQuery(data: {
    query: string
    service?: string
  }): Promise<ApiResponse<any>> {
    return request.post('/chatai/mcp/query', data)
  },

  // 获取数据库架构 (后端提供)
  getDatabaseSchema(): Promise<ApiResponse<any>> {
    return request.get('/chatai/mcp/schema')
  },

  // ========== 聊天记录管理API ==========

  // 创建新聊天会话
  createChatSession(data: {
    title?: string
    user_id?: string
  }): Promise<ApiResponse<ChatSession>> {
    return request.post('/chatai/storage/sessions', data)
  },

  // 获取聊天会话列表
  getChatSessions(params?: {
    user_id?: string
    limit?: number
    offset?: number
  }): Promise<ApiResponse<ChatSession[]>> {
    return request.get('/chatai/storage/sessions', { params })
  },

  // 更新会话标题
  updateChatSessionTitle(sessionId: string, title: string): Promise<ApiResponse<ChatSession>> {
    return request.put(`/chatai/storage/sessions/${sessionId}`, { title })
  },

  // 删除会话
  deleteChatSession(sessionId: string): Promise<ApiResponse<any>> {
    return request.delete(`/chatai/storage/sessions/${sessionId}`)
  },

  // 获取会话的所有消息
  getChatMessages(sessionId: string, params?: {
    limit?: number
    offset?: number
  }): Promise<ApiResponse<ChatMessage[]>> {
    return request.get(`/chatai/storage/sessions/${sessionId}/messages`, { params })
  },

  // 获取完整聊天历史
  getChatHistory(params?: {
    user_id?: string
  }): Promise<ApiResponse<ChatHistory[]>> {
    return request.get('/chatai/storage/history', { params })
  },

  // 清理过期聊天记录
  cleanupChatRecords(data?: {
    days_to_keep?: number
  }): Promise<ApiResponse<{ deleted_count: number }>> {
    return request.post('/chatai/storage/cleanup', data)
  }
}

