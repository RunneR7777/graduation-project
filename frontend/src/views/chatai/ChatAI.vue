<template>
  <div class="chat-layout">
    <!-- 侧边栏 -->
    <div 
      class="sidebar" 
      :class="{ collapsed: !isSidebarExpanded }"
    >
      <div class="sidebar-header">
        <div class="logo-area">
          <v-icon color="primary">mdi-robot</v-icon>
          <span class="logo-text" v-show="isSidebarExpanded">ChatAI</span>
        </div>
        <div class="header-actions">
          <v-btn 
            icon 
            small 
            class="sidebar-toggle" 
            @click="toggleSidebar"
            :title="isSidebarExpanded ? '收起侧边栏' : '展开侧边栏'"
          >
            <v-icon>{{ isSidebarExpanded ? 'mdi-menu' : 'mdi-menu-open' }}</v-icon>
          </v-btn>
          <v-btn 
            icon 
            small 
            class="new-chat-btn" 
            @click="createNewChat" 
            title="新对话"
          >
            <v-icon>mdi-plus</v-icon>
          </v-btn>
        </div>
      </div>

      <div class="history-list">
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          class="history-item"
          :class="{ active: currentChatId === chat.session_id }"
          @click="selectChat(chat.session_id)"
        >
          <v-icon size="18" class="history-icon">mdi-message-text-outline</v-icon>
          <span class="history-title" v-show="isSidebarExpanded">{{ chat.title }}</span>
          <v-btn 
            v-show="isSidebarExpanded"
            icon 
            x-small 
            class="delete-btn" 
            @click.stop="confirmDeleteChat(chat.session_id)"
          >
            <v-icon size="14">mdi-close</v-icon>
          </v-btn>
        </div>
      </div>

      <div class="sidebar-footer" v-show="isSidebarExpanded">
        <v-btn text small @click="openSettings" class="footer-btn">
          <v-icon left size="16">mdi-cog-outline</v-icon>
          设置
        </v-btn>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content" :class="{ 'sidebar-collapsed': !isSidebarExpanded }">
      <!-- 顶部工具栏 -->
      <div class="top-bar" v-if="currentChat">
        <div class="top-bar-title">
          {{ currentChat.title }}
        </div>
      </div>
      <!-- 欢迎页 (无消息时显示) -->
      <div v-if="!currentMessages.length" class="welcome-screen">
        <div class="welcome-header">
          <h1>ChatAI 智能分析</h1>
          <p>基于 LangGraph 的新一代网络安全分析助手</p>
        </div>

        <div class="example-grid">
          <div 
            v-for="(example, index) in questionTemplates" 
            :key="index"
            class="example-card"
            @click="sendQuickQuestion(example.question)"
          >
            <div class="card-icon">
              <v-icon :color="example.color">{{ example.icon }}</v-icon>
            </div>
            <div class="card-content">
              <h3>{{ example.title }}</h3>
              <p>{{ example.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-else class="messages-container" ref="messagesContainer">
        <message-bubble
          v-for="(msg, index) in currentMessages"
          :key="index"
          :content="msg.content"
          :is-user="msg.role === 'user'"
          :loading="(msg as any).loading"
          :query-info="(msg as any).queryInfo"
          @copy="copyToClipboard"
          @regenerate="regenerateResponse(index)"
          @show-query="showQueryInfo"
        />
      </div>

      <!-- 底部输入区 -->
      <div class="input-area">
        <div class="input-container">
          <div class="mode-bar">
            <mode-selector v-model="currentMode" />
            <span class="mode-desc">{{ getModeDesc(currentMode) }}</span>
          </div>
          
          <div class="input-wrapper">
            <textarea
              v-model="currentMessage"
              placeholder="输入您的问题..."
              @keydown.enter.exact.prevent="handleEnter"
              @keydown.enter.shift.exact="handleShiftEnter"
              :disabled="isTyping"
              rows="1"
              ref="textareaRef"
              @input="autoResize"
            ></textarea>
            
            <button 
              class="send-btn" 
              :disabled="!currentMessage.trim() || isTyping"
              @click="sendMessage"
            >
              <v-icon color="white" size="18">mdi-arrow-up</v-icon>
            </button>
          </div>
          
          <div class="input-footer">
            <span>Powered by DeepSeek & LangChain Agent</span>
            <span v-if="isTyping" class="status-text">
              <v-icon size="12" class="spin-icon">mdi-loading</v-icon> 正在生成...
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 查询详情对话框 -->
    <v-dialog v-model="queryInfoDialog" max-width="700">
      <v-card>
        <v-card-title>查询详情</v-card-title>
        <v-card-text>
          <pre class="code-block" v-if="selectedQueryInfo">{{ JSON.stringify(selectedQueryInfo, null, 2) }}</pre>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { ChatMessage, MCPMessageResponse, MCPStatusResponse, EChartsConfig } from '@/types/api'
import { chataiApi } from '@/services'
import type { ChatSession, SendMessagePayload } from '@/services/chataiApi'
import MessageBubble from '@/components/chatai/MessageBubble.vue'
import ModeSelector from '@/components/chatai/ModeSelector.vue'
import { fetchEventSource } from '@microsoft/fetch-event-source'

const router = useRouter()

// 响应式数据
const isSidebarExpanded = ref(true) // 默认展开，类似 Claude
const currentMessage = ref('')
const currentMode = ref<'quick' | 'normal' | 'threat'>('normal')
const isTyping = ref(false)
const currentChatId = ref<string | null>(null)
const chatHistory = ref<ChatSession[]>([])
const currentMessages = ref<ChatMessage[]>([])
const queryInfoDialog = ref(false)
const selectedQueryInfo = ref<any>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const messagesContainer = ref<HTMLElement | null>(null)

// 计算属性
const currentChat = computed(() => 
  chatHistory.value.find((chat: ChatSession) => chat.session_id === currentChatId.value)
)

// 快速问题模板
const questionTemplates = ref([
  {
    title: '流量趋势',
    question: '分析最近24小时的 TCP 流量趋势',
    description: '查看网络流量变化',
    icon: 'mdi-chart-line',
    color: 'blue'
  },
  {
    title: '风险检测',
    question: '检测网络中的高风险主机',
    description: '识别潜在的安全威胁',
    icon: 'mdi-shield-alert',
    color: 'red'
  },
  {
    title: '快速查询',
    question: '查询流量最大的前10个源IP',
    description: '获取实时数据统计',
    icon: 'mdi-lightning-bolt',
    color: 'amber'
  },
  {
    title: '主机分析',
    question: '分析特定IP的行为特征',
    description: '深入了解主机行为',
    icon: 'mdi-desktop-tower',
    color: 'purple'
  }
])

// 方法
const toggleSidebar = () => {
  isSidebarExpanded.value = !isSidebarExpanded.value
}

const createNewChat = async () => {
  try {
    // 先检查是否已经存在空对话（标题为"新对话"且没有消息）
    const existingEmptyChat = chatHistory.value.find(
      (chat: ChatSession) => chat.title === '新对话' && chat.message_count === 0
    )
    
    if (existingEmptyChat) {
      // 如果已存在空对话，直接使用它
      currentChatId.value = existingEmptyChat.session_id
      currentMessages.value = []
      return
    }
    
    // 否则创建新对话
    const response = await chataiApi.createChatSession({
      title: '新对话',
      user_id: 'default_user'
    })
    
    if (response.data && (response.data as any).code === 200) {
      const newChat = (response.data as any).data
      chatHistory.value.unshift(newChat)
      currentChatId.value = newChat.session_id
      currentMessages.value = []
    }
  } catch (error) {
    console.error('创建会话失败:', error)
  }
}

const selectChat = async (id: string) => {
  currentChatId.value = id
  try {
    const response = await chataiApi.getChatMessages(id)
    if ((response.data as any).code === 200) {
      currentMessages.value = (response.data as any).data
    }
  } catch (error) {
    console.error('加载消息失败:', error)
  }
}

const confirmDeleteChat = async (id: string) => {
  if (confirm('确定要删除此会话吗？')) {
    try {
      await chataiApi.deleteChatSession(id)
      chatHistory.value = chatHistory.value.filter(c => c.session_id !== id)
      if (currentChatId.value === id) {
        currentChatId.value = null
        currentMessages.value = []
        // 如果还有其他对话，选中第一个；否则创建新对话
        if (chatHistory.value.length > 0) {
          selectChat(chatHistory.value[0].session_id)
        } else {
          createNewChat()
        }
      }
    } catch (error) {
      console.error('删除会话失败:', error)
    }
  }
}

const getModeDesc = (mode: string) => {
  const map: Record<string, string> = {
    quick: '直接查询数据库，返回原始数据，速度最快',
    normal: '智能分析数据，提供专业洞察和建议',
    threat: '深度安全分析，输出结构化调查剧本'
  }
  return map[mode] || ''
}

const autoResize = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = textareaRef.value.scrollHeight + 'px'
  }
}

const handleEnter = () => {
  sendMessage()
}

const handleShiftEnter = () => {
  // 默认换行
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isTyping.value) return
  
  if (!currentChatId.value) {
    await createNewChat()
  }

  const userMsgText = currentMessage.value
  currentMessage.value = ''
  
  // 添加用户消息
  currentMessages.value.push({
    id: Date.now(),
    message_id: Date.now().toString(),
    role: 'user',
    content: userMsgText,
    created_at: new Date().toISOString()
  } as any)

  // 添加 AI 占位消息
  const aiMsgId = Date.now() + 1
  currentMessages.value.push({
    id: aiMsgId,
    message_id: aiMsgId.toString(),
    role: 'assistant',
    content: '',
    created_at: new Date().toISOString(),
    loading: true
  } as any)

  isTyping.value = true
  await scrollToBottom()

  try {
    await streamResponse(userMsgText, currentChatId.value!)
  } catch (error) {
    console.error('发送失败:', error)
    const lastMsg = currentMessages.value[currentMessages.value.length - 1]
    lastMsg.content = `Error: ${error instanceof Error ? error.message : String(error)}`
    ;(lastMsg as any).loading = false
  } finally {
    isTyping.value = false
  }
}

const sendQuickQuestion = (question: string) => {
  currentMessage.value = question
  sendMessage()
}

const streamResponse = async (text: string, chatId: string) => {
  const url = chataiApi.getStreamUrl()
  const lastMsgIndex = currentMessages.value.length - 1
  let aiContent = ''

  await fetchEventSource(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: text,
      chat_id: chatId,
      analysis_mode: currentMode.value,
      stream: true
    }),
    onmessage(msg) {
      try {
        const data = JSON.parse(msg.data)
        if (data.type === 'thinking') {
          // 可选：显示思考状态
        } else if (data.type === 'result') {
          aiContent = data.data.ai_response
          const msgObj = currentMessages.value[lastMsgIndex]
          msgObj.content = aiContent
          ;(msgObj as any).queryInfo = data.data.query_info
          ;(msgObj as any).loading = false
          
          // 更新会话标题（如果是第一条消息）
          if (currentMessages.value.length <= 2) {
            updateChatTitle(chatId, text.slice(0, 15))
          }
        } else if (data.type === 'error') {
          throw new Error(data.message)
        }
      } catch (e) {
        console.error('解析消息失败:', e)
      }
    },
    onerror(err) {
      throw err
    }
  })
}

const updateChatTitle = async (sessionId: string, title: string) => {
  try {
    await chataiApi.updateChatSessionTitle(sessionId, title)
    const chat = chatHistory.value.find(c => c.session_id === sessionId)
    if (chat) chat.title = title
  } catch (error) {
    console.error('更新标题失败:', error)
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
}

const regenerateResponse = (index: number) => {
  // 重新生成逻辑：移除当前及之后的消息，重新发送上一条用户消息
  if (index > 0) {
    const userMsg = currentMessages.value[index - 1]
    if (userMsg.role === 'user') {
      currentMessages.value.splice(index - 1)
      currentMessage.value = userMsg.content
      sendMessage()
    }
  }
}

const showQueryInfo = (info: any) => {
  selectedQueryInfo.value = info
  queryInfoDialog.value = true
}

const openSettings = () => {
  router.push('/settings')
}

const logout = () => {
  router.push('/login')
}

// 初始化加载
onMounted(async () => {
  try {
    const response = await chataiApi.getChatSessions({ user_id: 'default_user' })
    if ((response.data as any).code === 200) {
      let sessions = (response.data as any).data
      
      // 过滤重复的空对话：找出所有标题为"新对话"且没有消息的会话
      const emptyNewChats = sessions.filter((s: ChatSession) => 
        s.title === '新对话' && s.message_count === 0
      )
      
      // 如果有多个空对话，只保留最新的一个，删除其他的
      if (emptyNewChats.length > 1) {
        // 按创建时间排序，保留最新的
        emptyNewChats.sort((a: ChatSession, b: ChatSession) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        
        // 删除除了最新之外的所有空对话
        const toDelete = emptyNewChats.slice(1)
        for (const session of toDelete) {
          try {
            await chataiApi.deleteChatSession(session.session_id)
          } catch (error) {
            console.error('删除重复空对话失败:', error)
          }
        }
        
        // 从列表中移除已删除的会话
        sessions = sessions.filter((s: ChatSession) => 
          !toDelete.some((deleted: ChatSession) => deleted.session_id === s.session_id)
        )
      }
      
      chatHistory.value = sessions
      
      if (chatHistory.value.length === 0) {
        createNewChat()
      } else {
        // 默认选中第一个
        selectChat(chatHistory.value[0].session_id)
      }
    }
  } catch (error) {
    console.error('加载历史失败:', error)
  }
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  background-color: #ffffff;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #111827;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background-color: #F9FAFB;
  border-right: 1px solid #E5E7EB;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 10;
  position: relative;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 56px;
  border-bottom: 1px solid #E5E7EB;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  font-size: 16px;
  white-space: nowrap;
  flex: 1;
  user-select: none;
}

.logo-text {
  font-size: 15px;
  color: #111827;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.sidebar-toggle,
.new-chat-btn {
  flex-shrink: 0;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  scrollbar-width: thin;
  scrollbar-color: #D1D5DB transparent;
}

.history-list::-webkit-scrollbar {
  width: 6px;
}

.history-list::-webkit-scrollbar-thumb {
  background-color: #D1D5DB;
  border-radius: 3px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
  position: relative;
  margin-bottom: 2px;
}

.history-item:hover {
  background-color: #F3F4F6;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.history-item.active {
  background-color: #EFF6FF;
  color: #2563EB;
}

.history-icon {
  flex-shrink: 0;
  color: #6B7280;
}

.history-item.active .history-icon {
  color: #2563EB;
}

.history-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
  line-height: 1.4;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #E5E7EB;
}

.footer-btn {
  width: 100%;
  justify-content: flex-start;
  text-transform: none;
  color: #6B7280;
  font-size: 14px;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 顶部工具栏 */
.top-bar {
  height: 56px;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  align-items: center;
  padding: 0 16px;
  background: white;
  position: sticky;
  top: 0;
  z-index: 5;
}

.top-bar-title {
  font-size: 15px;
  font-weight: 500;
  color: #111827;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 欢迎页 */
.welcome-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 40px;
}

.welcome-header {
  text-align: center;
}

.welcome-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #2563EB, #4F46E5);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.example-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  max-width: 800px;
  width: 100%;
}

.example-card {
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.example-card:hover {
  border-color: #2563EB;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
  transform: translateY(-2px);
}

.card-content h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}

.card-content p {
  font-size: 13px;
  color: #6B7280;
  margin: 0;
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  scroll-behavior: smooth;
}

/* 输入区域 */
.input-area {
  padding: 24px;
  background: linear-gradient(to top, white 80%, rgba(255,255,255,0));
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  transition: border-color 0.2s;
}

.input-container:focus-within {
  border-color: #2563EB;
}

.mode-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #F3F4F6;
}

.mode-desc {
  font-size: 12px;
  color: #9CA3AF;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

textarea {
  flex: 1;
  border: none;
  resize: none;
  outline: none;
  font-family: inherit;
  font-size: 15px;
  line-height: 1.5;
  max-height: 200px;
  padding: 8px 0;
  color: #111827;
}

.send-btn {
  width: 32px;
  height: 32px;
  background: #2563EB;
  border-radius: 8px;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
}

.send-btn:disabled {
  background: #E5E7EB;
  cursor: not-allowed;
}

.input-footer {
  margin-top: 8px;
  text-align: center;
  font-size: 11px;
  color: #9CA3AF;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.status-text {
  color: #2563EB;
  display: flex;
  align-items: center;
  gap: 4px;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  font-family: monospace;
}
</style>
