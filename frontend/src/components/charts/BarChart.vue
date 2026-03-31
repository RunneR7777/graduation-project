<template>
  <BaseChart
    :option="chartOption"
    :loading="loading"
    :height="height"
    @click="handleChartClick"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'

interface ChartDataItem {
  name: string
  value: number
}

interface Props {
  title: string
  data: ChartDataItem[]
  loading?: boolean
  height?: string
  horizontal?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  height: '300px',
  horizontal: false
})

const emit = defineEmits<{
  click: [data: any]
}>()

const chartOption = computed(() => {
  const isHorizontal = props.horizontal
  const safeData = props.data || []
  
  return {
    // 动画配置：为柱状图添加流畅的加载动画效果
    animation: true,
    animationDuration: 6000,
    animationEasing: 'cubicOut',
    animationDelay: (idx: number) => idx * 100, // 每个柱子依次出现，形成渐进动画
    title: {
      text: props.title,
      left: 'center',
      textStyle: {
        color: '#333',
        fontSize: 16
      }
    },
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
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: isHorizontal ? 'value' : 'category',
      data: isHorizontal ? undefined : safeData.map(item => item.name)
    },
    yAxis: {
      type: isHorizontal ? 'category' : 'value',
      data: isHorizontal ? safeData.map(item => item.name) : undefined
    },
    series: [
      {
        name: props.title,
        type: 'bar',
        data: safeData.map(item => item.value),
        itemStyle: {
          // 柱状图主色调：使用蓝色系 (#409EFF)，提供更好的视觉对比度和通用性
          // 相比之前的青绿色 (#009688)，蓝色在数据可视化中更常用，且与大多数UI框架的配色方案兼容
          color: '#409EFF'
        },
        label: {
          // 在柱子上显示具体数值
          show: true,
          position: isHorizontal ? 'right' : 'top',
          color: '#333',
          fontSize: 12,
          formatter: (params: any) => {
            // 格式化显示数值，保留适当的小数位数
            const value = params.value
            return typeof value === 'number' ? value.toLocaleString() : value
          }
        },
        emphasis: {
          itemStyle: {
            // 悬停状态颜色：使用深蓝色 (#337ECC)，与主色调 (#409EFF) 形成渐变效果
            // 提供清晰的交互反馈，同时保持整体配色的一致性
            color: '#337ECC'
          }
        }
      }
    ]
  }
})

const handleChartClick = (params: any) => {
  emit('click', params)
}
</script>

