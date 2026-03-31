<template>
  <v-app>
    <router-view/>
    <!-- 全局消息提示组件 -->
    <GlobalMessage />
  </v-app>
</template>

<script setup lang="ts">
import GlobalMessage from '@/components/common/GlobalMessage.vue'
</script>

