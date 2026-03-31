import request from './request'
import type { ApiResponse } from './request'

// ========== ECharts 配置类型 ==========
export interface EChartConfig {
  title?: any
  tooltip?: any
  legend?: any
  xAxis?: any
  yAxis?: any
  series?: any[]
  [key: string]: any
}

export interface GenerateChartRequest {
  chart_config: EChartConfig
  format?: 'option' | 'png' | 'svg'
}

export interface GenerateChartResponse {
  code: number
  message: string
  data: any
}

export interface ChartExamplesResponse {
  code: number
  message: string
  data: {
    line_chart: EChartConfig
    bar_chart: EChartConfig
    pie_chart: EChartConfig
    scatter_chart: EChartConfig
  }
}

// ========== ECharts API ==========
export const echartsApi = {
  /**
   * 生成 ECharts 图表
   * @param chartConfig ECharts 配置对象
   * @param format 导出格式: 'option' | 'png' | 'svg'
   * @returns 图表数据
   */
  generateChart(
    chartConfig: EChartConfig,
    format: 'option' | 'png' | 'svg' = 'option'
  ): Promise<GenerateChartResponse> {
    return request.post('/api/chatai/echarts/generate', {
      chart_config: chartConfig,
      format: format
    })
  },

  /**
   * 获取 ECharts 图表示例
   * @returns 各种类型的图表配置示例
   */
  getExamples(): Promise<ChartExamplesResponse> {
    return request.get('/api/chatai/echarts/examples')
  }
}

// ========== 图表创建工具函数 ==========
export const chartUtils = {
  /**
   * 创建折线图配置
   * @param data 数据数组
   * @param xAxisData X轴数据
   * @param title 图表标题
   * @returns ECharts 配置对象
   */
  createLineChart(
    data: number[],
    xAxisData: string[],
    title: string = '折线图'
  ): EChartConfig {
    return {
      title: { text: title },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: xAxisData
      },
      yAxis: { type: 'value' },
      series: [{
        data: data,
        type: 'line',
        smooth: true
      }]
    }
  },

  /**
   * 创建柱状图配置
   * @param data 数据数组
   * @param xAxisData X轴数据
   * @param title 图表标题
   * @returns ECharts 配置对象
   */
  createBarChart(
    data: number[],
    xAxisData: string[],
    title: string = '柱状图'
  ): EChartConfig {
    return {
      title: { text: title },
      tooltip: {},
      xAxis: {
        type: 'category',
        data: xAxisData
      },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: data
      }]
    }
  },

  /**
   * 创建饼图配置
   * @param data 数据数组 [{name: string, value: number}]
   * @param title 图表标题
   * @returns ECharts 配置对象
   */
  createPieChart(
    data: Array<{ name: string; value: number }>,
    title: string = '饼图'
  ): EChartConfig {
    return {
      title: { text: title },
      tooltip: { trigger: 'item' },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [{
        name: '数据',
        type: 'pie',
        radius: '50%',
        data: data,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
  },

  /**
   * 创建散点图配置
   * @param data 数据数组 [[x, y], ...]
   * @param title 图表标题
   * @returns ECharts 配置对象
   */
  createScatterChart(
    data: Array<[number, number]>,
    title: string = '散点图'
  ): EChartConfig {
    return {
      title: { text: title },
      xAxis: {},
      yAxis: {},
      series: [{
        symbolSize: 20,
        data: data,
        type: 'scatter'
      }]
    }
  },

  /**
   * 创建面积图配置
   * @param data 数据数组
   * @param xAxisData X轴数据
   * @param title 图表标题
   * @returns ECharts 配置对象
   */
  createAreaChart(
    data: number[],
    xAxisData: string[],
    title: string = '面积图'
  ): EChartConfig {
    return {
      title: { text: title },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: xAxisData
      },
      yAxis: { type: 'value' },
      series: [{
        data: data,
        type: 'line',
        areaStyle: {},
        smooth: true
      }]
    }
  }
}

// ========== 统一导出 ==========
export const chartServices = {
  ...echartsApi,
  ...chartUtils
}

export default chartServices

