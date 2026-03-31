<template>
  <div class="ml-4">
    <v-card-title>
      <v-list-item-action>
        <v-icon class="teal--text">mdi-server-network</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="teal--text">
          <span>远端主机</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-row class="mr-8 ml-2">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            远端主机列表
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
            sort-by="sentPercentage"
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

            <!-- ASN名称列 -->
            <template v-slot:item.asnName="{ item }">
              <v-chip
                small
                color="blue-grey"
                text-color="white"
              >
                {{ item.asnName || 'Unknown' }}
              </v-chip>
            </template>

            <!-- 地理位置列 -->
            <template v-slot:item.country="{ item }">
              <v-chip
                small
                :color="getLocationColor(item.country)"
                text-color="white"
              >
                {{ item.country || 'Unknown' }}
              </v-chip>
            </template>

            <!-- 活跃度列 -->
            <template v-slot:item.activity="{ item }">
              <v-progress-linear
                :value="item.sentPercentage"
                height="15"
                :color="getActivityColor(item.sentPercentage)"
                class="rounded-lg"
              >
                <span class="white--text">{{ item.sentPercentage }}%</span>
              </v-progress-linear>
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
                color="warning"
                text
                @click="monitorHost(item)"
              >
                监控
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
  name: 'RemoteHosts',
  data: () => ({
    search: '',
    loading: false,
    options: {},
    totalItems: 0,
    headers: [
      { text: 'IP地址', value: 'ipAddress', width: '150' },
      { text: 'ASN', value: 'asn', width: '80' },
      { text: 'ASN名称', value: 'asnName', width: '180' },
      { text: '组织', value: 'orgName', width: '150' },
      { text: '国家/地区', value: 'country', width: '120' },
      { text: '网络前缀', value: 'prefix', width: '120' },
      { text: '最后连接', value: 'lastSeen', width: '120' },
      { text: '流量占比', value: 'activity', width: '150' },
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
    getIPColor() {
      // 所有地址都是IPv6，使用统一的颜色
      return 'blue-grey';
    },
    formatIPv6(ip) {
      // 格式化IPv6地址，使其更易读
      if (!ip) return '';
      try {
        // 使用更精确的IPv6地址压缩算法
        const parts = ip.split(':');
        let longestZeroSequence = { start: -1, length: 0 };
        let currentZeroSequence = { start: -1, length: 0 };
        
        // 找到最长的连续0序列
        for (let i = 0; i < parts.length; i++) {
          if (parts[i] === '0' || parts[i] === '') {
            if (currentZeroSequence.start === -1) {
              currentZeroSequence.start = i;
            }
            currentZeroSequence.length++;
          } else {
            if (currentZeroSequence.length > longestZeroSequence.length) {
              longestZeroSequence = { ...currentZeroSequence };
            }
            currentZeroSequence = { start: -1, length: 0 };
          }
        }
        
        // 处理最后一个序列
        if (currentZeroSequence.length > longestZeroSequence.length) {
          longestZeroSequence = { ...currentZeroSequence };
        }
        
        // 压缩最长的0序列
        if (longestZeroSequence.length > 1) {
          const before = parts.slice(0, longestZeroSequence.start).join(':');
          const after = parts.slice(longestZeroSequence.start + longestZeroSequence.length).join(':');
          return before + '::' + after;
        }
        
        return ip;
      } catch (e) {
        console.error('格式化IPv6地址失败:', e);
        return ip;
      }
    },
    async fetchHostsData() {
      this.loading = true;
      
      try {
        // 构建查询参数
        const page = this.options.page || 1;
        const pageSize = this.options.itemsPerPage || 10;
        
        // 获取排序参数
        const sortBy = this.options.sortBy?.[0] || 'sentPercentage';
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
          ipVersion: 'IPv6',  // 明确指定IPv6
          direction: 'All',
          sortBy: sortBy,
          sortDesc: sortDesc ? 'desc' : 'asc'
        };
        
        console.log('远端主机API请求参数:', requestParams);
        
        // 发起API请求
        const response = await hostsApi.getRemoteHosts({
          params: requestParams
        });
        
        console.log('远端主机API响应:', response.data);
        
        // 处理返回数据
        if (response.data && (response.data.code === 0 || response.data.status?.code === 200)) {
          // 处理两种可能的响应格式
          const data = response.data.data || response.data;
          this.totalItems = data.total;
          
          // 转换数据结构以适应前端表格
          this.hostsData = data.items.map(item => ({
            ipAddress: this.formatIPv6(item.address),
            asn: item.asn || 'Unknown',
            asnName: item.asnName || 'Unknown',
            orgName: item.orgName || 'Unknown',
            country: item.country || 'Unknown',
            prefix: item.prefix || 'Unknown',
            lastSeen: item.lastSeen || item.seenSince || '',
            sentPercentage: item.sentPercentage || 0,
            activity: item.activity || item.sentPercentage || 0,
            flows: item.flows || 0
          }));
          
          console.log(`获取到远端主机数据: ${this.hostsData.length}条记录, 总数: ${this.totalItems}`);
          // 不再需要手动前端排序，因为后端已经排序好了
        } else {
          console.error('获取远端主机数据失败:', response.data);
          this.$message.error(response.data?.message || '获取远端主机数据失败');
        }
      } catch (error) {
        console.error('获取远端主机数据出错:', error);
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
      } finally {
        this.loading = false;
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
    getActivityColor(activity) {
      if (activity < 30) return 'blue';
      if (activity < 70) return 'amber';
      return 'red';
    },
    viewHostDetail(item) {
      this.$router.push({
        path: '/address/active-detection',
        query: { address: item.ipAddress }
      });
    },
    monitorHost(item) {
      this.$message.success(`已开始监控主机: ${item.ipAddress}`);
    }
  }
}
</script>

<style scoped>
.v-data-table {
  background: white !important;
}
</style> 