<template>
    <div class="ml-4">
        <v-card-title>
            <v-list-item-action>
                <v-icon class="teal--text">mdi-map-marker-radius</v-icon>
            </v-list-item-action>
            <v-list-item-content class="ml-n3">
                <v-list-item-title class="teal--text">
                    <span>IP地理位置分布</span>
                </v-list-item-title>
            </v-list-item-content>
        </v-card-title>

        <!-- 筛选器 -->
        <v-row class="mr-8 ml-2">
            <v-col cols="12">
                <v-card>
                    <v-card-text>
                        <v-row>
                            <v-col cols="3">
                                <v-select
                                    v-model="viewType"
                                    :items="viewTypes"
                                    label="查看方式"
                                    dense
                                    outlined
                                ></v-select>
                            </v-col>
                            <v-col cols="3">
                                <v-select
                                    v-model="timeRange"
                                    :items="timeRanges"
                                    label="时间范围"
                                    dense
                                    outlined
                                ></v-select>
                            </v-col>
                            <v-col cols="3">
                                <v-switch
                                    v-model="realtime"
                                    label="实时更新"
                                    color="primary"
                                ></v-switch>
                            </v-col>
                        </v-row>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <!-- 地图容器 -->
        <v-row class="mr-8 ml-2 mt-4">
            <v-col cols="12">
                <v-card>
                    <v-card-text>
                        <div ref="mapContainer" style="width: 100%; height: 600px;"></div>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <!-- 详情面板 -->
        <v-navigation-drawer
            v-model="drawer"
            absolute
            right
            temporary
            width="400"
        >
            <v-list-item>
                <v-list-item-content>
                    <v-list-item-title class="title">
                        连接详情
                    </v-list-item-title>
                    <v-list-item-subtitle>
                        {{ selectedLocation ? selectedLocation.name : '' }}
                    </v-list-item-subtitle>
                </v-list-item-content>
            </v-list-item>

            <v-divider></v-divider>

            <v-list dense v-if="selectedLocation">
                <v-list-item>
                    <v-list-item-content>
                        <v-list-item-title>风险等级</v-list-item-title>
                        <v-list-item-subtitle>
                            <v-chip
                                :color="getColorByRisk(selectedLocation.riskLevel)"
                                dark
                                small
                            >
                                {{ selectedLocation.riskLevel }}
                            </v-chip>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
                
                <v-list-item>
                    <v-list-item-content>
                        <v-list-item-title>活跃连接</v-list-item-title>
                        <v-list-item-subtitle>
                            <v-chip small>入站: {{ selectedLocation.connections.inbound }}</v-chip>
                            <v-chip small class="ml-2">出站: {{ selectedLocation.connections.outbound }}</v-chip>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>

                <v-list-item>
                    <v-list-item-content>
                        <v-list-item-title>主要协议分布</v-list-item-title>
                        <v-list-item-subtitle>
                            <v-chip-group>
                                <v-chip
                                    v-for="protocol in selectedLocation.protocols"
                                    :key="protocol.name"
                                    small
                                    :color="getColorByProtocol(protocol.name)"
                                    dark
                                >
                                    {{ protocol.name }}: {{ protocol.percentage }}%
                                </v-chip>
                            </v-chip-group>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>

                <v-divider></v-divider>

                <v-list-item>
                    <v-list-item-content>
                        <v-list-item-title>Top 来源</v-list-item-title>
                        <v-list-item-subtitle>
                            <div v-for="source in selectedLocation.topSources" :key="source.ip">
                                {{ source.ip }} ({{ source.count }}次)
                            </div>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>

                <v-list-item>
                    <v-list-item-content>
                        <v-list-item-title>Top 目标</v-list-item-title>
                        <v-list-item-subtitle>
                            <div v-for="dest in selectedLocation.topDestinations" :key="dest.ip">
                                {{ dest.ip }} ({{ dest.count }}次)
                            </div>
                        </v-list-item-subtitle>
                    </v-list-item-content>
                </v-list-item>
            </v-list>
        </v-navigation-drawer>
    </div>
</template>

<script>
import { use, init } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { MapChart, EffectScatterChart, LinesChart } from 'echarts/charts';
import {
    TitleComponent,
    TooltipComponent,
    GeoComponent,
    VisualMapComponent
} from 'echarts/components';
import { registerMap } from 'echarts/core';
import chinaGeoJson from '@/assets/map/china.js';

use([
    CanvasRenderer,
    MapChart,
    EffectScatterChart,
    LinesChart,
    TitleComponent,
    TooltipComponent,
    GeoComponent,
    VisualMapComponent
]);

registerMap('china', chinaGeoJson);

export default {
    name: 'IPGeoMap',
    data: () => ({
        chart: null,
        drawer: false,
        selectedLocation: null,
        realtime: true,
        viewType: 'connections',
        timeRange: 'hour',
        viewTypes: [
            { text: '连接数量', value: 'connections' },
            { text: '流量大小', value: 'traffic' },
            { text: '风险等级', value: 'risk' }
        ],
        timeRanges: [
            { text: '最近1小时', value: 'hour' },
            { text: '最近24小时', value: 'day' },
            { text: '最近7天', value: 'week' }
        ],
        updateTimer: null
    }),
    methods: {
        initChart() {
            if (this.chart) {
                this.chart.dispose();
            }

            this.chart = init(this.$refs.mapContainer);
            this.chart.setOption({
                backgroundColor: '#404a59',
                title: {
                    text: 'IP连接地理分布',
                    left: 'center',
                    textStyle: {
                        color: '#fff'
                    }
                },
                tooltip: {
                    trigger: 'item',
                    formatter: params => {
                        if (params.seriesType === 'effectScatter') {
                            return `${params.name}<br/>连接数: ${params.value[2]}`;
                        }
                        return params.name;
                    }
                },
                visualMap: {
                    min: 0,
                    max: 100,
                    calculable: true,
                    inRange: {
                        color: ['#50a3ba', '#eac736', '#d94e5d']
                    },
                    textStyle: {
                        color: '#fff'
                    }
                },
                geo: {
                    map: 'china',
                    label: {
                        emphasis: {
                            show: false
                        }
                    },
                    itemStyle: {
                        normal: {
                            areaColor: '#323c48',
                            borderColor: '#111'
                        },
                        emphasis: {
                            areaColor: '#2a333d'
                        }
                    }
                },
                series: [
                    {
                        name: 'IP连接',
                        type: 'lines',
                        coordinateSystem: 'geo',
                        zlevel: 2,
                        effect: {
                            show: true,
                            period: 6,
                            trailLength: 0.7,
                            color: '#fff',
                            symbolSize: 3
                        },
                        lineStyle: {
                            normal: {
                                color: '#a6c84c',
                                width: 0,
                                curveness: 0.2
                            }
                        },
                        data: []
                    },
                    {
                        name: 'IP分布',
                        type: 'effectScatter',
                        coordinateSystem: 'geo',
                        data: [],
                        symbolSize: val => val[2] / 10,
                        showEffectOn: 'render',
                        rippleEffect: {
                            brushType: 'stroke'
                        },
                        hoverAnimation: true,
                        label: {
                            normal: {
                                formatter: '{b}',
                                position: 'right',
                                show: false
                            }
                        },
                        itemStyle: {
                            normal: {
                                color: '#f4e925',
                                shadowBlur: 10,
                                shadowColor: '#333'
                            }
                        },
                        zlevel: 1
                    }
                ]
            });

            this.chart.on('click', params => {
                if (params.seriesType === 'effectScatter') {
                    this.selectedLocation = {
                        name: params.name,
                        value: params.value[2],
                        protocols: ['HTTP', 'HTTPS', 'DNS'],
                        totalTraffic: '2.5 GB'
                    };
                    this.drawer = true;
                }
            });
        },
        async fetchMapData() {
            try {
                const [geoRes, realtimeRes] = await Promise.all([
                    this.$api.network.getIPGeoData({
                        viewType: this.viewType,
                        timeRange: this.timeRange
                    }),
                    this.$api.network.getIPGeoRealtime()
                ]);

                // 处理地理分布数据
                const locations = geoRes.data.map(item => ({
                    name: item.location,
                    value: [item.longitude, item.latitude, item.count],
                    itemStyle: {
                        normal: {
                            color: this.getColorByRisk(item.risk)
                        }
                    }
                }));

                // 处理实时连接数据
                const lines = realtimeRes.data.map(conn => ({
                    coords: [
                        [conn.source.longitude, conn.source.latitude],
                        [conn.target.longitude, conn.target.latitude]
                    ],
                    lineStyle: {
                        normal: {
                            color: this.getColorByProtocol(conn.protocol)
                        }
                    }
                }));

                this.updateMapData(locations, lines);
            } catch (error) {
                this.$message.error('获取地理数据失败');
                this.updateMapData(this.getMockLocations(), this.getMockLines());
            }
        },
        updateMapData(locations, lines) {
            if (!this.chart) return;
            
            const option = this.chart.getOption();
            option.series[0].data = lines;  // 更新连线数据
            option.series[1].data = locations;  // 更新散点数据
            this.chart.setOption(option);
        },
        async viewLocationDetail(location) {
            try {
                const res = await this.$api.network.getIPGeoLocationDetail(location.name);
                this.selectedLocation = {
                    name: location.name,
                    value: location.value[2],
                    protocols: res.data.protocols,
                    totalTraffic: this.formatTraffic(res.data.totalTraffic),
                    connections: res.data.connections,
                    topSources: res.data.topSources,
                    topDestinations: res.data.topDestinations,
                    riskLevel: res.data.riskLevel
                };
                this.drawer = true;
            } catch (error) {
                this.$message.error('获取详情失败');
            }
        },
        // 辅助方法
        getColorByRisk(risk) {
            if (risk >= 80) return '#d94e5d';
            if (risk >= 50) return '#eac736';
            return '#50a3ba';
        },
        getColorByProtocol(protocol) {
            const colors = {
                'HTTP': '#a6c84c',
                'HTTPS': '#ffa022',
                'DNS': '#46bee9',
                'OTHER': '#7cffb2'
            };
            return colors[protocol] || colors.OTHER;
        },
        formatTraffic(bytes) {
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let size = bytes;
            let unitIndex = 0;
            while (size >= 1024 && unitIndex < units.length - 1) {
                size /= 1024;
                unitIndex++;
            }
            return `${size.toFixed(2)} ${units[unitIndex]}`;
        },
        getMockLocations() {
            return [
                {name: '北京', value: [116.405285, 39.904989, 80]},
                {name: '上海', value: [121.472644, 31.231706, 60]},
                {name: '广州', value: [113.280637, 23.125178, 40]},
                {name: '深圳', value: [114.085947, 22.547, 30]}
            ];
        },
        getMockLines() {
            return [
                {
                    coords: [
                        [116.405285, 39.904989],
                        [121.472644, 31.231706]
                    ]
                },
                {
                    coords: [
                        [113.280637, 23.125178],
                        [114.085947, 22.547]
                    ]
                }
            ];
        },
        startRealtimeUpdate() {
            if (this.updateTimer) {
                clearInterval(this.updateTimer);
            }
            if (this.realtime) {
                this.updateTimer = setInterval(() => {
                    this.fetchMapData();
                }, 5000); // 每5秒更新一次
            }
        }
    },
    watch: {
        realtime(val) {
            if (val) {
                this.startRealtimeUpdate();
            } else if (this.updateTimer) {
                clearInterval(this.updateTimer);
            }
        },
        viewType() {
            this.fetchMapData();
        },
        timeRange() {
            this.fetchMapData();
        }
    },
    mounted() {
        this.initChart();
        this.fetchMapData();
        this.startRealtimeUpdate();
    },
    beforeDestroy() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        if (this.chart) {
            this.chart.dispose();
            this.chart = null;
        }
    }
};
</script> 