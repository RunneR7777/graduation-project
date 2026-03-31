<template>
  <v-app id="chatai-app">
    <router-view />
  </v-app>
</template>

<script>
export default {
  name: 'ChatAILayout',
  data() {
    return {}
  }
}
</script>

<style>
#chatai-app {
  height: 100vh;
  overflow: hidden;
  background-color: #ffffff !important;
}

#chatai-app .v-application--wrap {
  min-height: 100vh;
}

/* 全局滚动条样式优化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #E5E7EB;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #D1D5DB;
}
</style>
