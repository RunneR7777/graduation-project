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
  color?: string
}

interface Props {
  title: string
  data: ChartDataItem[]
  loading?: boolean
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  height: '300px'
})

const emit = defineEmits<{
  click: [data: any]
}>()

const chartOption = computed(() => ({
  title: {
    text: props.title,
    left: 'center',
    textStyle: {
      color: '#333',
      fontSize: 16
    }
  },
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c} ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    top: 'middle'
  },
  series: [
    {
      name: props.title,
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['60%', '50%'],
      data: (props.data || []).map(item => ({
        name: item.name,
        value: item.value,
        itemStyle: {
          color: item.color || undefined
        }
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        formatter: '{b}: {d}%'
      }
    }
  ]
}))

const handleChartClick = (params: any) => {
  emit('click', params)
}
</script>

