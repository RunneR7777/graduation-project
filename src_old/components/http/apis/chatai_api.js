import request from './request'

// ChatAI相关API
export const chataiApi = {
  // 发送消息到AI (支持新参数)
  sendMessage: (data) => {
    return request({
      url: '/chatai/mcp/message', // 统一使用新API路径
      method: 'post',
      data: {
        message: data.message,
        chat_id: data.chat_id,
        analysis_mode: data.analysis_mode || 'normal', // 模式: quick, normal, threat
        stream: data.stream || false,
        conversation_history: data.conversation_history
      }
    })
  },

  // 获取流式响应URL
  getStreamUrl: () => {
    const baseURL = process.env.VUE_APP_BASE_API || '/api';
    return `${baseURL}/chatai/mcp/message`;
  },

  // 获取聊天历史
  getChatHistory: (params) => {
    return request({
      url: '/chatai/history',
      method: 'get',
      params: params
    })
  },

  // 创建新对话
  createChat: (data) => {
    return request({
      url: '/chatai/chat',
      method: 'post',
      data: data
    })
  },

  // 删除对话
  deleteChat: (chatId) => {
    return request({
      url: `/chatai/chat/${chatId}`,
      method: 'delete'
    })
  },

  // 更新对话标题
  updateChatTitle: (chatId, title) => {
    return request({
      url: `/chatai/chat/${chatId}/title`,
      method: 'put',
      data: { title }
    })
  },

  // 获取MCP服务状态
  getMCPStatus: () => {
    return request({
      url: '/chatai/mcp/status',
      method: 'get'
    })
  },

  // 执行SQL查询 (高级功能)
  executeSQLQuery: (data) => {
    return request({
      url: '/chatai/mcp/query',
      method: 'post',
      data: data
    })
  },

  // 获取数据库schema
  getDatabaseSchema: () => {
    return request({
      url: '/chatai/mcp/schema',
      method: 'get'
    })
  }
}

export default chataiApi
