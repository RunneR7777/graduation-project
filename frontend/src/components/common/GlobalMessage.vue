<template>
  <v-snackbar
    v-model="visible"
    :color="color"
    :timeout="timeout"
    :location="location"
    multi-line
  >
    {{ text }}
    <template v-slot:actions>
      <v-btn
        variant="text"
        @click="visible = false"
      >
        关闭
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import message, { type MessageOptions } from '@/utils/message'

// 消息状态
const visible = ref(false)
const text = ref('')
const color = ref('info')
const timeout = ref(3000)
const location = ref<any>('top')

// 显示消息函数
const showMessage = (options: MessageOptions) => {
  text.value = options.text
  color.value = options.color || 'info'
  timeout.value = options.timeout || 3000
  visible.value = true
}

// 组件挂载时注册消息回调
onMounted(() => {
  message.setCallback(showMessage)
})
</script>

