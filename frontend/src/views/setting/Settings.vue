<template>
  <div class="pa-4">
    <v-card-title>
      <v-icon class="teal--text mr-2">mdi-cog-outline</v-icon>
      <span class="teal--text">设置</span>
    </v-card-title>
    
    <v-card>
      <v-card-text>
        <v-tabs v-model="tab">
          <v-tab value="account">账户设置</v-tab>
          <v-tab value="system">系统设置</v-tab>
          <v-tab value="tools">工具设置</v-tab>
        </v-tabs>
        
        <v-window v-model="tab">
          <v-window-item value="account">
            <div class="pa-4">
              <p>账户设置 - 正在开发中...</p>
            </div>
          </v-window-item>
          <v-window-item value="system">
            <div class="pa-4">
              <p>系统设置 - 正在开发中...</p>
            </div>
          </v-window-item>
          <v-window-item value="tools">
            <div class="pa-4">
              <p>工具设置 - 正在开发中...</p>
            </div>
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const tab = ref('account')
</script>

