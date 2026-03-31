<!-- 
  ChatAI 引擎选择器组件
  用于选择不同的分析引擎
-->

<template>
  <div class="chatai-engine-selector">
    <!-- 引擎选择器 -->
    <div class="engine-options">
      <div 
        class="engine-option"
        :class="{ active: selectedEngine === 'original' }"
        @click="selectEngine('original')"
      >
        <div class="engine-icon">⚡</div>
        <div class="engine-info">
          <div class="engine-name">简单查询</div>
          <!-- <div class="engine-desc">原有引擎 · 2-3秒</div> -->
        </div>
      </div>
      
      <div 
        class="engine-option"
        :class="{ active: selectedEngine === 'langchain_normal' }"
        @click="selectEngine('langchain_normal')"
      >
        <div class="engine-icon">🔍</div>
        <div class="engine-info">
          <div class="engine-name">智能分析</div>
          <!-- <div class="engine-desc">LangChain · 5-10秒</div> -->
        </div>
      </div>
      
      <div 
        class="engine-option"
        :class="{ active: selectedEngine === 'langchain_threat' }"
        @click="selectEngine('langchain_threat')"
      >
        <div class="engine-icon">🛡️</div>
        <div class="engine-info">
          <div class="engine-name">威胁分析</div>
          <!-- <div class="engine-desc">深度调查 · 10-20秒</div> -->
        </div>
      </div>
    </div>
    
    <!-- 思考过程显示 -->
    <div v-if="thinking" class="thinking-process">
      <div class="thinking-step">
        <div class="thinking-icon">
          <div class="spinner"></div>
        </div>
        <div class="thinking-text">
          {{ thinkingStep }}
        </div>
        <div class="thinking-progress">
          <div class="progress-bar" :style="{ width: thinkingProgress + '%' }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatAIEngineSelector',
  
  data() {
    return {
      selectedEngine: 'original',  // 默认选择原引擎
      thinking: false,
      thinkingStep: '',
      thinkingProgress: 0
    };
  },
  
  methods: {
    selectEngine(engine) {
      this.selectedEngine = engine;
      this.$emit('engine-change', engine);
    },
    
    getEngineConfig() {
      // 返回当前选择的引擎配置
      return {
        use_langchain: this.selectedEngine !== 'original',
        analysis_mode: this.selectedEngine === 'langchain_threat' ? 'threat' : 'normal'
      };
    },
    
    showThinking(step, progress) {
      // 显示思考步骤
      this.thinking = true;
      this.thinkingStep = step;
      this.thinkingProgress = progress;
    },
    
    hideThinking() {
      // 隐藏思考过程
      this.thinking = false;
      this.thinkingStep = '';
      this.thinkingProgress = 0;
    },
    
    async sendMessage(message, chatId) {
      if (this.thinking) {
        console.warn('正在处理中，请稍后...');
        return;
      }
      // 构建请求参数
      const payload = {
        message: message,
        chat_id: chatId,
        stream: true,  // 启用流式输出
        ...this.getEngineConfig()
      };
      
      // 使用 EventSource 接收流式响应
      this.thinking = true;
      this.thinkingStep = '正在连接...';
      this.thinkingProgress = 0;
      
      try {
        const response = await fetch('/api/chatai/mcp/message', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });
        
        if (!payload.stream) {
          // 非流式响应
          const data = await response.json();
          this.thinking = false;
          return data;
        }
        
        // 流式响应处理
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let accumulatedText = '';  // 累积的文本内容
        let isInThinkingPhase = false;  // 是否在思考阶段
        let isInAnswerPhase = false;  // 是否在回答阶段
        
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) {
            this.thinking = false;
            break;
          }
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop();  // 保留不完整的行
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'thinking') {
                // 更新思考步骤
                this.thinkingStep = data.step;
                this.thinkingProgress = data.progress;
                this.$emit('thinking-update', { step: data.step, progress: data.progress });
              } else if (data.type === 'streaming') {
                // 流式文本内容
                const chunk = data.content || '';
                accumulatedText += chunk;
                
                // 检测 <thinking/> 标记
                if (accumulatedText.includes('<thinking/>')) {
                  isInThinkingPhase = true;
                  this.thinking = true;
                  this.thinkingStep = '正在思考...';
                  this.thinkingProgress = 50;
                }
                
                // 检测 <answer> 标记
                if (accumulatedText.includes('<answer>')) {
                  isInAnswerPhase = true;
                  isInThinkingPhase = false;
                  this.thinking = false;
                  
                  // 提取 <answer> 后的内容
                  const answerStart = accumulatedText.indexOf('<answer>') + 8;
                  const answerContent = accumulatedText.substring(answerStart);
                  
                  // 发送部分答案更新
                  this.$emit('answer-streaming', answerContent);
                }
                
                // 如果已经在回答阶段，继续发送更新
                if (isInAnswerPhase && !accumulatedText.includes('<answer>')) {
                  this.$emit('answer-streaming', chunk);
                }
              } else if (data.type === 'result') {
                // 最终结果
                this.thinking = false;
                
                // 清理响应文本（移除标记）
                let finalResponse = data.data.ai_response || '';
                finalResponse = finalResponse.replace(/<thinking\/>/g, '').replace(/<answer>/g, '').trim();
                
                // 更新最终数据
                const finalData = {
                  ...data.data,
                  ai_response: finalResponse
                };
                
                this.$emit('message-received', finalData);
                return finalData;
              } else if (data.type === 'error') {
                // 错误处理
                this.thinking = false;
                this.$emit('error', data.message);
                throw new Error(data.message);
              }
            }
          }
        }
      } catch (error) {
        this.thinking = false;
        this.$emit('error', error.message);
        throw error;
      }
    }
  }
};
</script>

<style scoped>
.chatai-engine-selector {
  margin-bottom: 16px;
}

.engine-options {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.engine-option {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.engine-option:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

.engine-option.active {
  border-color: #1890ff;
  background: #e6f7ff;
}

.engine-icon {
  font-size: 24px;
  margin-right: 12px;
}

.engine-info {
  flex: 1;
}

.engine-name {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
}

.engine-desc {
  font-size: 12px;
  color: #999;
}

/* 思考过程样式 */
.thinking-process {
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 16px;
}

.thinking-step {
  display: flex;
  align-items: center;
  gap: 12px;
}

.thinking-icon {
  width: 24px;
  height: 24px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid #e0e0e0;
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.thinking-text {
  flex: 1;
  font-size: 14px;
  color: #666;
}

.thinking-progress {
  width: 100px;
  height: 4px;
  background: #e0e0e0;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #1890ff, #52c41a);
  transition: width 0.3s;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .engine-options {
    flex-direction: column;
  }
  
  .engine-option {
    width: 100%;
  }
}
</style>

