<template>
    <div class="ml-4">
        <v-card-title>
            <v-list-item-action>
                <v-icon class="teal--text">mdi-ip-network</v-icon>
            </v-list-item-action>
            <v-list-item-content class="ml-n3">
                <v-list-item-title class="teal--text">
                    <span>IPv6 活动地址风险分析</span>
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

        <!-- 活跃地址列表 -->
        <v-row class="mr-8 ml-2 mt-4">
            <v-col cols="12">
                <v-card>
                    <v-card-title>
                        活跃 IPv6 地址列表
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
                    
                    <v-card-subtitle class="pb-0">
                        按活跃度排序的IPv6地址列表
                    </v-card-subtitle>

                    <v-data-table
                        :headers="headers"
                        :items="sortedAddresses"
                        :search="search"
                        :loading="loading"
                        :items-per-page="10"
                        :footer-props="{
                            'items-per-page-options': [10],
                            'items-per-page-text': '每页显示:',
                            'page-text': '{0}-{1} 共 {2}'
                        }"
                        show-expand
                        class="elevation-1"
                    >
                        <!-- 风险评分列 -->
                        <template v-slot:item.riskScore="{ item }">
                            <v-chip
                                :color="getRiskColor(item.riskScore)"
                                dark
                                small
                            >
                                {{ item.riskScore }}
                            </v-chip>
                        </template>

                        <!-- 地址类型列 -->
                        <template v-slot:item.addressType="{ item }">
                            <v-chip
                                :color="getAddressTypeColor(item.addressType)"
                                small
                                label
                            >
                                {{ item.addressType }}
                            </v-chip>
                        </template>

                        <!-- 地址列 -->
                        <template v-slot:item.address="{ item }">
                            <v-btn
                                text
                                color="primary"
                                @click="navigateToAddressAnalysis(item.address)"
                            >
                                {{ item.address }}
                            </v-btn>
                        </template>

                        <!-- 操作列 -->
                        <template v-slot:item.actions="{ item }">
                            <v-btn
                                small
                                color="primary"
                                text
                                @click="viewDeviceDetails(item)"
                            >
                                详情
                            </v-btn>
                            <v-btn
                                small
                                color="error"
                                text
                                @click="enablePrivacyExt(item)"
                                v-if="item.riskScore >= 80"
                            >
                                启用隐私
                            </v-btn>
                        </template>

                        <!-- 展开详情 -->
                        <template v-slot:expanded-item="{ headers, item }">
                            <td :colspan="headers.length">
                                <v-card flat>
                                    <v-card-text>
                                        <v-row>
                                            <v-col cols="6">
                                                <strong>地址历史:</strong>
                                                <div v-for="(addr, i) in item.history" :key="i">
                                                    {{ addr.address }} ({{ addr.time }})
                                                </div>
                                            </v-col>
                                            <v-col cols="6">
                                                <strong>风险详情:</strong>
                                                <div v-for="(risk, i) in item.riskDetails" :key="i">
                                                    {{ risk }}
                                                </div>
                                            </v-col>
                                        </v-row>
                                    </v-card-text>
                                </v-card>
                            </td>
                        </template>
                    </v-data-table>
                </v-card>
            </v-col>
        </v-row>

        <!-- 设备详情弹窗 -->
        <v-dialog v-model="dialog" max-width="800">
            <v-card>
                <v-card-title>
                    设备详情
                    <v-spacer></v-spacer>
                    <v-btn icon @click="dialog = false">
                        <v-icon>mdi-close</v-icon>
                    </v-btn>
                </v-card-title>
                <v-card-text v-if="selectedDevice">
                    <v-tabs v-model="activeTab">
                        <v-tab>基本信息</v-tab>
                        <v-tab>地址历史</v-tab>
                        <v-tab>风险评估</v-tab>
                    </v-tabs>
                    <v-tabs-items v-model="activeTab">
                        <v-tab-item>
                            <!-- 基本信息内容 -->
                        </v-tab-item>
                        <v-tab-item>
                            <!-- 地址历史内容 -->
                        </v-tab-item>
                        <v-tab-item>
                            <!-- 风险评估内容 -->
                        </v-tab-item>
                    </v-tabs-items>
                </v-card-text>
            </v-card>
        </v-dialog>
    </div>
</template>

<script>
export default {
    name: 'ActiveIPAnalysis',
    data: () => ({
        search: '',
        loading: false,
        dialog: false,
        activeTab: 0,
        selectedDevice: null,
        riskStats: [
            { title: '活跃IPv6地址', value: '128', color: 'primary' },
            { title: '高风险地址', value: '23', color: 'error' },
            { title: '静态地址占比', value: '45%', color: 'warning' },
            { title: '平均风险分', value: '62', color: 'info' }
        ],
        headers: [
            { text: 'IPv6地址', value: 'address', width: '300' },
            { text: '设备名称', value: 'deviceName', width: '150' },
            { text: '地址类型', value: 'addressType', width: '120' },
            { text: '风险评分', value: 'riskScore', width: '100' },
            { text: '最后活动', value: 'lastSeen', width: '150' },
            { text: '变更频率', value: 'changeFreq', width: '120' },
            { text: '操作', value: 'actions', sortable: false }
        ],
        ipv6Addresses: []
    }),
    computed: {
        sortedAddresses() {
            return this.ipv6Addresses
                .slice() // 创建浅拷贝
                .sort((a, b) => b.activeScore - a.activeScore);
        }
    },
    methods: {
        getRiskColor(score) {
            if (score >= 80) return 'red';
            if (score >= 60) return 'orange';
            return 'green';
        },
        getAddressTypeColor(type) {
            switch(type) {
                case 'EUI-64': return 'error';
                case 'SLAAC': return 'warning';
                case 'Privacy': return 'success';
                default: return 'grey';
            }
        },
        async fetchIPv6Data() {
            this.loading = true;
            try {
                // 获取统计数据
                const statsRes = await this.$api.network.getIPv6Stats();
                this.riskStats = [
                    { title: '活跃IPv6地址', value: statsRes.data.activeCount, color: 'primary' },
                    { title: '高风险地址', value: statsRes.data.highRiskCount, color: 'error' },
                    { title: '静态地址占比', value: statsRes.data.staticPercentage + '%', color: 'warning' },
                    { title: '平均风险分', value: statsRes.data.avgRiskScore, color: 'info' }
                ];

                // 获取地址列表
                const params = {
                    search: this.search,
                    page: this.page,
                    pageSize: this.itemsPerPage
                };
                const listRes = await this.$api.network.getIPv6List(params);
                this.ipv6Addresses = listRes.data.items;
                this.totalItems = listRes.data.total;
            } catch (error) {
                this.$message.error('获取IPv6数据失败');
                // 使用模拟数据作为降级方案
                this.ipv6Addresses = this.generateMockData();
            } finally {
                this.loading = false;
            }
        },
        async viewDeviceDetails(item) {
            try {
                const res = await this.$api.network.getIPv6Detail(item.address);
                this.selectedDevice = res.data;
                this.dialog = true;
            } catch (error) {
                this.$message.error('获取设备详情失败');
            }
        },
        async enablePrivacyExt(item) {
            try {
                await this.$api.network.enableIPv6Privacy({
                    address: item.address,
                    deviceName: item.deviceName
                });
                this.$message.success(`已为设备 ${item.deviceName} 启用IPv6隐私扩展`);
                this.fetchIPv6Data(); // 刷新数据
            } catch (error) {
                this.$message.error('启用隐私扩展失败');
            }
        },
        generateMockData() {
            const mockData = [];
            const deviceTypes = ['工作站', '服务器', '打印机', '摄像头', '路由器'];
            const addressTypes = ['EUI-64', 'SLAAC', 'Privacy'];
            
            for (let i = 1; i <= 50; i++) {
                const activeScore = 100 - Math.floor(Math.random() * 50); // 50-100之间的随机数
                const deviceType = deviceTypes[Math.floor(Math.random() * deviceTypes.length)];
                const addressType = addressTypes[Math.floor(Math.random() * addressTypes.length)];
                const riskScore = Math.floor(Math.random() * 40) + 40; // 40-80之间的随机数
                
                mockData.push({
                    address: `2001:db8:85a3:8d3:${i.toString(16).padStart(4, '0')}:8a2e:370:${(7348 + i).toString(16)}`,
                    deviceName: `${deviceType}-${String.fromCharCode(65 + (i % 26))}`,
                    addressType: addressType,
                    riskScore: riskScore,
                    lastSeen: `${Math.floor(Math.random() * 60)}分钟前`,
                    changeFreq: addressType === 'Privacy' ? '动态' : '静态',
                    activeScore: activeScore,
                    history: [
                        { 
                            address: `2001:db8:85a3:8d3:${i.toString(16).padStart(4, '0')}:8a2e:370:${(7348 + i).toString(16)}`,
                            time: '2024-03-01'
                        }
                    ],
                    riskDetails: this.generateRiskDetails(addressType, riskScore)
                });
            }
            return mockData;
        },
        generateRiskDetails(addressType, riskScore) {
            const details = [];
            if (addressType === 'EUI-64') {
                details.push('使用EUI-64方式生成地址，可能暴露MAC地址');
            }
            if (riskScore >= 70) {
                details.push('长期使用静态地址增加追踪风险');
            }
            if (addressType === 'SLAAC') {
                details.push('SLAAC地址可能泄露网络信息');
            }
            return details;
        },
        navigateToAddressAnalysis(address) {
            this.$router.push(`/ipv6/address/${address}`);
        }
    },
    created() {
        // 在组件创建时生成模拟数据
        this.ipv6Addresses = this.generateMockData();
    }
};
</script>

<style scoped>
.v-data-table {
    background: white !important;
}
</style> 