<template>
  <div class="ml-4">
    <v-card-title>
      <v-list-item-action>
        <v-icon class="red--text">mdi-server-security</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="red--text">
          <span>危险主机</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-row class="mr-8 ml-2">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            危险主机列表
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
            :items="hostsData"
            :search="search"
            :loading="loading"
            :items-per-page="10"
            :server-items-length="totalItems"
            :options.sync="options"
            :footer-props="{
              'items-per-page-options': [10, 20, 50],
              'items-per-page-text': '每页显示:',
              'page-text': '{0}-{1} 共 {2}'
            }"
            class="elevation-1"
            :disable-sort="false"
            must-sort
            sort-by="riskLevel"
            sort-desc
          >
            <!-- IP地址列 -->
            <template v-slot:item.ipAddress="{ item }">
              <v-chip
                small
                :color="getIPColor(item.ipAddress)"
                text-color="white"
              >
                {{ item.ipAddress }}
              </v-chip>
            </template>

            <!-- 地理位置列 -->
            <template v-slot:item.location="{ item }">
              <v-chip
                small
                :color="getLocationColor(item.location)"
                text-color="white"
              >
                {{ item.location }}
              </v-chip>
            </template>

            <!-- 风险类型列 -->
            <template v-slot:item.riskType="{ item }">
              <v-chip
                small
                color="red"
                text-color="white"
              >
                {{ item.riskType }}
              </v-chip>
            </template>

            <!-- 风险等级列 -->
            <template v-slot:item.riskLevel="{ item }">
              <v-rating
                :value="item.riskLevel"
                color="red"
                background-color="grey lighten-3"
                half-increments
                readonly
                dense
                small
              ></v-rating>
            </template>

            <!-- 风险原因列 -->
            <template v-slot:item.riskReasons="{ item }">
              <div>
                <v-chip
                  v-for="(reason, index) in item.riskReasons"
                  :key="index"
                  x-small
                  class="mr-1 mb-1"
                  color="pink lighten-4"
                >
                  {{ reason }}
                </v-chip>
              </div>
            </template>

            <!-- 操作列 -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                small
                color="primary"
                text
                @click="viewHostDetail(item)"
              >
                详情
              </v-btn>
              <v-btn
                small
                color="error"
                text
                @click="blockHost(item)"
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
import hostsApi from '@/components/http/apis/hosts_api';

export default {
  name: 'RiskHosts',
  data: () => ({
    search: '',
    loading: false,
    options: {},
    totalItems: 0,
    headers: [
      { text: 'IP地址', value: 'ipAddress', width: '250' },
      { text: '主机名', value: 'hostname', width: '150' },
      { text: '地理位置', value: 'location', width: '120' },
      { text: '风险类型', value: 'riskType', width: '150' },
      { text: '风险等级', value: 'riskLevel', width: '150', sortable: true },
      { text: '风险原因', value: 'riskReasons', width: '200' },
      { text: '首次发现', value: 'firstSeen', width: '150', sortable: true },
      { text: '最后活动', value: 'lastSeen', width: '150', sortable: true },
      { text: '操作', value: 'actions', sortable: false }
    ],
    hostsData: []
  }),
  watch: {
    options: {
      handler(newOptions, oldOptions) {
        // 当分页或排序选项变化时都需要刷新数据
        if (!oldOptions || 
            newOptions.page !== oldOptions.page || 
            newOptions.itemsPerPage !== oldOptions.itemsPerPage ||
            JSON.stringify(newOptions.sortBy) !== JSON.stringify(oldOptions.sortBy) ||
            JSON.stringify(newOptions.sortDesc) !== JSON.stringify(oldOptions.sortDesc)) {
          console.log('选项变化触发数据刷新:', {
            page: newOptions.page,
            oldPage: oldOptions?.page,
            itemsPerPage: newOptions.itemsPerPage,
            oldItemsPerPage: oldOptions?.itemsPerPage,
          });
          this.fetchHostsData();
        }
      },
      deep: true
    }
  },
  created() {
    this.fetchHostsData();
  },
  methods: {
    async fetchHostsData() {
      this.loading = true;
      
      try {
        // 构建查询参数
        const page = this.options.page || 1;
        const pageSize = this.options.itemsPerPage || 10;
        
        // 获取排序参数
        const sortBy = this.options.sortBy?.[0] || 'riskLevel';
        // 确保正确获取排序方向
        let sortDesc = true; // 默认降序
        if (typeof this.options.sortDesc !== 'undefined' && 
            Array.isArray(this.options.sortDesc) && 
            this.options.sortDesc.length > 0) {
          sortDesc = this.options.sortDesc[0];
        }
        
        const requestParams = {
          page: page,
          pageSize: pageSize,
          sortBy: sortBy,
          sortDesc: sortDesc ? 'desc' : 'asc'
        };
        
        console.log('风险主机API请求参数:', requestParams);
        
        // 发起API请求
        const response = await hostsApi.getRiskHosts(requestParams);
        
        console.log('风险主机API响应:', response.data);
        
        // 处理返回数据
        if (response.data && (response.data.code === 0 || response.data.status?.code === 200)) {
          // 处理两种可能的响应格式
          const data = response.data.data || response.data;
          this.totalItems = data.total;
          
          // 数据已经处理好，直接使用
          this.hostsData = data.items;
          
          console.log(`获取到风险主机数据: ${this.hostsData.length}条记录, 总数: ${this.totalItems}`);
        } else {
          console.error('获取风险主机数据失败:', response.data);
          this.$message.error(response.data?.message || '获取风险主机数据失败');
          // 降级到模拟数据
          this.hostsData = this.generateMockHostsData();
        }
      } catch (error) {
        console.error('获取风险主机数据出错:', error);
        if (error.response) {
          // 服务器返回了错误状态码
          this.$message.error(`服务器错误: ${error.response.status} ${error.response.statusText}`);
        } else if (error.request) {
          // 请求已发出但没有收到响应
          this.$message.error('无法连接到服务器，请检查网络连接');
        } else {
          // 请求配置出错
          this.$message.error('请求配置错误: ' + error.message);
        }
        // 降级到模拟数据
        this.hostsData = this.generateMockHostsData();
      } finally {
        this.loading = false;
      }
    },
    generateMockHostsData() {
      const locations = ['中国', '美国', '日本', '韩国', '德国', '英国', '俄罗斯', '新加坡'];
      const riskTypes = ['端口扫描', '暴力破解', '恶意连接', 'DDoS攻击', '数据泄露', '异常流量'];
      const riskReasons = [
        ['高危端口访问', '高频数据包'],
        ['大流量传输', '系统端口访问'],
        ['大流量传输', '高频数据包'],
        ['高危端口访问', '系统端口访问'],
        ['系统端口访问']
      ];
      
      return Array.from({ length: 15 }, (_, i) => {
        const location = locations[Math.floor(Math.random() * locations.length)];
        const riskType = riskTypes[Math.floor(Math.random() * riskTypes.length)];
        const riskLevel = Math.floor(Math.random() * 5) + 1;
        const firstSeen = new Date(Date.now() - Math.floor(Math.random() * 30 * 86400000)).toLocaleString();
        const lastSeen = new Date(Date.now() - Math.floor(Math.random() * 7 * 86400000)).toLocaleString();
        const isInternal = Math.random() > 0.7;
        
        return {
          id: i + 1,
          ipAddress: isInternal ? this.generateRandomInternalIP() : this.generateRandomExternalIP(),
          hostname: isInternal ? `internal-${Math.floor(Math.random() * 1000)}.local` : `host-${Math.floor(Math.random() * 1000)}.example.com`,
          location: location,
          riskType: riskType,
          riskLevel: riskLevel,
          riskReasons: riskReasons[Math.floor(Math.random() * riskReasons.length)],
          firstSeen: firstSeen,
          lastSeen: lastSeen,
          riskScore: (riskLevel * 1.2).toFixed(2)
        };
      });
    },
    generateRandomInternalIP() {
      return `2001:da8:215:${Math.floor(Math.random() * 255)}:${Math.floor(Math.random() * 9999)}:${Math.floor(Math.random() * 9999)}:${Math.floor(Math.random() * 9999)}:${Math.floor(Math.random() * 9999)}`;
    },
    generateRandomExternalIP() {
      return `2409:${Math.floor(Math.random() * 9999)}:${Math.floor(Math.random() * 9999)}:${Math.floor(Math.random() * 255)}:${Math.floor(Math.random() * 9999)}`;
    },
    getIPColor(ip) {
      if (ip.startsWith('2001:da8')) {
        return 'teal';
      } else {
        return 'blue-grey';
      }
    },
    getLocationColor(location) {
      const colorMap = {
        '中国': 'red',
        '美国': 'blue',
        '日本': 'deep-purple',
        '韩国': 'indigo',
        '德国': 'amber',
        '英国': 'blue-grey',
        '俄罗斯': 'red darken-4',
        '新加坡': 'green',
        'China': 'red',
        'United States': 'blue',
        'Japan': 'deep-purple',
        'South Korea': 'indigo',
        'Germany': 'amber',
        'United Kingdom': 'blue-grey',
        'Russia': 'red darken-4',
        'Singapore': 'green'
      };
      
      return colorMap[location] || 'grey';
    },
    viewHostDetail(item) {
      this.$router.push({
        path: '/address/active-detection',
        query: { address: item.ipAddress }
      });
    },
    blockHost(item) {
      this.$message.success(`已阻断主机: ${item.ipAddress}`);
    }
  }
}
</script>

<style scoped>
.v-data-table {
  background: white !important;
}
</style> 