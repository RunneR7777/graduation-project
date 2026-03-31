<template>
  <div class="country-distribution-container">
    <v-container fluid>
      <v-card>
        <v-card-title>
          国家分布
          <v-spacer></v-spacer>
          <v-select
            v-model="itemsPerPage"
            :items="[5, 10, 15, 20]"
            label="每页显示"
            outlined
            dense
            class="ml-2"
            style="max-width: 120px"
          ></v-select>
        </v-card-title>
        <v-data-table
          :headers="headers"
          :items="countryData"
          :items-per-page="itemsPerPage"
          :loading="loading"
          class="elevation-1"
          :footer-props="{
            'items-per-page-options': [5, 10, 15, 20],
            'items-per-page-text': '每页行数'
          }"
        >
          <template v-slot:item.name="{ item }">
            <div class="d-flex align-center">
              <img :src="getFlagUrl(item.code)" class="mr-2" height="20" />
              <span>{{ item.name || item.code }}</span>
            </div>
          </template>
          
          <template v-slot:item.breakdown="{ item }">
            <v-progress-linear
              :value="item.sentPercentage"
              height="20"
              class="rounded-lg"
            >
              <template v-slot:default>
                <span class="white--text">
                  <strong>发送</strong>
                </span>
              </template>
            </v-progress-linear>
            <div class="caption text-right">
              <span class="green--text">接收: {{ 100 - item.sentPercentage }}%</span> | 
              <span class="amber--text">发送: {{ item.sentPercentage }}%</span>
            </div>
          </template>
        </v-data-table>
      </v-card>
    </v-container>
  </div>
</template>

<script>
import hostsApi from '@/components/http/apis/hosts_api';

export default {
  name: 'CountryDistribution',
  data() {
    return {
      loading: false,
      itemsPerPage: 10,
      headers: [
        { text: '国家', value: 'name', align: 'start' },
        { text: '主机数', value: 'hosts' },
        { text: '最后见到时间', value: 'seenSince' },
        { text: '流量分布', value: 'breakdown', sortable: false },
        { text: '吞吐量', value: 'throughput' },
        { text: '流量', value: 'traffic', sort: (a, b) => this.sortTraffic(a, b) }
      ],
      countryData: []
    }
  },
  created() {
    this.fetchCountryData();
  },
  methods: {
    async fetchCountryData() {
      this.loading = true;
      try {
        const response = await hostsApi.getCountryDistribution();
        
        console.log('国家分布API响应:', response);
        
        if (response.data && response.data.status && response.data.status.code === 200) {
          this.countryData = response.data.data.items.map(item => ({
            code: item.code,
            name: item.name || item.code,
            hosts: item.hosts,
            seenSince: item.seenSince,
            sentPercentage: item.sentPercentage || 50, // 提供默认值防止进度条出错
            throughput: item.throughput,
            traffic: item.traffic
          }));
        } else if (response.data && response.data.code === 0) {
          this.countryData = response.data.data.items.map(item => ({
            code: item.code,
            name: item.name || item.code,
            hosts: item.hosts,
            seenSince: item.seenSince,
            sentPercentage: item.sentPercentage || 50, // 提供默认值防止进度条出错
            throughput: item.throughput,
            traffic: item.traffic
          }));
        } else {
          console.error('获取国家分布数据失败:', response);
          this.$message.error('获取国家分布数据失败: ' + (response.data?.status?.message || '未知错误'));
        }
      } catch(error) {
        console.error('获取国家分布数据出错:', error);
        this.$message.error('网络错误，请稍后重试');
      } finally {
        this.loading = false;
      }
    },
    getFlagUrl(countryCode) {
      if (!countryCode) return ''; // 增加空值检查
      return `https://flagcdn.com/w20/${countryCode.toLowerCase()}.png`
    },
    sortTraffic(a, b) {
      // 提取数值和单位
      const extractValue = (str) => {
        if (!str) return 0; // 增加空值检查
        const match = str.match(/^([\d.]+)\s*([KMGT]?B)$/)
        if (!match) return 0
        const [, value, unit] = match
        const multipliers = { B: 1, KB: 1e3, MB: 1e6, GB: 1e9, TB: 1e12 }
        return parseFloat(value) * multipliers[unit]
      }
      
      return extractValue(a) - extractValue(b)
    }
  }
}
</script>

<style scoped>
.v-data-table >>> th {
  font-weight: bold !important;
}
</style> 