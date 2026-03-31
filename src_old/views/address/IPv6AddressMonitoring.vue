<template>
  <div class="ml-4">
    <v-card-title>
      <v-list-item-action>
        <v-icon class="teal--text">mdi-ip</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="teal--text">
          <span>IPv6地址监控</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-row class="mr-8 ml-2">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            监控中的IPv6地址
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
            :items="monitoredAddresses"
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
                @click="navigateToAddressAnalysis(item.address)"
              >
                详情
              </v-btn>
              <v-btn
                small
                color="error"
                text
                @click="stopMonitoring(item)"
              >
                停止监控
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
  name: 'IPv6AddressMonitoring',
  data: () => ({
    search: '',
    loading: false,
    headers: [
      { text: 'IPv6地址', value: 'address', width: '300' },
      { text: '设备名称', value: 'deviceName', width: '150' },
      { text: '状态', value: 'status', width: '120' },
      { text: '上次检查', value: 'lastCheck', width: '150' },
      { text: '监控启动时间', value: 'startTime', width: '150' },
      { text: '操作', value: 'actions', sortable: false }
    ],
    monitoredAddresses: []
  }),
  created() {
    this.fetchMonitoredAddresses();
  },
  methods: {
    fetchMonitoredAddresses() {
      this.loading = true;
      // 模拟获取数据
      setTimeout(() => {
        this.monitoredAddresses = this.generateMockMonitoringData();
        this.loading = false;
      }, 1000);
    },
    navigateToAddressAnalysis(address) {
      try {
        // 修改为跳转到 active-detection 路径
        this.$router.push({
          path: '/address/active-detection',
          query: { address: address }
        }).catch(err => {
          if (err.name !== 'NavigationDuplicated') {
            console.error('导航错误:', err);
            this.$message.error('页面导航失败');
          }
        });
      } catch (error) {
        console.error('导航方法错误:', error);
        this.$message.error('页面导航失败');
      }
    },
    stopMonitoring(item) {
      this.$message.success(`已停止监控 ${item.address}`);
      // 从列表中移除项目
      this.monitoredAddresses = this.monitoredAddresses.filter(
        address => address.address !== item.address
      );
    },
    generateMockMonitoringData() {
      const statuses = ['活跃', '闲置', '可疑活动'];
      const deviceTypes = ['工作站', '服务器', '打印机', '摄像头', '路由器'];
      
      return Array.from({ length: 15 }, (_, i) => {
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        const deviceType = deviceTypes[Math.floor(Math.random() * deviceTypes.length)];
        
        return {
          address: `2001:db8:85a3:8d3:${i.toString(16).padStart(4, '0')}:8a2e:370:${(7348 + i).toString(16)}`,
          deviceName: `${deviceType}-${String.fromCharCode(65 + (i % 26))}`,
          status: status,
          lastCheck: new Date(Date.now() - Math.floor(Math.random() * 86400000)).toLocaleString(),
          startTime: new Date(Date.now() - Math.floor(Math.random() * 604800000)).toLocaleString()
        };
      });
    }
  }
}
</script>

<style scoped>
.v-data-table {
  background: white !important;
}
</style>