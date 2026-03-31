<template>
  <div class="ml-4">
    <v-card-title>
      <v-list-item-action>
        <v-icon class="teal--text">mdi-chart-pie</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="teal--text">
          <span>IPv6地址统计</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-row class="mr-8 ml-2">
      <!-- 统计卡片 -->
      <v-col cols="12" md="4">
        <v-card class="mb-4" height="150" color="teal lighten-5">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-ip-network</v-icon>
            活跃地址总数
          </v-card-title>
          <v-card-text class="d-flex justify-center align-center">
            <div class="text-h3 font-weight-bold teal--text">{{ totalAddresses }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card class="mb-4" height="150" color="teal lighten-5">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-format-list-group</v-icon>
            前缀数量
          </v-card-title>
          <v-card-text class="d-flex justify-center align-center">
            <div class="text-h3 font-weight-bold teal--text">{{ prefixCount }}</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card class="mb-4" height="150" color="teal lighten-5">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-percent</v-icon>
            平均命中率
          </v-card-title>
          <v-card-text class="d-flex justify-center align-center">
            <div class="text-h3 font-weight-bold teal--text">{{ averageHitRate }}%</div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 生成方式分布 -->
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-chart-pie</v-icon>
            地址生成方式分布
          </v-card-title>
          <v-card-text style="height: 350px">
            <div ref="generationMethodChart" style="width: 100%; height: 100%;"></div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 前缀分布 -->
      <v-col cols="12" md="6">
        <v-card class="mb-4">
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-chart-bar</v-icon>
            前缀分布
          </v-card-title>
          <v-card-text style="height: 350px">
            <div ref="prefixDistributionChart" style="width: 100%; height: 100%;"></div>
          </v-card-text>
        </v-card>
      </v-col>
      
      <!-- 命中率热力图 -->
      <v-col cols="12">
        <v-card>
          <v-card-title class="subtitle-1 font-weight-bold">
            <v-icon left color="teal">mdi-chart-timeline-variant</v-icon>
            前缀命中率
            <v-spacer></v-spacer>
            <v-text-field
              v-model="search"
              append-icon="mdi-magnify"
              label="搜索前缀"
              single-line
              hide-details
              dense
              outlined
              class="ml-2"
              style="max-width: 250px"
            ></v-text-field>
          </v-card-title>
          <v-data-table
            :headers="hitRateHeaders"
            :items="prefixHitRates"
            :search="search"
            :items-per-page="10"
            class="elevation-1"
          >
            <template v-slot:item.prefix="{ item }">
              <v-chip small color="teal" text-color="white">
                {{ item.prefix }}
              </v-chip>
            </template>
            
            <template v-slot:item.hitRate="{ item }">
              <v-progress-linear
                :value="item.hitRate"
                height="20"
                :color="getHitRateColor(item.hitRate)"
                class="rounded-lg"
              >
                <span class="white--text">{{ item.hitRate }}%</span>
              </v-progress-linear>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script>
// 使用 ECharts 替代 Chart.js
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
  name: 'AddressStatistics',
  data: () => ({
    search: '',
    totalAddresses: 0,
    prefixCount: 0,
    averageHitRate: 0,
    hitRateHeaders: [
      { text: '前缀', value: 'prefix', width: '250' },
      { text: '地址数量', value: 'addressCount', width: '150' },
      { text: '命中率', value: 'hitRate', width: '400' },
      { text: '最后活跃时间', value: 'lastActive', width: '200' }
    ],
    prefixHitRates: [],
    generationMethodChart: null,
    prefixDistributionChart: null
  }),
  mounted() {
    this.fetchStatisticsData();
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.handleResize);
    // 销毁图表实例
    if (this.generationMethodChart) {
      this.generationMethodChart.dispose();
    }
    if (this.prefixDistributionChart) {
      this.prefixDistributionChart.dispose();
    }
  },
  methods: {
    fetchStatisticsData() {
      // 模拟获取数据
      setTimeout(() => {
        // 生成模拟数据
        this.totalAddresses = 12568;
        this.prefixCount = 24;
        this.averageHitRate = 68;
        this.prefixHitRates = this.generateMockPrefixData();
        
        // 初始化图表
        this.initGenerationMethodChart();
        this.initPrefixDistributionChart();
      }, 1000);
    },
    generateMockPrefixData() {
      const prefixes = [
        '2001:da8:215::', '2001:da8:216::', '2001:da8:217::', 
        '2001:da8:218::', '2001:da8:219::', '2001:da8:21a::', 
        '2001:da8:21b::', '2001:da8:21c::', '2001:da8:21d::', 
        '2001:da8:21e::', '2001:da8:21f::', '2001:da8:220::', 
        '2001:da8:221::', '2001:da8:222::', '2001:da8:223::'
      ];
      
      return prefixes.map((prefix, index) => {
        const addressCount = Math.floor(Math.random() * 2000) + 100;
        const hitRate = Math.floor(Math.random() * 100);
        const lastActive = new Date(Date.now() - Math.floor(Math.random() * 86400000)).toLocaleString();
        
        return {
          id: index + 1,
          prefix: prefix,
          addressCount: addressCount,
          hitRate: hitRate,
          lastActive: lastActive
        };
      });
    },
    initGenerationMethodChart() {
      // 初始化 ECharts 实例
      this.generationMethodChart = echarts.init(this.$refs.generationMethodChart);
      
      // 生成方式数据
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          data: ['EUI-64', '随机生成', 'CGA', '静态配置', '临时地址', '其他']
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
            data: [
              { value: 45, name: 'EUI-64' },
              { value: 25, name: '随机生成' },
              { value: 12, name: 'CGA' },
              { value: 8, name: '静态配置' },
              { value: 7, name: '临时地址' },
              { value: 3, name: '其他' }
            ],
            color: [
              '#009688',
              '#2196F3',
              '#9C27B0',
              '#FF9800',
              '#4CAF50',
              '#9E9E9E'
            ]
          }
        ]
      };
      
      // 使用配置项设置图表
      this.generationMethodChart.setOption(option);
    },
    initPrefixDistributionChart() {
      // 初始化 ECharts 实例
      this.prefixDistributionChart = echarts.init(this.$refs.prefixDistributionChart);
      
      // 前缀分布数据
      const prefixes = this.prefixHitRates.map(item => item.prefix.replace('::', ''));
      const addressCounts = this.prefixHitRates.map(item => item.addressCount);
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
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
          data: prefixes,
          axisLabel: {
            interval: 0,
            rotate: 45
          }
        },
        yAxis: {
          type: 'value',
          name: '地址数量'
        },
        series: [
          {
            name: '地址数量',
            type: 'bar',
            data: addressCounts,
            itemStyle: {
              color: '#009688'
            }
          }
        ]
      };
      
      // 使用配置项设置图表
      this.prefixDistributionChart.setOption(option);
    },
    getHitRateColor(hitRate) {
      if (hitRate < 30) return 'blue';
      if (hitRate < 70) return 'amber';
      return 'green';
    },
    handleResize() {
      if (this.generationMethodChart) {
        this.generationMethodChart.resize();
      }
      if (this.prefixDistributionChart) {
        this.prefixDistributionChart.resize();
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