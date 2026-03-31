<template>
  <div class="mode-selector">
    <div 
      v-for="mode in modes" 
      :key="mode.value"
      class="mode-item"
      :class="{ active: value === mode.value }"
      @click="$emit('input', mode.value)"
    >
      <v-icon size="16" :color="value === mode.value ? 'primary' : 'grey'">
        {{ mode.icon }}
      </v-icon>
      <span class="mode-label">{{ mode.label }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModeSelector',
  props: {
    value: {
      type: String,
      default: 'normal'
    }
  },
  data() {
    return {
      modes: [
        { label: '快速查询', value: 'quick', icon: 'mdi-lightning-bolt' },
        { label: '智能分析', value: 'normal', icon: 'mdi-brain' },
        { label: '威胁分析', value: 'threat', icon: 'mdi-shield-search' }
      ]
    }
  }
}
</script>

<style scoped>
.mode-selector {
  display: inline-flex;
  background: #F3F4F6;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.mode-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #6B7280;
  transition: all 0.2s;
  user-select: none;
}

.mode-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.mode-item.active {
  background: white;
  color: #2563EB;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.mode-label {
  line-height: 1;
}
</style>
