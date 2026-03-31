<template>
  <div class="chart-container">
    <v-chart 
      v-if="!loading && option"
      :option="option" 
      :loading="loading"
      autoresize
      :style="{ height: height }"
      @click="handleClick"
    />
    <v-skeleton-loader
      v-else
      type="image"
      :height="height"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { 
  LineChart, 
  BarChart, 
  PieChart, 
  ScatterChart,
  MapChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  VisualMapComponent,
  GeoComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  MapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  VisualMapComponent,
  GeoComponent
])

interface Props {
  option: any
  loading?: boolean
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  height: '300px'
})

const emit = defineEmits<{
  click: [params: any]
}>()

const handleClick = (params: any) => {
  emit('click', params)
}
</script>

<style scoped>
.chart-container {
  width: 100%;
}
</style>

