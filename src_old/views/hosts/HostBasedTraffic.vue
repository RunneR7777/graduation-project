<template>
  <div>
    <v-card-title>
      基于主机的流量分析
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

    <!-- 筛选器 -->
    <v-card-text>
      <v-row>
        <v-col cols="12" sm="2">
          <v-select
            v-model="filters.ipVersion"
            :items="ipVersions"
            label="IP版本"
            outlined
            dense
            clearable
          ></v-select>
        </v-col>
        <v-col cols="12" sm="2">
          <v-select
            v-model="filters.localNetwork"
            :items="localNetworks"
            label="本地网络"
            outlined
            dense
            clearable
          ></v-select>
        </v-col>
        <v-col cols="12" sm="2">
          <v-select
            v-model="filters.direction"
            :items="directions"
            label="方向"
            outlined
            dense
            clearable
          ></v-select>
        </v-col>
        <v-col cols="12" sm="2">
          <v-select
            v-model="filters.filterHosts"
            :items="filterHosts"
            label="过滤主机"
            outlined
            dense
            clearable
          ></v-select>
        </v-col>
        <v-col cols="12" sm="2">
          <v-select
            v-model="filters.hostPools"
            :items="hostPools"
            label="主机池"
            outlined
            dense
            clearable
          ></v-select>
        </v-col>
        <v-col cols="12" sm="2">
          <v-btn 
            color="primary" 
            outlined 
            block
            @click="applyFilters"
          >
            应用筛选
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>

    <!-- 数据表格 -->
    <v-data-table
      :headers="headers"
      :items="hostData"
      :loading="loading"
      :server-items-length="totalItems"
      :options.sync="options"
      :page.sync="page"
      :items-per-page.sync="itemsPerPage"
      class="elevation-1"
      :footer-props="{
        'items-per-page-options': [5, 10, 15, 20],
        'items-per-page-text': '每页行数'
      }"
      @update:options="handleTableUpdate"
    >
      <!-- 地址列 -->
      <template v-slot:item.address="{ item }">
        <v-chip
          :color="item.random ? 'green' : 'blue'"
          text-color="white"
          small
          class="mr-2"
        >
          R
        </v-chip>
        <a 
          @click="viewHostDetail(item.address)" 
          class="blue--text text-decoration-none"
        >
          {{ item.address }}
        </a>
      </template>
      
      <!-- 流量分布列 -->
      <template v-slot:item.trafficBreakdown="{ item }">
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
      
      <!-- 吞吐量列 -->
      <template v-slot:item.throughput="{ item }">
        {{ item.throughput }}
        <v-icon v-if="item.trend === 'up'" small color="red">mdi-arrow-up</v-icon>
        <v-icon v-if="item.trend === 'down'" small color="green">mdi-arrow-down</v-icon>
      </template>
    </v-data-table>
  </div>
</template>

<script>
import hostsApi from '@/components/http/apis/hosts_api';

export default {
  name: 'HostBasedTraffic',
  data() {
    return {
      loading: false,
      page: 1,
      itemsPerPage: 10,
      options: {},
      isInitialLoad: true,
      lastRequestTime: 0,
      filters: {
        ipVersion: 'All',
        localNetwork: 'All',
        direction: 'All',
        filterHosts: 'All',
        hostPools: 'All'
      },
      ipVersions: ['All', 'IPv4', 'IPv6'],
      localNetworks: ['All', '192.168.0.0/16', '10.0.0.0/8', '172.16.0.0/12'],
      directions: ['All', '入站', '出站', '双向'],
      filterHosts: ['All', '活跃主机', '非活跃主机'],
      hostPools: ['All', '服务器', '工作站', '移动设备'],
      headers: [
        { text: '地址', value: 'address', align: 'start' },
        { text: '名称', value: 'name' },
        { text: '流量', value: 'flows' },
        { text: '警报', value: 'alerts' },
        { text: '评分', value: 'score' },
        { text: 'CVEs', value: 'cves' },
        { text: '最后见到时间', value: 'seenSince' },
        { text: '流量分布', value: 'trafficBreakdown', sortable: false },
        { text: '吞吐量', value: 'throughput' },
        { text: '总字节数', value: 'totalBytes', sort: (a, b) => this.sortBytes(a, b) }
      ],
      hostData: [],
      totalItems: 0,
      isTableUpdating: false
    }
  },
  watch: {
    itemsPerPage(newVal, oldVal) {
      if (newVal !== oldVal && !this.loading) {
        this.applyFilters();
      }
    }
  },
  methods: {
    async applyFilters() {
      const now = Date.now();
      if (now - this.lastRequestTime < 1000 && !this.isInitialLoad) {
        console.log('请求过于频繁，已忽略');
        return;
      }
      this.lastRequestTime = now;
      
      this.loading = true;
      try {
        console.log('发送请求参数:', {
          ipVersion: this.filters.ipVersion !== 'All' ? this.filters.ipVersion : '',
          localNetwork: this.filters.localNetwork !== 'All' ? this.filters.localNetwork : '',
          direction: this.filters.direction !== 'All' ? this.filters.direction : '',
          filterHosts: this.filters.filterHosts !== 'All' ? this.filters.filterHosts : '',
          hostPools: this.filters.hostPools !== 'All' ? this.filters.hostPools : '',
          page: this.page,
          pageSize: this.itemsPerPage
        });
        
        const response = await hostsApi.getHostBasedTraffic({
          ipVersion: this.filters.ipVersion !== 'All' ? this.filters.ipVersion : '',
          localNetwork: this.filters.localNetwork !== 'All' ? this.filters.localNetwork : '',
          direction: this.filters.direction !== 'All' ? this.filters.direction : '',
          filterHosts: this.filters.filterHosts !== 'All' ? this.filters.filterHosts : '',
          hostPools: this.filters.hostPools !== 'All' ? this.filters.hostPools : '',
          page: this.page,
          pageSize: this.itemsPerPage
        });
        
        console.log('收到响应:', response);
        
        if (response.data.status && response.data.status.code === 200) {
          this.hostData = response.data.data.items;
          this.totalItems = response.data.data.total;
          console.log('更新数据成功:', this.hostData);
        } else {
          console.error('API返回错误:', response.data);
          this.$toast.error(response.data.status?.message || '获取数据失败');
        }
      } catch (error) {
        console.error('Error fetching host data:', error);
        this.$toast.error('获取数据失败');
      } finally {
        this.loading = false;
        this.isInitialLoad = false;
      }
    },
    viewHostDetail(address) {
      this.$router.push(`/host/${address}`);
    },
    sortBytes(a, b) {
      const extractValue = (str) => {
        if (!str) return 0;
        const match = str.match(/^([\d.]+)\s*([KMGT]?B)$/);
        if (!match) return parseFloat(str) || 0;
        const [, value, unit] = match;
        const multipliers = { B: 1, KB: 1e3, MB: 1e6, GB: 1e9, TB: 1e12 };
        return parseFloat(value) * (multipliers[unit] || 1);
      };
      
      return extractValue(a) - extractValue(b);
    },
    handleTableUpdate(options) {
      // 仅在真正需要时才请求数据
      console.log('表格更新选项:', options);
      
      // 检查是否有实际的分页、排序或筛选变化
      const pageChanged = options.page !== this.page;
      const pageSizeChanged = options.itemsPerPage !== this.itemsPerPage;
      
      if ((pageChanged || pageSizeChanged) && !this.loading && !this.isTableUpdating) {
        console.log('分页参数变化，重新请求数据');
        this.page = options.page;
        this.itemsPerPage = options.itemsPerPage;
        this.isTableUpdating = true;
        
        // 设置延迟，防止因多次快速切换导致的重复请求
        setTimeout(() => {
          this.applyFilters();
          this.isTableUpdating = false;
        }, 300);
      }
    }
  },
  created() {
    this.applyFilters();
  },
  mounted() {
    console.log('组件已挂载');
  }
}
</script>

<style scoped>
.v-data-table >>> th {
  font-weight: bold !important;
}
</style> 