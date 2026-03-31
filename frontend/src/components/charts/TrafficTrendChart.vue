<template>
  <BaseChart
    :option="chartOption"
    :loading="loading"
    height="300px"
    @click="handleChartClick"
  />
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'
import BaseChart from './BaseChart.vue'
import type { TrafficTrendData } from '@/types/api'

interface Props {
  data: TrafficTrendData[]
  loading?: boolean
  mode?: 'all' | 'inbound' | 'outbound' // 显示模式：all-全部, inbound-仅进站, outbound-仅出站
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  mode: 'all' // 默认显示全部
})

const emit = defineEmits<{
  refresh: []
  click: [data: any]
}>()

const chartOption = computed(() => {
  // 根据模式决定显示哪些系列
  const series: any[] = []
  const legendData: string[] = []

  // 入站流量系列
  if (props.mode === 'all' || props.mode === 'inbound') {
    series.push({
      name: '入站流量',
      type: 'line',
      data: props.data?.map(item => item.inbound) || [],
      smooth: true,
      areaStyle: {
        opacity: 0.3
      },
      itemStyle: {
        color: '#4CAF50'
      }
    })
    legendData.push('入站流量')
  }

  // 出站流量系列
  if (props.mode === 'all' || props.mode === 'outbound') {
    series.push({
      name: '出站流量',
      type: 'line',
      data: props.data?.map(item => item.outbound) || [],
      smooth: true,
      areaStyle: {
        opacity: 0.3
      },
      itemStyle: {
        color: '#2196F3'
      }
    })
    legendData.push('出站流量')
  }

  // 风险流量系列（仅在显示全部时显示）
  if (props.mode === 'all') {
    series.push({
      name: '风险流量',
      type: 'line',
      data: props.data?.map(item => item.risk || 0) || [],
      smooth: true,
      areaStyle: {
        opacity: 0.3
      },
      itemStyle: {
        color: '#FF5252'
      }
    })
    legendData.push('风险流量')
  }

  return {
    title: {
      text: '流量趋势',
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 16
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`
        params.forEach((item: any) => {
          result += `${item.marker}${item.seriesName}: ${formatBytes(item.value)}<br/>`
        })
        return result
      }
    },
    legend: {
      data: legendData,
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
      data: props.data?.map(item => formatTime(item.time)) || []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => formatBytes(value)
      }
    },
    series
  }
})

const handleChartClick = (params: any) => {
  emit('click', params)
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

