<template>
    <div class="sidebar-container">
        <div class="sidebar-drawer">
            <v-list density="compact" class="sidebar-list py-2">
            <template v-for="(item, i) in items" :key="i">
                <v-row v-if="item.header" align="center" class="px-3 mt-2 mb-1">
                    <v-col cols="12">
                        <v-list-subheader class="text-caption font-weight-bold text-grey-darken-2 px-2">
                            {{ item.text }}
                        </v-list-subheader>
                    </v-col>
                </v-row>

                <v-list-group
                    v-else-if="item.group"
                    :value="item.text"
                    class="sidebar-group"
                >
                    <template v-slot:activator="{ props }">
                        <v-list-item 
                            v-bind="props"
                            class="sidebar-group-item"
                            rounded="lg"
                        >
                            <template v-slot:prepend>
                                <v-icon size="20" class="mr-1 text-teal">{{ item.icon }}</v-icon>
                            </template>
                            <v-list-item-title class="font-weight-bold text-body-2 text-teal">{{item.text}}</v-list-item-title>
                        </v-list-item>
                    </template>

                    <v-list-item
                        v-for="(subItem, subIndex) in item.items"
                        :key="subIndex"
                        @click="goToPath(subItem.path!)"
                        :class="{ 'sidebar-item-active': isPath(subItem.path) }"
                        class="sidebar-sub-item ml-4"
                        rounded="lg"
                    >
                        <v-list-item-title class="text-body-2">
                            <span :class="isPath(subItem.path) ? 'text-teal font-weight-bold' : 'text-grey-darken-1'">{{ subItem.text }}</span>
                        </v-list-item-title>
                    </v-list-item>
                </v-list-group>

                <v-list-item 
                    v-else-if="item.dc" 
                    link 
                    @click="goToPath(item.path!)" 
                    :class="{ 'sidebar-item-active': isPath(item.path) }"
                    class="sidebar-main-item"
                    rounded="lg"
                >
                    <template v-slot:prepend>
                        <v-icon 
                            size="20" 
                            class="mr-1"
                            :class="isPath(item.path) ? 'text-teal' : 'text-grey-darken-1'"
                        >{{ item.icon }}</v-icon>
                    </template>
                    <v-list-item-title class="text-body-2">
                        <span :class="isPath(item.path) ? 'text-teal font-weight-bold' : 'text-grey-darken-1'">{{ item.text }}</span>
                    </v-list-item-title>
                </v-list-item>

                <v-divider v-if="item.divider" :key="'divider-'+i" class="my-2 mx-3"/>
            </template>
        </v-list>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import sidebarItems from '@/utils/sidebar'
import type { SidebarItem } from '@/types/sidebar'

const router = useRouter()
const route = useRoute()

const items = ref<SidebarItem[]>(sidebarItems())

const currentPath = computed(() => route.path)

const isPath = (path: string | undefined) => {
    if (path === undefined) {
        return false
    }
    return path === currentPath.value
}

const goToPath = (path: string) => {
    router.push(path)
}
</script>

<style scoped>
.sidebar-container {
    flex-shrink: 0;
    height: 100%;
    width: 260px;
}

.sidebar-drawer {
    border-right: 1px solid rgba(0, 0, 0, 0.05);
    height: 100%;
    width: 100%;
    background-color: #fafafa;
    overflow-y: auto;
    overflow-x: hidden;
}

.sidebar-list {
    padding-left: 8px;
    padding-right: 8px;
    overflow-x: hidden;

}

.sidebar-group-item {
    margin-bottom: 2px;
    margin-top: 4px;
    background: linear-gradient(to right, rgba(0, 150, 136, 0.05) 0%, rgba(0, 150, 136, 0.02) 100%) !important;
    border-left: 3px solid transparent;
    transition: all 0.3s ease;
}

.sidebar-group-item:hover {
    background: linear-gradient(to right, rgba(0, 150, 136, 0.12) 0%, rgba(0, 150, 136, 0.06) 100%) !important;
    border-left-color: #00897B;
}

.sidebar-main-item {
    margin-bottom: 2px;
    transition: all 0.3s ease;
}

.sidebar-main-item:hover {
    background-color: rgba(0, 150, 136, 0.08) !important;
}

.sidebar-sub-item {
    margin-bottom: 2px;
    min-height: 36px !important;
    transition: all 0.3s ease;
}

.sidebar-sub-item:hover {
    background-color: rgba(0, 150, 136, 0.08) !important;
}

.sidebar-item-active {
    background-color: rgba(0, 150, 136, 0.12) !important;
    border-left: 3px solid #009688;
}

.sidebar-item-active:hover {
    background-color: rgba(0, 150, 136, 0.15) !important;
}

.font-weight-bold {
    font-weight: bold !important;
}

.text-teal {
    color: #009688 !important;
}

/* 平滑的图标和文字过渡 */
:deep(.v-icon) {
    transition: all 0.3s ease;
}

:deep(.v-list-item-title) {
    transition: all 0.3s ease;
}

/* 分组标题样式 */
:deep(.v-list-group__items) {
    background-color: transparent !important;
}

/* 子项缩进 */
:deep(.v-list-group__items .v-list-item) {
    padding-left: 16px !important;
}
</style>

