<template>
  <div class="ml-4">
    <v-card-title>
      <v-list-item-action>
        <v-icon class="teal--text">mdi-arrow-down-bold-circle</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="teal--text">
          <span>进站流量</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-row class="mr-8 ml-2">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            进站流量列表
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
            :items="trafficData"
            :search="search"
            :loading="loading"
            :items-per-page="10"
            :footer-props="{
              'items-per-page-options': [10, 20, 50],
              'items-per-page-text': '每页显示:',
              'page-text': '{0}-{1} 共 {2}'
            }"
            class="elevation-1"
          >
            <!-- 源IP列 -->
            <template v-slot:item.sourceIP="{ item }">
              <v-chip
                small
                :color="getIPColor(item.sourceIP)"
                text-color="white"
              >
                {{ item.sourceIP }}
              </v-chip>
            </template>

            <!-- 目标IP列 -->
            <template v-slot:item.destIP="{ item }">
              <v-chip
                small
                :color="getIPColor(item.destIP)"
                text-color="white"
              >
                {{ item.destIP }}
              </v-chip>
            </template>

            <!-- 协议列 -->
            <template v-slot:item.protocol="{ item }">
              <v-chip
                small
                :color="getProtocolColor(item.protocol)"
                text-color="white"
              >
                {{ item.protocol }}
              </v-chip>
            </template>

            <!-- 风险等级列 -->
            <template v-slot:item.riskLevel="{ item }">
              <v-chip
                small
                :color="getRiskColor(item.riskLevel)"
                text-color="white"
              >
                {{ item.riskLevel }}
              </v-chip>
            </template>

            <!-- 操作列 -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                small
                color="primary"
                text
                @click="viewFlowDetail(item)"
              >
                详情
              </v-btn>
              <v-btn
                small
                color="error"
                text
                @click="blockFlow(item)"
              >
                阻断
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
export default {
  name: 'InboundTraffic',
  data: () => ({
    search: '',
    loading: false,
    headers: [
      { text: '源IP', value: 'sourceIP', width: '200' },
      { text: '目标IP', value: 'destIP', width: '200' },
      { text: '协议', value: 'protocol', width: '100' },
      { text: '端口', value: 'port', width: '80' },
      { text: '流量大小', value: 'size', width: '100' },
      { text: '时间', value: 'timestamp', width: '150' },
      { text: '风险等级', value: 'riskLevel', width: '100' },
      { text: '操作', value: 'actions', sortable: false }
    ],
    trafficData: [],
    totalItems: 0
  }),
  created() {
    this.fetchTrafficData();
  },
  methods: {
    fetchTrafficData() {
      this.loading = true;
      this.$api.network.getInboundTraffic({
        page: 1,
        pageSize: 10,
        search: this.search
      }).then(res => {
        if (res && res.data) {
          let response = res.data;
          let status = response['status'];
          let result = response['data'];
          if (status && status['code'] === 200) {
            this.trafficData = result.items || [];
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
    getIPColor(ip) {
      if (ip.startsWith('2001:da8')) {
        return 'teal';
      } else {
        return 'blue-grey';
      }
    },
    getProtocolColor(protocol) {
      const colorMap = {
        'HTTP': 'blue',
        'HTTPS': 'green',
        'DNS': 'purple',
        'ICMP': 'orange',
        'SSH': 'deep-purple',
        'FTP': 'indigo',
        'SMTP': 'cyan',
        'TCP': 'blue',
        'UDP': 'green'
      };
      
      return colorMap[protocol] || 'grey';
    },
    getRiskColor(risk) {
      const colorMap = {
        '低': 'blue',
        '中': 'orange',
        '高': 'red',
        '安全': 'green'
      };
      
      return colorMap[risk] || 'grey';
    },
    viewFlowDetail(item) {
      this.$router.push({
        path: `/network/traffic/flow/${item.id}`
      });
    },
    blockFlow(item) {
      this.$message.success(`已阻断从 ${item.sourceIP} 到 ${item.destIP} 的流量`);
    }
  },
  watch: {
    search: {
      handler() {
        this.fetchTrafficData();
      }
    }
  }
}
</script>

<style scoped>
.v-data-table {
  background: white !important;
}
</style> 