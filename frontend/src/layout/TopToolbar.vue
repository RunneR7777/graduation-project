<template>
    <v-app-bar class="white" app elevation="2" height="70">
        <div class="d-flex align-center logo-container" @click="goToPath('/')" style="cursor: pointer;">
            <v-avatar tile size="55" class="ml-4 mr-3">
                <img src="@/assets/images/fuxi_v3.svg" alt="logo"/>
            </v-avatar>
            <span class="text-h6 grey--text text--darken-2 font-weight-bold system-title">6Guard-园区网络IPv6安全风险评估系统</span>
        </div>
        <v-spacer />
        <div>
            <div >
                <v-menu left offset-y>
                    <template v-slot:activator="{ props }">
                        <span v-bind="props" :class="'mr-4 ml-12 flag-icon flag-icon-' + language"/>
                    </template>

                    <v-list>
                        <v-list-item @click="language = 'us'">
                            <template v-slot:prepend>
                                <span class="mr-4 ml-4 flag-icon flag-icon-us"/>
                            </template>
                            <v-list-item-title class="mr-3 grey--text">English</v-list-item-title>
                        </v-list-item>
                    </v-list>
                    <v-divider/>
                    <v-list>
                        <v-list-item @click="language = 'cn'">
                            <template v-slot:prepend>
                                <span class="mr-4 ml-4 flag-icon flag-icon-cn"/>
                            </template>
                            <v-list-item-title class="mr-3 grey--text">Unfinished</v-list-item-title>
                        </v-list-item>
                    </v-list>
                </v-menu>

                <v-menu>
                    <template v-slot:activator="{ props }">
                        <v-btn icon class="mr-1" v-bind="props">
                            <v-icon>mdi-cog-transfer-outline</v-icon>
                        </v-btn>
                    </template>
                    <v-list>
                        <v-list-item>
                            <template v-slot:prepend>
                                <v-icon>mdi-account-box</v-icon>
                            </template>
                            <v-list-item-title>
                                <span>{{username}}</span>
                            </v-list-item-title>
                        </v-list-item>

                        <v-divider class="mb-3"/>

                        <v-list-item @click="goToPath('/settings')">
                            <template v-slot:prepend>
                                <v-icon>mdi-cog-outline</v-icon>
                            </template>
                            <v-list-item-title>
                                <span>设置</span>
                            </v-list-item-title>
                        </v-list-item>

                        <v-list-item>
                            <template v-slot:prepend>
                                <v-icon>mdi-book-search</v-icon>
                            </template>
                            <v-list-item-title>
                                <a
                                    class="black--text"
                                    href="https://github.com/jeffzh3ng/fuxi#issues"
                                    target="_blank">
                                    帮助与文档
                                </a>
                            </v-list-item-title>
                        </v-list-item>

                        <v-divider class="mt-1"/>

                        <v-list-item class="mt-2" @click="logout">
                            <template v-slot:prepend>
                                <v-icon color="error">mdi-logout</v-icon>
                            </template>
                            <v-list-item-title>
                                <span class="error--text">退出登录</span>
                            </v-list-item-title>
                        </v-list-item>
                    </v-list>
                </v-menu>
            </div>
        </div>

    </v-app-bar>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const username = ref("Administrator")
const language = ref("us")

const goToPath = (path: string) => {
    router.push(path)
}

const logout = () => {
    window.localStorage.removeItem('access_token')
    // TODO: 添加消息提示
    // this.$message.success("Logout successfully")
    router.push('/login')
}
</script>

<style scoped>
a:link { 
    text-decoration: none;
}

.logo-container {
    transition: all 0.3s ease;
}

.logo-container:hover {
    opacity: 0.8;
}

.system-title {
    letter-spacing: 0.5px;
    transition: color 0.3s ease;
}

.logo-container:hover .system-title {
    color: #009688 !important;
}
</style>

