<template>
  <div class="message-bubble" :class="isUser ? 'user' : 'ai'">
    <div class="avatar">
      <div v-if="isUser" class="user-avatar">U</div>
      <div v-else class="ai-avatar">
        <v-icon color="white" size="18">mdi-robot</v-icon>
      </div>
    </div>
    
    <div class="content-wrapper">
      <div class="sender-name">{{ isUser ? 'You' : 'ChatAI' }}</div>
      
      <div class="message-card">
        <template v-if="isUser">
          <div class="user-text">{{ content }}</div>
        </template>
        <template v-else>
          <div v-if="loading" class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
          <markdown-renderer 
            v-else 
            :content="content" 
          />
          
          <!-- 消息操作栏 -->
          <div v-if="!loading" class="message-actions">
            <v-btn icon x-small @click="$emit('copy', content)" title="复制">
              <v-icon size="14">mdi-content-copy</v-icon>
            </v-btn>
            <v-btn icon x-small @click="$emit('regenerate')" title="重新生成">
              <v-icon size="14">mdi-refresh</v-icon>
            </v-btn>
            <v-btn 
              v-if="queryInfo" 
              icon 
              x-small 
              @click="$emit('show-query', queryInfo)"
              title="查看查询详情"
            >
              <v-icon size="14">mdi-database-search</v-icon>
            </v-btn>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import MarkdownRenderer from './MarkdownRenderer.vue';

export default {
  name: 'MessageBubble',
  components: {
    MarkdownRenderer
  },
  props: {
    content: {
      type: String,
      required: true
    },
    isUser: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    queryInfo: {
      type: Object,
      default: null
    }
  }
}
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  padding: 0 16px;
}

.message-bubble.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  margin-top: 4px;
}

.user-avatar {
  width: 100%;
  height: 100%;
  background: #3B82F6;
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.ai-avatar {
  width: 100%;
  height: 100%;
  background: #10B981;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-wrapper {
  flex: 1;
  max-width: calc(100% - 48px);
}

.sender-name {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
  display: none; /* 默认隐藏名字，追求极简 */
}

.message-card {
  position: relative;
}

.user .user-text {
  background: #F3F4F6;
  padding: 12px 16px;
  border-radius: 12px;
  color: #111827;
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.message-bubble:hover .message-actions {
  opacity: 1;
}

/* 打字机动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #9CA3AF;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
