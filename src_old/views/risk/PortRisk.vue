<template>
    <div class="ml-4">
        <!-- 页面标题 -->
        <v-card-title>
            <v-list-item-action>
                <v-icon class="teal--text">mdi-lan-connect</v-icon>
            </v-list-item-action>
            <v-list-item-content class="ml-n3">
                <v-list-item-title class="teal--text">
                    <span>高危端口分析</span>
                </v-list-item-title>
            </v-list-item-content>
        </v-card-title>

        <!-- 风险概览卡片 -->
        <v-row class="mr-8 ml-2">
            <v-col cols="3" v-for="(stat, index) in riskStats" :key="index">
                <v-card :color="stat.color" dark>
                    <v-card-text>
                        <div class="text-h4">{{ stat.value }}</div>
                        <div>{{ stat.title }}</div>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <!-- 高危端口列表 -->
        <v-row class="mr-8 ml-2 mt-4">
            <v-col cols="12">
                <v-card>
                    <v-card-title>
                        高危端口列表
                        <v-spacer></v-spacer>
                        <v-text-field
                            v-model="search"
                            append-icon="mdi-magnify"
                            label="搜索"
                            single-line
                            hide-details
                            dense
                            outlined
                        ></v-text-field>
                    </v-card-title>

                    <v-data-table
                        :headers="headers"
                        :items="portData"
                        :search="search"
                        :loading="loading"
                        :items-per-page="10"
                        class="elevation-1"
                    >
                        <template v-slot:item.risk="{ item }">
                            <v-chip
                                :color="getRiskColor(item.risk)"
                                dark
                                small
                            >
                                {{ item.risk }}
                            </v-chip>
                        </template>

                        <template v-slot:item.actions="{ item }">
                            <v-btn
                                small
                                color="primary"
                                text
                                @click="viewDetails(item)"
                            >
                                详情
                            </v-btn>
                        </template>
                    </v-data-table>
                </v-card>
            </v-col>
        </v-row>

        <!-- 详情弹窗 -->
        <v-dialog v-model="dialog" max-width="800">
            <v-card>
                <v-card-title>
                    端口详情
                    <v-spacer></v-spacer>
                    <v-btn icon @click="dialog = false">
                        <v-icon>mdi-close</v-icon>
                    </v-btn>
                </v-card-title>
                <v-card-text v-if="selectedPort">
                    <v-row>
                        <v-col cols="6">
                            <strong>端口号：</strong> {{ selectedPort.port }}
                        </v-col>
                        <v-col cols="6">
                            <strong>服务：</strong> {{ selectedPort.service }}
                        </v-col>
                        <v-col cols="6">
                            <strong>风险等级：</strong>
                            <v-chip :color="getRiskColor(selectedPort.risk)" dark small>
                                {{ selectedPort.risk }}
                            </v-chip>
                        </v-col>
                        <v-col cols="12">
                            <strong>风险描述：</strong>
                            <div class="mt-2">{{ selectedPort.description }}</div>
                        </v-col>
                        <v-col cols="12">
                            <strong>建议措施：</strong>
                            <div class="mt-2">{{ selectedPort.suggestion }}</div>
                        </v-col>
                    </v-row>
                </v-card-text>
            </v-card>
        </v-dialog>
    </div>
</template>

<script>
export default {
    name: 'PortRisk',
    data: () => ({
        loading: false,
        search: '',
        dialog: false,
        selectedPort: null,
        headers: [
            { text: '端口', value: 'port', width: '100' },
            { text: '服务', value: 'service', width: '150' },
            { text: '风险等级', value: 'risk', width: '100' },
            { text: '描述', value: 'description' },
            { text: '操作', value: 'actions', sortable: false, width: '100' }
        ],
        riskStats: [
            { title: '开放端口总数', value: 1205, color: 'primary' },
            { title: '高危端口数', value: 238, color: 'error' },
            { title: '异常服务数', value: 45, color: 'warning' },
            { title: '未知服务数', value: 156, color: 'info' }
        ],
        portData: []
    }),
    methods: {
        getRiskColor(risk) {
            if (risk >= 80) return 'red';
            if (risk >= 60) return 'orange';
            return 'green';
        },
        async fetchPortData() {
            this.loading = true;
            try {
                const res = await this.$api.network.getPortRiskList();
                this.portData = res.data;
            } catch (error) {
                this.$message.error('获取端口数据失败');
                // 使用模拟数据
                this.portData = this.getMockData();
            } finally {
                this.loading = false;
            }
        },
        viewDetails(item) {
            this.selectedPort = item;
            this.dialog = true;
        },
        getMockData() {
            return [
                {
                    port: 22,
                    service: 'SSH',
                    risk: 85,
                    description: 'SSH服务可能存在弱密码或未及时更新的漏洞',
                    suggestion: '建议更改默认端口，限制IP访问，加强密码策略'
                },
                {
                    port: 3389,
                    service: 'RDP',
                    risk: 80,
                    description: 'Windows远程桌面服务暴露在公网',
                    suggestion: '建议使用VPN访问，限制IP白名单'
                }
                // 添加更多模拟数据...
            ];
        }
    },
    mounted() {
        this.fetchPortData();
    }
};
</script> 