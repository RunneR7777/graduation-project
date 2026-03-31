<template>
    <v-app id="keep">
        <TopToolbar/>
        <div class="layout-container">
            <SideBar/>
            <Content/>
        </div>
    </v-app>
</template>

<script setup lang="ts">
import TopToolbar from './TopToolbar.vue'
import SideBar from './SideBar.vue'
import Content from './Content.vue'
</script>

<style>
    #keep .v-navigation-drawer__border {
        display: none
    }
    
    .layout-container {
        display: flex;
        height: calc(100vh - 70px); /* 减去顶部工具栏高度 */
        margin-top: 70px; /* 为顶部工具栏留出空间 */
        overflow: hidden;
    }
</style>

