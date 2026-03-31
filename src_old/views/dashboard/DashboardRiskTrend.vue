<!-- <template>
    <div>
        <div ref="chartContainer" style="width: 100%; height: 400px;"></div>
        <v-row class="mt-2">
            <v-col cols="4">
                <v-select
                    v-model="timeRange"
                    :items="timeRangeOptions"
                    dense
                    outlined
                    label="时间范围"
                />
            </v-col>
            <v-col cols="8">
                <v-chip-group
                    v-model="selectedMetrics"
                    multiple
                    column
                >
                    <v-chip
                        v-for="metric in metrics"
                        :key="metric.value"
                        :value="metric.value"
                        filter
                        small
                    >
                        {{ metric.label }}
                    </v-chip>
                </v-chip-group>
            </v-col>
        </v-row>
    </div>
</template>

<script>
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
    GridComponent,
    TooltipComponent,
    LegendComponent,
    ToolboxComponent,
    TimelineComponent
} from 'echarts/components';
import { init } from 'echarts/core';

// 注册必需的组件
use([
    CanvasRenderer,
    LineChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    ToolboxComponent,
    TimelineComponent
]);

export default {
    name: 'DashboardRiskTrend',
    data: () => ({
        chart: null,
        timeRange: 'week',
        timeRangeOptions: [
            { text: '最近7天', value: 'week' },
            { text: '最近30天', value: 'month' },
            { text: '最近90天', value: 'quarter' }
        ],
        selectedMetrics: ['risk_index', 'high_risk_addr', 'port_risk'],
        metrics: [
            { label: '综合风险指数', value: 'risk_index' },
            { label: '高危地址数', value: 'high_risk_addr' },
            { label: '端口风险值', value: 'port_risk' }
        ],
        chartOptions: {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['综合风险指数', '高危地址数', '端口风险值']
            },
            grid: {
                left: '10%',
                right: '10%',
                bottom: '5%',
                containLabel: true
            },
            xAxis: {
                type: 'time',
                boundaryGap: false
            },
            yAxis: [
            {
                type: 'value',
                name: '风险指数',
                max: 100,
                position: 'left',
                offset: 30,
                nameGap: 40,
                axisLine: { show: true, lineStyle: { color: '#FF4081' } },
                axisLabel: { formatter: '{value}' }
            },
            {
                type: 'value',
                name: '数量',
                position: 'right',
                offset: 30,
                nameGap: 40,
                axisLine: { show: true, lineStyle: { color: '#2196F3' } },
                axisLabel: { formatter: '{value}' }
            }
        ],
            series: [
                {
                    name: '综合风险指数',
                    type: 'line',
                    yAxisIndex: 0,
                    smooth: true,
                    itemStyle: {
                        color: '#FF4081'
                    },
                    data: []
                },
                {
                    name: '高危地址数',
                    type: 'line',
                    yAxisIndex: 1,
                    smooth: true,
                    itemStyle: {
                        color: '#2196F3'
                    },
                    data: []
                },
                {
                    name: '端口风险值',
                    type: 'line',
                    yAxisIndex: 1,
                    smooth: true,
                    itemStyle: {
                        color: '#4CAF50'
                    },
                    data: []
                }
            ]
        }
    }),
    methods: {
        initChart() {
            if (this.chart) {
                this.chart.dispose();
            }
            this.$nextTick(() => {
                if (this.$refs.chartContainer) {
                    this.chart = init(this.$refs.chartContainer, null, {
                        renderer: 'canvas',
                        useDirtyRect: false
                    });
                    this.chart.setOption(this.chartOptions, true);
                    window.addEventListener('resize', this.resizeChart);
                    
                    // 初始化后立即获取数据
                    this.fetchTrendData();
                }
            });
        },
        resizeChart() {
            if (this.chart && this.$refs.chartContainer) {
                // 确保容器可见且有尺寸
                if (this.$refs.chartContainer.offsetHeight > 0 && 
                    this.$refs.chartContainer.offsetWidth > 0) {
                    this.chart.resize({
                        width: 'auto',
                        height: 'auto'
                    });
                }
            }
        },
        async fetchTrendData() {
            // 使用模拟数据
            const mockData = {
                risk_index: [
                    ['2024-03-01', 65],
                    ['2024-03-02', 68],
                    ['2024-03-03', 75],
                    ['2024-03-04', 72],
                    ['2024-03-05', 70],
                    ['2024-03-06', 75],
                    ['2024-03-07', 73]
                ],
                high_risk_addr: [
                    ['2024-03-01', 12],
                    ['2024-03-02', 15],
                    ['2024-03-03', 18],
                    ['2024-03-04', 15],
                    ['2024-03-05', 14],
                    ['2024-03-06', 15],
                    ['2024-03-07', 15]
                ],
                port_risk: [
                    ['2024-03-01', 220],
                    ['2024-03-02', 232],
                    ['2024-03-03', 245],
                    ['2024-03-04', 238],
                    ['2024-03-05', 230],
                    ['2024-03-06', 238],
                    ['2024-03-07', 238]
                ]
            };
            
            // 确保图表存在
            if (!this.chart && this.$refs.chartContainer) {
                this.initChart();
            }
            
            this.updateChartData(mockData);
        },
        
        updateChartData(data) {
            if (this.chart) {
                // 更新数据
                this.chartOptions.series[0].data = data.risk_index || [];
                this.chartOptions.series[1].data = data.high_risk_addr || [];
                this.chartOptions.series[2].data = data.port_risk || [];
                
                // 根据选中的指标显示或隐藏系列
                this.chartOptions.series.forEach((series) => {
                    const metricValue = {
                        '综合风险指数': 'risk_index',
                        '高危地址数': 'high_risk_addr',
                        '端口风险值': 'port_risk'
                    }[series.name];
                    
                    series.show = this.selectedMetrics.includes(metricValue);
                });
                
                // 完全重新设置选项，强制重绘
                this.chart.setOption(this.chartOptions, true);
                
                this.$nextTick(() => {
                    this.resizeChart();
                });
            } else {
                // 如果图表不存在，重新初始化
                this.$nextTick(() => {
                    this.initChart();
                });
            }
        }
    },
    watch: {
        timeRange: {
            handler: 'fetchTrendData',
            immediate: false  // 改为false，避免重复调用
        },
        selectedMetrics: {
            handler(newVal) {
                // 只更新系列的可见性，不重新获取数据
                if (this.chart) {
                    this.chartOptions.series.forEach((series) => {
                        const metricValue = {
                            '综合风险指数': 'risk_index',
                            '高危地址数': 'high_risk_addr',
                            '端口风险值': 'port_risk'
                        }[series.name];
                        
                        series.show = newVal.includes(metricValue);
                    });
                    
                    this.chart.setOption(this.chartOptions);
                }
            }
        },
        '$vuetify.breakpoint.width'() {
            this.resizeChart();
        },
        '$parent.showTrendDialog': {
            handler(val) {
                if (val) {
                    this.$nextTick(() => {
                        // 对话框打开时，延迟重新初始化图表
                        setTimeout(() => {
                            this.initChart();
                        }, 300);
                    });
                }
            },
            immediate: false
        }
    },
    mounted() {
        this.initChart();
    },
    beforeDestroy() {
        if (this.chart) {
            window.removeEventListener('resize', this.resizeChart);
            this.chart.dispose();
            this.chart = null;
        }
    }
};
</script>

<style scoped>
.v-chart {
    width: 100%;
    height: 400px;
}

/* 确保图表容器有明确的尺寸 */
div[ref="chartContainer"] {
    width: 100% !important;
    height: 400px !important;
    min-width: 300px;
    min-height: 300px;
}
</style>  -->