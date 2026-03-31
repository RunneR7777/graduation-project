<template>
    <div class="ml-4">
        <v-card-title>
            <v-list-item-action>
                <v-icon class="teal--text">mdi-chart-timeline-variant</v-icon>
            </v-list-item-action>
            <v-list-item-content class="ml-n3">
                <v-list-item-title class="teal--text">
                    <span>网络流量分析</span>
                </v-list-item-title>
            </v-list-item-content>
        </v-card-title>

        <!-- 筛选器 -->
        <v-row class="mr-8 ml-2">
            <v-col cols="12">
                <v-card>
                    <v-card-text>
                        <v-row>
                            <v-col cols="3">
                                <v-text-field
                                    v-model="filters.host"
                                    label="主机"
                                    dense
                                    outlined
                                    clearable
                                ></v-text-field>
                            </v-col>
                            <v-col cols="2">
                                <v-select
                                    v-model="filters.protocol"
                                    :items="protocolOptions"
                                    label="协议"
                                    dense
                                    outlined
                                    clearable
                                ></v-select>
                            </v-col>
                            <v-col cols="2">
                                <v-select
                                    v-model="filters.state"
                                    :items="stateOptions"
                                    label="TCP状态"
                                    dense
                                    outlined
                                    clearable
                                ></v-select>
                            </v-col>
                            <v-col cols="3">
                                <v-select
                                    v-model="filters.type"
                                    :items="trafficTypes"
                                    label="流量类型"
                                    dense
                                    outlined
                                    clearable
                                ></v-select>
                            </v-col>
                            <v-col cols="2">
                                <v-btn 
                                    color="primary" 
                                    @click="resetFilters"
                                    block
                                >
                                    重置
                                </v-btn>
                            </v-col>
                        </v-row>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <!-- 流量列表 -->
        <v-row class="mr-8 ml-2 mt-4">
            <v-col cols="12">
                <v-data-table
                    :headers="headers"
                    :items="items"
                    :loading="loading"
                    :items-per-page="pageSize"
                    :page.sync="pageCurrent"
                    :server-items-length="totalItems"
                    :sort-by.sync="sortBy"
                    :sort-desc.sync="sortDesc"
                    :footer-props="{
                        'items-per-page-options': [5, 10, 15, 20],
                        'items-per-page-text': '每页显示'
                    }"
                    @update:items-per-page="pageSize = $event"
                    @update:page="pageCurrent = $event"
                    @update:sort-by="sortBy = $event"
                    @update:sort-desc="sortDesc = $event"
                    class="elevation-1"
                >
                    <template v-slot:item.actions="{ item }">
                        <v-tooltip bottom>
                            <template v-slot:activator="{ on }">
                                <v-btn 
                                    icon 
                                    small 
                                    color="primary" 
                                    v-on="on"
                                    @click="showDetails(item)"
                                >
                                    <v-icon small>mdi-information-outline</v-icon>
                                </v-btn>
                            </template>
                            <span>查看流量详情</span>
                        </v-tooltip>
                    </template>

                    <template v-slot:item.lastSeen="{ item }">
                        {{ formatTime(item.lastSeen) }}
                    </template>

                    <template v-slot:item.score="{ item }">
                        <v-chip
                            :color="getScoreColor(item.score)"
                            dark
                            small
                        >
                            {{ item.score }}
                        </v-chip>
                    </template>

                    <template v-slot:item.flow="{ item }">
                        <div class="d-flex align-center">
                            <span class="mr-2">{{ item.flow.source }}</span>
                            <v-icon small>mdi-arrow-right</v-icon>
                            <span class="ml-2">{{ item.flow.destination }}</span>
                        </div>
                    </template>
                </v-data-table>
            </v-col>
        </v-row>

        <!-- 详情展示 -->
        <v-row class="mr-8 ml-2 mt-4" v-if="selectedItem">
            <v-col cols="12">
                <v-card>
                    <v-card-title>
                        <v-list-item-action>
                            <v-icon class="teal--text">mdi-information</v-icon>
                        </v-list-item-action>
                        <v-list-item-content class="ml-n3">
                            <v-list-item-title class="teal--text">
                                <span>流量详情</span>
                            </v-list-item-title>
                        </v-list-item-content>
                    </v-card-title>
                    <v-card-text>
                        <v-row>
                            <v-col cols="12">
                                <v-simple-table>
                                    <template v-slot:default>
                                        <tbody>
                                            <tr v-for="(value, key) in selectedItem" :key="key">
                                                <td class="text-right" style="width: 150px">{{ formatKey(key) }}</td>
                                                <td>{{ formatValue(value) }}</td>
                                            </tr>
                                        </tbody>
                                    </template>
                                </v-simple-table>
                            </v-col>
                        </v-row>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>
    </div>
</template>

<script>
export default {
    name: "NetworkTraffic",
    data: () => ({
        loading: false,
        selectedItem: null,
        filters: {
            host: '',
            protocol: null,
            state: null,
            type: null
        },
        sortBy: 'lastSeen',
        sortDesc: true,
        protocolOptions: [
            'TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS'
        ],
        stateOptions: [
            'ESTABLISHED', 'TIME_WAIT', 'CLOSE_WAIT', 'FIN_WAIT'
        ],
        trafficTypes: [
            '正常流量', 'P2P流量', '加密流量', '异常流量'
        ],
        headers: [
            { text: '操作', value: 'actions', sortable: false, width: '80' },
            { text: '最近活动', value: 'lastSeen', width: '120' },
            { text: '持续时间', value: 'duration', width: '120' },
            { text: '协议', value: 'protocol', width: '150' },
            { text: '分数', value: 'score', width: '100' },
            { text: '流量信息', value: 'flow', sortable: false },
            { text: '实时吞吐量', value: 'throughput', width: '120' },
            { text: '总流量', value: 'totalBytes', width: '120' }
        ],
        items: [],
        pageCurrent: 1,
        pageSize: 10,
        totalItems: 0
    }),
    methods: {
        resetFilters() {
            this.filters = {
                host: '',
                protocol: null,
                state: null,
                type: null
            };
            this.getData();
        },
        getData() {
            this.loading = true;
            console.log('API路径:', process.env.VUE_APP_BASE_API);
            this.$api.network.getTrafficList({
                ...this.filters,
                page: this.pageCurrent,
                pageSize: this.pageSize,
                sortBy: this.sortBy,
                sortDesc: this.sortDesc
            }).then(res => {
                console.log('API响应:', res);
                if (res && res.data) {
                    let response = res.data;
                    let status = response['status'];
                    let result = response['data'];
                    if (status && status['code'] === 200) {
                        this.items = result.items || [];
                        this.totalItems = result.total || 0;
                    } else {
                        this.$message.error(status ? status['message'] : '未知错误');
                    }
                } else {
                    this.$message.error('响应数据格式错误');
                }
            }).catch(error => {
                console.error('API错误:', error);
                if (error && error.response && error.response.data) {
                    this.$message.error(error.response.data.message || '获取数据失败');
                } else {
                    this.$message.error('网络连接失败，请检查后端服务是否运行');
                }
            }).finally(() => {
                this.loading = false;
            });
        },
        showDetails(item) {
            this.selectedItem = item;
        },
        formatTime(time) {
            if (!time) return '未知';
            const now = new Date();
            const lastSeen = new Date(time);
            const diffSeconds = Math.floor((now - lastSeen) / 1000);

            if (diffSeconds < 60) {
                return '< 1分钟';
            } else if (diffSeconds < 3600) {
                const minutes = Math.floor(diffSeconds / 60);
                return `${minutes}分钟前`;
            } else if (diffSeconds < 86400) {
                const hours = Math.floor(diffSeconds / 3600);
                return `${hours}小时前`;
            } else {
                const days = Math.floor(diffSeconds / 86400);
                return `${days}天前`;
            }
        },
        getScoreColor(score) {
            if (score >= 80) return 'red';
            if (score >= 60) return 'orange';
            return 'green';
        },
        formatKey(key) {
            const keyMap = {
                'lastSeen': '最近活动',
                'duration': '持续时间',
                'protocol': '协议',
                'score': '分数',
                'flow': '流量信息',
                'throughput': '实时吞吐量',
                'totalBytes': '总流量'
            };
            return keyMap[key] || key;
        },
        formatValue(value) {
            if (value === null || value === undefined) return '-';
            if (typeof value === 'object') {
                if (value.source && value.destination) {
                    return `${value.source} → ${value.destination}`;
                }
                return JSON.stringify(value, null, 2);
            }
            return value;
        }
    },
    watch: {
        filters: {
            handler() {
                this.pageCurrent = 1;
                this.getData();
            },
            deep: true
        },
        pageCurrent() {
            this.getData();
        },
        pageSize() {
            this.pageCurrent = 1;
            this.getData();
        },
        sortBy() {
            this.pageCurrent = 1;
            this.getData();
        },
        sortDesc() {
            this.pageCurrent = 1;
            this.getData();
        }
    },
    mounted() {
        this.getData();
    }
};
</script>

<style scoped>
.v-data-table {
    background: white !important;
}
</style> 