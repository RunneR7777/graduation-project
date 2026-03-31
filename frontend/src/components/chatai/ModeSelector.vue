<template>
  <div class="mode-selector">
    <button
      v-for="mode in modes"
      :key="mode.value"
      class="mode-item"
      :class="{ active: modelValue === mode.value }"
      type="button"
      @click="emit('update:modelValue', mode.value)"
    >
      <v-icon :size="16" :color="modelValue === mode.value ? 'primary' : 'grey'">
        {{ mode.icon }}
      </v-icon>
      <span>{{ mode.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
type ModeValue = 'quick' | 'normal' | 'threat';

interface Props {
  modelValue: ModeValue;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (event: 'update:modelValue', value: ModeValue): void;
}>();

const modes: Array<{ label: string; value: ModeValue; icon: string }> = [
  { label: '快速查询', value: 'quick', icon: 'mdi-lightning-bolt' },
  { label: '智能分析', value: 'normal', icon: 'mdi-brain' },
  { label: '威胁分析', value: 'threat', icon: 'mdi-shield-search' },
];
</script>

<style scoped>
.mode-selector {
  display: inline-flex;
  background: #f3f4f6;
  border-radius: 999px;
  padding: 4px;
  gap: 4px;
}

.mode-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-item:hover {
  color: #374151;
}

.mode-item.active {
  background: white;
  color: #2563eb;
  box-shadow: 0 4px 20px rgba(37, 99, 235, 0.15);
}
</style>

