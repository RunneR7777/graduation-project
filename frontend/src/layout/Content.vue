<template>
    <div class="content-container">
        <v-container fluid class="content-wrapper">
            <v-row align="center" justify="center" class="mr-2 ml-2 mt-2">
                <v-col cols="12">
                    <v-card
                        min-height="650"
                        elevation="4"
                    >
                        <router-view/>
                    </v-card>
                </v-col>
            </v-row>
        </v-container>
    </div>
</template>

<script setup lang="ts">
// Vue 3 Composition API setup
</script>

<style scoped>
.content-container {
    flex: 1;
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
}

.content-wrapper {
    height: 100%;
    padding: 0;
}

/* 自定义滚动条样式 */
.content-container::-webkit-scrollbar {
    width: 8px;
}

.content-container::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.content-container::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
}

.content-container::-webkit-scrollbar-thumb:hover {
    background: #a8a8a8;
}
</style>

