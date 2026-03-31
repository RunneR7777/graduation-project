<!-- <template>
    <div>
        <div ref="chartContainer" style="width: 100%; height: 400px;"></div>
        <v-row class="mt-2">
            <v-col cols="4">
                <v-select
                    v-model="viewType"
                    :items="viewTypes"
                    dense
                    outlined
                    label="查看方式"
                />
            </v-col>
        </v-row>
    </div>
</template>

<script>
import { use, init } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { PieChart } from 'echarts/charts';
import {
    GridComponent,
    TooltipComponent,
    LegendComponent,
    ToolboxComponent
} from 'echarts/components';

// 注册必需的组件
use([
    CanvasRenderer,
    PieChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    ToolboxComponent
]);

export default {
    name: 'DashboardRiskDistribution',
    data: () => ({
        chart: null,
        viewType: 'type',
        viewTypes: [
            { text: '按风险类型', value: 'type' },
            { text: '按区域分布', value: 'area' },
            { text: '按风险等级', value: 'level' }
        ],
        chartOptions: {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c} ({d}%)'
            },
            legend: {
                orient: 'vertical',
                left: 'left',
                top: 'middle'
            },
            series: [
                {
                    name: '风险分布',
                    type: 'pie',
                    radius: ['50%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2
                    },
                    label: {
                        show: true,
                        position: 'outside',
                        formatter: '{b}: {c} ({d}%)'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: '16',
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: true
                    },
                    data: []
                }
            ],
            color: [
                '#FF4081',
                '#2196F3',
                '#4CAF50',
                '#FFC107',
                '#9C27B0'
            ]
        }
    }),
    methods: {
        initChart() {
            this.chart = init(this.$refs.chartContainer);
            this.chart.setOption(this.chartOptions);
        },
        async fetchDistributionData() {
            // 使用模拟数据
            const mockData = {
                type: {
                    '地址暴露': 125,
                    '端口风险': 86,
                    '流量异常': 45,
                    '配置错误': 32,
                    '其他风险': 28
                }
            };
            this.updateChartData(mockData);
        },
        updateChartData(data) {
            if (!this.chart) return;

            let seriesData = [];
            switch(this.viewType) {
                case 'type':
                    seriesData = Object.entries(data.type).map(([name, value]) => ({
                        name,
                        value
                    }));
                    break;
                // 其他类型的处理...
            }
            
            this.chartOptions.series[0].data = seriesData;
            this.chart.setOption(this.chartOptions);
        }
    },
    watch: {
        viewType: 'fetchDistributionData',
        '$vuetify.breakpoint.width'() {
            if (this.chart) {
                this.chart.resize();
            }
        }
    },
    mounted() {
        this.initChart();
        this.fetchDistributionData();
    },
    beforeDestroy() {
        if (this.chart) {
            this.chart.dispose();
            this.chart = null;
        }
    }
};
</script>

<style scoped>
.chart-container {
    width: 100%;
    height: 400px;
}
</style>  -->