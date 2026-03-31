<template>
  <div>
    <v-card>
      <v-card-title>安全风险趋势分析</v-card-title>
      <v-card-text>
        <div style="height: 400px;" ref="trendChart"></div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  LineChart,
  CanvasRenderer
])

const trendChart = ref<HTMLElement | null>(null)
let chartInstance: any = null

const renderChart = () => {
  if (!trendChart.value) return
  
  chartInstance = echarts.init(trendChart.value)
  
  const option = {
    title: {
      text: '安全风险趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['风险事件', '高危事件', '风险评分'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: Array.from({ length: 24 }, (_, i) => `${i}:00`)
    },
    yAxis: [
      {
        type: 'value',
        name: '事件数量',
        position: 'left'
      },
      {
        type: 'value',
        name: '风险评分',
        position: 'right',
        max: 100
      }
    ],
    series: [
      {
        name: '风险事件',
        type: 'line',
        data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 20)),
        smooth: true,
        itemStyle: { color: '#FF9800' }
      },
      {
        name: '高危事件',
        type: 'line',
        data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 8)),
        smooth: true,
        itemStyle: { color: '#F44336' }
      },
      {
        name: '风险评分',
        type: 'line',
        yAxisIndex: 1,
        data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 40) + 60),
        smooth: true,
        itemStyle: { color: '#2196F3' }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

onMounted(() => {
  renderChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

