<template>
  <div class="message-bubble" :class="bubbleClass">
    <div class="avatar">
      <div v-if="isUser" class="user-avatar">U</div>
      <div v-else class="ai-avatar">
        <v-icon size="18" color="white">mdi-robot</v-icon>
      </div>
    </div>

    <div class="content">
      <div class="sender" v-if="showSender">{{ senderLabel }}</div>

      <div class="message-card">
        <template v-if="isUser">
          <div class="user-text">{{ content }}</div>
        </template>
        <template v-else>
          <div v-if="loading" class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <markdown-renderer v-else :content="content" />

          <div v-if="!loading" class="actions">
            <v-btn icon="mdi-content-copy" size="x-small" variant="text"
                   @click="emit('copy', content)" />
            <v-btn icon="mdi-refresh" size="x-small" variant="text"
                   @click="emit('regenerate')" />
            <v-btn v-if="queryInfo" icon="mdi-database-search" size="x-small" variant="text"
                   @click="emit('show-query', queryInfo)" />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import MarkdownRenderer from './MarkdownRenderer.vue';

interface Props {
  content: string;
  isUser?: boolean;
  loading?: boolean;
  queryInfo?: Record<string, unknown> | null;
  showSender?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  isUser: false,
  loading: false,
  queryInfo: null,
  showSender: false,
});

const emit = defineEmits<{
  copy: [string];
  regenerate: [];
  'show-query': [Record<string, unknown>];
}>();

const bubbleClass = computed(() => (props.isUser ? 'user' : 'ai'));
const senderLabel = computed(() => (props.isUser ? 'You' : 'ChatAI'));
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  max-width: 900px;
  margin-left: auto;
  margin-right: auto;
  padding: 0 16px;
}

.message-bubble.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  margin-top: 4px;
}

.user-avatar,
.ai-avatar {
  width: 100%;
  height: 100%;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.user-avatar {
  background: #e5edff;
  color: #2563eb;
}

.ai-avatar {
  background: #10b981;
}

.content {
  flex: 1;
}

.sender {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 4px;
}

.message-card {
  background: white;
  border-radius: 16px;
  padding: 16px 20px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.message-bubble.user .message-card {
  background: #f3f6ff;
  box-shadow: none;
  border-color: transparent;
}

.user-text {
  white-space: pre-wrap;
  color: #1f2937;
}

.actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message-card:hover .actions {
  opacity: 1;
}

.typing-indicator {
  display: flex;
  gap: 5px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #d1d5db;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>

