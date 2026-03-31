<template>
  <div class="chat-layout" id="chatai-new-ui">
    <!-- 侧边栏 -->
    <div 
      class="sidebar" 
      :class="{ expanded: isSidebarExpanded }"
      @mouseenter="handleSidebarHover(true)"
      @mouseleave="handleSidebarHover(false)"
    >
      <div class="sidebar-header">
        <div class="logo-area">
          <v-icon color="primary">mdi-robot</v-icon>
          <span class="logo-text" v-show="isSidebarExpanded">ChatAI</span>
        </div>
        <v-btn icon small class="new-chat-btn" @click="createNewChat" title="新对话">
          <v-icon>mdi-plus</v-icon>
        </v-btn>
      </div>

      <div class="history-list">
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id"
          class="history-item"
          :class="{ active: currentChatId === chat.id }"
          @click="selectChat(chat.id)"
          v-show="isSidebarExpanded"
        >
          <v-icon size="16" color="grey">mdi-message-text-outline</v-icon>
          <span class="history-title">{{ chat.title }}</span>
          <v-btn icon x-small class="delete-btn" @click.stop="deleteChat(chat.id)">
            <v-icon size="14">mdi-close</v-icon>
          </v-btn>
        </div>
        
        <!-- 收起状态下的历史图标 -->
        <div v-show="!isSidebarExpanded" class="mini-history">
          <v-btn 
            v-for="chat in chatHistory.slice(0, 5)" 
            :key="chat.id"
            icon 
            small 
            :color="currentChatId === chat.id ? 'primary' : 'grey'"
            @click="selectChat(chat.id)"
          >
            <v-icon>mdi-message-text-outline</v-icon>
          </v-btn>
        </div>
      </div>

      <div class="sidebar-footer">
        <v-btn icon small @click="toggleSettings">
          <v-icon>mdi-cog-outline</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 欢迎页 (无消息时显示) -->
      <div v-if="!currentMessages.length" class="welcome-screen">
        <div class="welcome-header">
          <h1>ChatAI 智能分析</h1>
          <p>基于 LangGraph 的新一代网络安全分析助手</p>
        </div>

        <div class="example-grid">
          <div 
            v-for="(example, index) in exampleQuestions" 
            :key="index"
            class="example-card"
            @click="sendMessage(example.text, example.mode)"
          >
            <div class="card-icon">
              <v-icon :color="example.color">{{ example.icon }}</v-icon>
            </div>
            <div class="card-content">
              <h3>{{ example.title }}</h3>
              <p>{{ example.text }}</p>
            </div>
            <div class="card-mode">
              <v-chip x-small outlined>{{ getModeLabel(example.mode) }}</v-chip>
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
          :is-user="msg.type === 'user'"
          :loading="msg.loading"
          :query-info="msg.query_info"
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
              v-model="inputMessage"
              placeholder="输入您的问题..."
              @keydown.enter.exact.prevent="handleEnter"
              @keydown.enter.shift.exact="handleShiftEnter"
              :disabled="isTyping"
              rows="1"
              ref="textarea"
              @input="autoResize"
            ></textarea>
            
            <button 
              class="send-btn" 
              :disabled="!inputMessage.trim() || isTyping"
              @click="sendCurrentMessage"
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
    <v-dialog v-model="queryDialog" max-width="700">
      <v-card>
        <v-card-title>查询详情</v-card-title>
        <v-card-text>
          <pre class="code-block" v-if="selectedQuery">{{ JSON.stringify(selectedQuery, null, 2) }}</pre>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import MessageBubble from './components/MessageBubble.vue';
import ModeSelector from './components/ModeSelector.vue';
import chataiApi from '@/components/http/apis/chatai_api';
import { fetchEventSource } from '@microsoft/fetch-event-source';

export default {
  name: 'ChatAI',
  components: {
    MessageBubble,
    ModeSelector
  },
  data() {
    return {
      isSidebarExpanded: false,
      inputMessage: '',
      currentMode: 'normal',
      isTyping: false,
      chatHistory: [],
      currentChatId: null,
      queryDialog: false,
      selectedQuery: null,
      
      exampleQuestions: [
        {
          title: '流量趋势',
          text: '分析最近24小时的 TCP 流量趋势',
          icon: 'mdi-chart-line',
          color: 'blue',
          mode: 'normal'
        },
        {
          title: '风险检测',
          text: '检测是否存在端口扫描攻击行为',
          icon: 'mdi-shield-alert',
          color: 'red',
          mode: 'threat'
        },
        {
          title: '快速查询',
          text: '查询流量最大的前10个源IP',
          icon: 'mdi-lightning-bolt',
          color: 'amber',
          mode: 'quick'
        },
        {
          title: '主机分析',
          text: '分析IP 192.168.1.100 的行为特征',
          icon: 'mdi-desktop-tower',
          color: 'purple',
          mode: 'normal'
        }
      ]
    }
  },
  computed: {
    currentChat() {
      return this.chatHistory.find(chat => chat.id === this.currentChatId);
    },
    currentMessages() {
      return this.currentChat ? this.currentChat.messages : [];
    }
  },
  mounted() {
    this.createNewChat();
  },
  methods: {
    handleSidebarHover(isHover) {
      this.isSidebarExpanded = isHover;
    },
    
    createNewChat() {
      const newChat = {
        id: Date.now().toString(),
        title: '新对话',
        messages: []
      };
      this.chatHistory.unshift(newChat);
      this.currentChatId = newChat.id;
    },
    
    selectChat(id) {
      this.currentChatId = id;
    },
    
    deleteChat(id) {
      this.chatHistory = this.chatHistory.filter(c => c.id !== id);
      if (this.currentChatId === id) {
        this.currentChatId = this.chatHistory[0]?.id || null;
        if (!this.currentChatId) this.createNewChat();
      }
    },
    
    getModeLabel(mode) {
      const map = { quick: '快速查询', normal: '智能分析', threat: '威胁分析' };
      return map[mode] || mode;
    },
    
    getModeDesc(mode) {
      const map = {
        quick: '直接查询数据库，返回原始数据，速度最快',
        normal: '智能分析数据，提供专业洞察和建议',
        threat: '深度安全分析，输出结构化调查剧本'
      };
      return map[mode] || '';
    },
    
    autoResize() {
      const el = this.$refs.textarea;
      el.style.height = 'auto';
      el.style.height = el.scrollHeight + 'px';
    },
    
    handleEnter() {
      this.sendCurrentMessage();
    },
    
    handleShiftEnter() {
      // 默认换行
    },
    
    sendCurrentMessage() {
      if (!this.inputMessage.trim() || this.isTyping) return;
      this.sendMessage(this.inputMessage, this.currentMode);
      this.inputMessage = '';
      this.$nextTick(() => {
        this.$refs.textarea.style.height = 'auto';
      });
    },
    
    async sendMessage(text, mode) {
      if (!this.currentChatId) this.createNewChat();
      
      // 添加用户消息
      this.currentChat.messages.push({
        type: 'user',
        content: text
      });
      
      // 添加 AI 占位消息
      const aiMessageIndex = this.currentChat.messages.push({
        type: 'ai',
        content: '',
        loading: true
      }) - 1;
      
      this.isTyping = true;
      this.scrollToBottom();
      
      try {
        await this.streamResponse(text, mode, aiMessageIndex);
      } catch (error) {
        console.error('发送失败:', error);
        this.currentChat.messages[aiMessageIndex].content = `Error: ${error.message}`;
        this.currentChat.messages[aiMessageIndex].loading = false;
      } finally {
        this.isTyping = false;
      }
    },
    
    async streamResponse(text, mode, messageIndex) {
      const url = chataiApi.getStreamUrl();
      let aiContent = '';
      
      await fetchEventSource(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          chat_id: this.currentChatId,
          analysis_mode: mode,
          stream: true
        }),
        onmessage: (msg) => {
          try {
            const data = JSON.parse(msg.data);
            
            if (data.type === 'thinking') {
              // 显示思考进度...可以添加单独的 UI 状态
            } else if (data.type === 'result') {
              // 最终结果
              aiContent = data.data.ai_response;
              const msgObj = this.currentChat.messages[messageIndex];
              msgObj.content = aiContent;
              msgObj.query_info = data.data.query_info;
              msgObj.loading = false;
              
              // 如果是第一条消息，更新标题
              if (this.currentChat.messages.length <= 2) {
                this.currentChat.title = text.slice(0, 15);
              }
            } else if (data.type === 'error') {
              throw new Error(data.message);
            }
          } catch (e) {
            console.error('解析消息失败:', e);
          }
        },
        onerror: (err) => {
          throw err;
        }
      });
    },
    
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) container.scrollTop = container.scrollHeight;
      });
    },
    
    copyToClipboard(text) {
      navigator.clipboard.writeText(text);
      // 可以添加 toast 提示
    },
    
    regenerateResponse(index) {
      // 实现重新生成逻辑
    },
    
    showQueryInfo(info) {
      this.selectedQuery = info;
      this.queryDialog = true;
    },
    
    toggleSettings() {
      // 打开设置
    }
  }
}
</script>

<style scoped>
#chatai-new-ui.chat-layout {
  display: flex;
  height: 100vh;
  background-color: #ffffff;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #111827;
  position: relative; /* 确保 z-index 生效 */
}

/* 侧边栏 */
.sidebar {
  width: 60px;
  background-color: #F9FAFB;
  border-right: 1px solid #E5E7EB;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  z-index: 10;
}

.sidebar.expanded {
  width: 260px;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  font-size: 16px;
  white-space: nowrap;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}

.history-item:hover {
  background-color: #E5E7EB;
}

.history-item.active {
  background-color: #DBEAFE;
  color: #2563EB;
}

.history-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.mini-history {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #E5E7EB;
  display: flex;
  justify-content: center;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
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
  position: relative;
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

.card-mode {
  position: absolute;
  top: 12px;
  right: 12px;
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
