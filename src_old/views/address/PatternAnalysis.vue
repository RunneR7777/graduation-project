<template>
  <div class="ml-4">
    <v-card-title>
      <v-list-item-action>
        <v-icon class="teal--text">mdi-fingerprint</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="teal--text">
          <span>生成模式分析</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-row class="mr-8 ml-2">
      <!-- 图表组件 -->
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-chart-pie</v-icon>
            地址生成方式分布
          </v-card-title>
          <v-card-text style="height: 350px">
            <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
            <div v-else ref="genMethodChart" style="width: 100%; height: 100%;"></div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-chart-bar</v-icon>
            前缀分布
          </v-card-title>
          <v-card-text style="height: 350px">
            <v-progress-circular v-if="loading" indeterminate color="primary"></v-progress-circular>
            <div v-else ref="prefixChart" style="width: 100%; height: 100%;"></div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 过滤器 -->
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-text>
            <v-row>
              <v-col cols="12" md="3">
                <v-select
                  v-model="selectedPrefix"
                  :items="prefixOptions"
                  label="前缀"
                  outlined
                  dense
                  @change="filterAddresses"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="selectedGenMethod"
                  :items="genMethodOptions"
                  label="生成方式"
                  outlined
                  dense
                  @change="filterAddresses"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3">
                <v-select
                  v-model="selectedStatus"
                  :items="statusOptions"
                  label="状态"
                  outlined
                  dense
                  @change="filterAddresses"
                ></v-select>
              </v-col>
              <v-col cols="12" md="3" class="d-flex align-center">
                <v-text-field
                  v-model.number="days"
                  type="number"
                  min="1"
                  label="时间窗口(天)"
                  outlined
                  dense
                  class="mr-2"
                  @change="filterAddresses"
                ></v-text-field>
                <v-btn color="primary" @click="filterAddresses">
                  <v-icon left>mdi-filter</v-icon>
                  筛选
                </v-btn>
                <v-btn class="ml-2" text @click="resetFilters">
                  <v-icon left>mdi-refresh</v-icon>
                  重置
                </v-btn>
                <!-- <v-btn v-if="!showStatsPanel" icon class="ml-2" @click="toggleStatsPanel" title="显示统计信息">
                  <v-icon>mdi-chart-box</v-icon>
                </v-btn> -->
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 地址列表 -->
      <v-col cols="12">
        <v-card>
          <v-card-title>
            IPv6地址生成模式
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
            :items="addressesData"
            :search="search"
            :loading="loading"
            :items-per-page="10"
            :footer-props="{
              'items-per-page-options': [10, 20, 50],
              'items-per-page-text': '每页显示:',
              'page-text': '{0}-{1} 共 {2}'
            }"
            class="elevation-1"
            :server-items-length="totalItems"
            :options.sync="options"
            @update:options="fetchAddressesData"
          >
            <!-- 地址列 -->
            <template v-slot:item.address="{ item }">
              <v-chip
                small
                color="teal"
                text-color="white"
              >
                {{ item.address }}
              </v-chip>
            </template>
            
            <!-- 前缀列 -->
            <template v-slot:item.prefix="{ item }">
              <span>{{ item.prefix }}</span>
            </template>
            
            <!-- 接口标识列 -->
            <template v-slot:item.interfaceId="{ item }">
              <span class="font-weight-medium">{{ item.interfaceId }}</span>
            </template>
            
            <!-- MAC地址列 -->
            <template v-slot:item.macAddress="{ item }">
              <span v-if="item.macAddress">{{ item.macAddress }}</span>
              <span v-else class="grey--text">N/A</span>
            </template>
            
            <!-- 生成方式列 -->
            <template v-slot:item.generationMethod="{ item }">
              <v-chip
                small
                :color="getGenMethodColor(item.generationMethod)"
                text-color="white"
              >
                {{ item.generationMethod }}
              </v-chip>
            </template>
            
            <!-- 状态列 -->
            <template v-slot:item.status="{ item }">
              <v-chip
                small
                :color="getStatusColor(item.status)"
                text-color="white"
              >
                {{ item.status }}
              </v-chip>
            </template>
            
            <!-- 操作列 -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                small
                color="primary"
                text
                @click="viewAddressDetail(item)"
              >
                详情
              </v-btn>
              <v-btn
                small
                color="warning"
                text
                @click="monitorAddress(item)"
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
import addressApi from '@/components/http/apis/address_api';
import * as echarts from 'echarts/core';
import { PieChart, BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 注册必要的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  PieChart,
  BarChart,
  CanvasRenderer
]);

export default {
  name: 'PatternAnalysis',
  data: () => ({
    search: '',
    loading: false,
    showStatsPanel: true,
    selectedPrefix: 'all',
    selectedGenMethod: 'all',
    selectedStatus: 'all',
    // 查询时间窗口（天），与后端默认保持一致
    days: 365,
    daysOptions: [
      { text: '近1天', value: 1 },
      { text: '近3天', value: 3 },
      { text: '近7天', value: 7 },
      { text: '近14天', value: 14 },
      { text: '近30天', value: 30 },
      { text: '近一年', value: 365 },
    ],
    prefixOptions: [
      { text: '全部前缀', value: 'all' },
      { text: '2001:da8:215::', value: '2001:da8:215::' },
      { text: '2001:da8:216::', value: '2001:da8:216::' },
      { text: '2001:da8:217::', value: '2001:da8:217::' }
    ],
    genMethodOptions: [
      { text: '全部生成方式', value: 'all' },
      { text: 'EUI-64', value: 'EUI-64' },
      { text: '随机生成', value: '随机生成' },
      { text: 'CGA', value: 'CGA' },
      { text: '静态配置', value: '静态配置' },
      { text: '临时地址', value: '临时地址' },
      { text: '低字节', value: '低字节' },
      { text: '嵌入IPv4', value: '嵌入IPv4' },
      { text: 'ISATAP', value: 'ISATAP' }
    ],
    statusOptions: [
      { text: '全部状态', value: 'all' },
      { text: '活跃', value: '活跃' },
      { text: '非活跃', value: '非活跃' },
      { text: '可疑', value: '可疑' }
    ],
    headers: [
      { text: 'IPv6地址', value: 'address', width: '250' },
      { text: '前缀', value: 'prefix', width: '150' },
      { text: '接口标识', value: 'interfaceId', width: '150' },
      { text: 'MAC地址', value: 'macAddress', width: '150' },
      { text: '生成方式', value: 'generationMethod', width: '120' },
      { text: '状态', value: 'status', width: '100' },
      { text: '最后活跃时间', value: 'lastActive', width: '150' },
      { text: '操作', value: 'actions', sortable: false }
    ],
    addressesData: [],
    totalItems: 0,
    stats: null,
    // 新增：后端返回的前缀Top列表
    prefixTopList: [],
    options: {
      page: 1,
      itemsPerPage: 10
    },
    genMethodChart: null,
    prefixChart: null,
    _updatingOptions: false
  }),
  watch: {
    options: {
      handler() {
        // 避免无限循环调用
        if (this._updatingOptions) return;
        
        this._updatingOptions = true;
        this.fetchAddressesData();
        this._updatingOptions = false;
      },
      deep: true
    }
  },
  methods: {
    toggleStatsPanel() {
      this.showStatsPanel = !this.showStatsPanel;
      // 保存用户偏好到localStorage
      localStorage.setItem('showIPv6StatsPanel', this.showStatsPanel);
    },
    fetchAddressesData() {
      // 轻量并发保护：避免短时间内重复触发造成并发请求
      if (this.loading) return;
      this.loading = true;
      
      // 构建API请求参数
      const params = {
        prefix: this.selectedPrefix,
        genMethod: this.selectedGenMethod,
        status: this.selectedStatus,
        page: this.options.page,
        pageSize: this.options.itemsPerPage,
        days: this.days
      };
      
      addressApi.getPatternAnalysis(params)
        .then(({ data }) => {
          if ((data.code === 0) || (data.status && data.status.code === 200)) {
            const responseData = data.data;
            this.addressesData = responseData.items;
            this.totalItems = responseData.total;
            this.stats = responseData.stats;
            // 保存后端前缀Top数据
            this.prefixTopList = responseData.topPrefixes || [];
          } else {
            this.$message.error(`获取数据失败: ${data.message || data.status?.message || '未知错误'}`);
          }
        })
        .catch(error => {
          console.error('获取IPv6地址模式分析数据失败:', error);
          this.$message.error(`获取数据失败: ${error.message || '网络异常'}`);
        })
        .finally(() => {
          this.loading = false;
          // 在loading结束后再渲染图表，确保v-else的图表容器已挂载
          this.$nextTick(() => {
            this.renderGenMethodChart();
            this.renderPrefixChart();
          });
        });
    },
    renderGenMethodChart() {
      if (!this.stats || !this.stats.iidTypes || !this.$refs.genMethodChart) return;
      
      // 销毁旧图表实例，避免重复渲染导致的问题
      if (this.genMethodChart) {
        this.genMethodChart.dispose();
      }
      
      // 初始化图表
      this.genMethodChart = echarts.init(this.$refs.genMethodChart);
      
      // 准备数据
      const data = Object.entries(this.stats.iidTypes).map(([name, info]) => ({
        name,
        value: info.count
      }));
      
      // 设置颜色映射
      const colorMap = {
        'EUI-64': '#009688',
        '随机生成': '#2196F3',
        'CGA': '#673AB7',
        '静态配置': '#FF9800',
        '临时地址': '#4CAF50',
        '低字节': '#F44336',
        '嵌入IPv4': '#3F51B5',
        'ISATAP': '#00BCD4',
        '其他类型': '#9E9E9E'
      };
      
      // 图表配置
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          data: data.map(item => item.name)
        },
        series: [
          {
            name: '生成方式',
            type: 'pie',
            radius: ['50%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: {
              borderRadius: 10,
              borderColor: '#fff',
              borderWidth: 2
            },
            label: {
              show: false,
              position: 'center'
            },
            emphasis: {
              label: {
                show: true,
                fontSize: '18',
                fontWeight: 'bold'
              }
            },
            labelLine: {
              show: false
            },
            data: data,
            color: Object.values(colorMap)
          }
        ]
      };
      
      // 渲染图表
      this.genMethodChart.setOption(option);
      window.addEventListener('resize', this.genMethodChart.resize);
    },
    renderPrefixChart() {
      if (!this.$refs.prefixChart) return;
      
      // 销毁旧图表实例，避免重复渲染导致的问题
      if (this.prefixChart) {
        this.prefixChart.dispose();
      }
      
      // 初始化图表
      this.prefixChart = echarts.init(this.$refs.prefixChart);
      
      // 使用后端返回的topPrefixes数据，如果没有则使用本地统计数据
      let prefixData = [];
      if (this.prefixTopList && this.prefixTopList.length > 0) {
        prefixData = this.prefixTopList.map(item => ({
          prefix: item.prefix,
          count: item.count,
          percentage: item.percentage
        }));
      } else {
        // 如果后端没有返回topPrefixes数据，使用本地统计（兼容旧版本）
        if (!this.addressesData || !this.addressesData.length) return;
        const prefixCounts = {};
        this.addressesData.forEach(item => {
          const prefix = item.prefix;
          prefixCounts[prefix] = (prefixCounts[prefix] || 0) + 1;
        });
        prefixData = Object.entries(prefixCounts)
          .map(([prefix, count]) => ({ 
            prefix, 
            count,
            percentage: Math.round(count / this.addressesData.length * 100 * 100) / 100
          }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 8);
      }
      
      // 图表配置（修复tooltip结构）
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: (params) => {
            const item = prefixData[params[0].dataIndex];
            return `${item.prefix}<br/>数量: ${item.count}<br/>占比: ${item.percentage}%`;
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: prefixData.map(item => {
            let shortPrefix = item.prefix.replace('::', '');
            return shortPrefix.length > 12 ? shortPrefix.substring(0, 12) + '...' : shortPrefix;
          }),
          axisLabel: { rotate: 45, interval: 0 }
        },
        yAxis: { type: 'value', name: '地址数量' },
        series: [
          {
            name: '地址数量',
            type: 'bar',
            barWidth: '60%',
            data: prefixData.map(item => item.count),
            itemStyle: { color: '#009688' }
          }
        ]
      };
      
      // 渲染图表
      this.prefixChart.setOption(option);
      window.addEventListener('resize', this.prefixChart.resize);
    },
    refreshData() {
      this.fetchAddressesData();
    },
    getGenMethodColor(method) {
      const colorMap = {
        'EUI-64': 'teal',
        '随机生成': 'blue',
        'CGA': 'purple',
        '静态配置': 'orange',
        '临时地址': 'green',
        '低字节': 'red',
        '嵌入IPv4': 'indigo',
        'ISATAP': 'cyan'
      };
      
      return colorMap[method] || 'grey';
    },
    getTypeColor(type) {
      const colorMap = {
        '单播': 'primary',
        '多播': 'deep-purple',
        '未指定': 'grey'
      };
      
      return colorMap[type] || 'grey';
    },
    getStatusColor(status) {
      const colorMap = {
        '活跃': 'green',
        '非活跃': 'grey',
        '可疑': 'orange'
      };
      
      return colorMap[status] || 'grey';
    },
    filterAddresses() {
      // 重置到第一页
      this.options.page = 1;
      this.fetchAddressesData();
    },
    resetFilters() {
      this.selectedPrefix = 'all';
      this.selectedGenMethod = 'all';
      this.selectedStatus = 'all';
      this.days = 7;
      this.options.page = 1;
      this.fetchAddressesData();
    },
    viewAddressDetail(item) {
      this.$router.push({
        path: '/address/active-detection',
        query: { ipAddress: item.address }
      });
    },
    monitorAddress(item) {
      this.$message.success(`已开始监控地址: ${item.address}`);
    },
    handleResize() {
      if (this.genMethodChart) {
        this.genMethodChart.resize();
      }
      if (this.prefixChart) {
        this.prefixChart.resize();
      }
    }
  },
  created() {
    this.fetchAddressesData();
  },
  mounted() {
    this.$nextTick(() => {
      if (this.stats) {
        this.renderGenMethodChart();
        this.renderPrefixChart();
      }
    });
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize);
    // 清除图表实例
    if (this.genMethodChart) {
      window.removeEventListener('resize', this.genMethodChart.resize);
      this.genMethodChart.dispose();
      this.genMethodChart = null;
    }
    if (this.prefixChart) {
      window.removeEventListener('resize', this.prefixChart.resize);
      this.prefixChart.dispose();
      this.prefixChart = null;
    }
  }
}
</script>

<style scoped>
.v-data-table {
  background: white !important;
}
</style> 