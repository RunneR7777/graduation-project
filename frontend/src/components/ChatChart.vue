<template>
  <div class="chat-chart-container">
    <div 
      ref="chartRef" 
      class="chart" 
      :style="{ width: width, height: height }"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import type { EChartsConfig } from '@/types/api'

interface Props {
  chartConfig: EChartsConfig
  width?: string
  height?: string
  theme?: 'light' | 'dark'
}

const props = withDefaults(defineProps<Props>(), {
  width: '100%',
  height: '400px',
  theme: 'light'
})

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

onMounted(() => {
  initChart()
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

// 监听配置变化
watch(() => props.chartConfig, () => {
  updateChart()
}, { deep: true })

// 监听主题变化
watch(() => props.theme, () => {
  if (chartInstance) {
    chartInstance.dispose()
    initChart()
  }
})

const initChart = () => {
  if (!chartRef.value) return
  
  try {
    chartInstance = echarts.init(chartRef.value, props.theme)
    updateChart()
    
    // 响应式处理 - 使用ResizeObserver监听容器大小变化
    const resizeObserver = new ResizeObserver(() => {
      if (chartInstance) {
        chartInstance.resize()
      }
    })
    resizeObserver.observe(chartRef.value)
    
    // 兼容性处理 - 保留window resize监听
    window.addEventListener('resize', handleResize)
  } catch (error) {
    console.error('初始化图表失败:', error)
  }
}

const updateChart = () => {
  if (!chartInstance || !props.chartConfig) return
  
  try {
    // 设置默认主题色
    const defaultColor = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
    const config = {
      color: defaultColor,
      ...props.chartConfig
    }
    
    chartInstance.setOption(config, true)
  } catch (error) {
    console.error('更新图表失败:', error)
  }
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}
</script>

<style scoped>
.chat-chart-container {
  width: 100%;
  min-width: 300px;
  overflow: hidden;
  margin: 16px 0;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart {
  min-height: 300px;
}

/* 深色主题支持 */
.chat-chart-container.dark {
  background: #1e1e1e;
}
</style>

