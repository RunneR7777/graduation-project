<template>
  <div class="ipv6-address-analysis">
    <v-card flat class="pa-4 mb-4">
      <v-row>
        <v-col cols="12">
          <div class="d-flex align-center mb-3">
            <v-icon size="36" color="teal" class="mr-3">mdi-ip-network-outline</v-icon>
            <h1 class="text-h4 teal--text font-weight-bold mb-0">IPv6地址行为分析</h1>
          </div>
          <v-divider></v-divider>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <v-col cols="12" md="8">
          <v-card class="mb-4 address-card" elevation="2">
            <v-card-title class="teal lighten-4 d-flex">
              <v-icon left class="mr-2">mdi-ip</v-icon>
              地址信息
            </v-card-title>
            <v-card-text class="pa-4">
              <v-row class="address-container">
                <v-col cols="12">
                  <div class="primary-address text-h5 font-weight-medium">
                    {{ ipData.ipAddress }}
                    <v-chip 
                      v-if="ipData.location" 
                      color="red" 
                      text-color="white" 
                      x-small 
                      class="ml-2"
                    >
                      {{ ipData.location }}
                    </v-chip>
                  </div>
                  <div v-if="ipData.alternateIp" class="secondary-address grey--text text--darken-1 mt-1">
                    {{ ipData.alternateIp }}
                  </div>
                </v-col>
              </v-row>
              
              <v-row class="mac-container mt-3">
                <v-col cols="12" md="6">
                  <div class="subtitle-1">路由器/接入点MAC</div>
                  <div class="font-weight-medium">{{ ipData.routerMac }}</div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="subtitle-1">主机MAC</div>
                  <div class="font-weight-medium d-flex align-center">
                    {{ ipData.hostMac }}
                    <v-chip 
                      v-if="ipData.isRouter" 
                      color="primary" 
                      x-small 
                      class="ml-2"
                    >
                      路由器/交换机
                    </v-chip>
                  </div>
                </v-col>
              </v-row>
              
              <v-row class="asn-container mt-3">
                <v-col cols="12">
                  <div class="subtitle-1">ASN信息</div>
                  <div class="d-flex align-center">
                    <div class="font-weight-medium">{{ ipData.asnInfo }}</div>
                    <div v-if="ipData.asnNumber" class="asn-number grey--text text--darken-1 ml-2">
                      [ASN {{ ipData.asnNumber }}]
                    </div>
                  </div>
                  <div class="mt-2">
                    <v-btn 
                      small 
                      text 
                      color="primary" 
                      class="px-2 mr-2"
                      elevation="0"
                    >
                      <v-icon left size="16">mdi-web</v-icon>
                      Whois查询
                    </v-btn>
                    <v-btn 
                      small 
                      text 
                      color="primary" 
                      class="px-2"
                      elevation="0"
                    >
                      <v-icon left size="16">mdi-chart-box-outline</v-icon>
                      RIPEstat查询
                    </v-btn>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
        
        <v-col cols="12" md="4">
          <v-card class="security-metrics" height="100%" elevation="2">
            <v-card-title class="teal lighten-4">
              <v-icon left class="mr-2">mdi-shield-alert-outline</v-icon>
              安全指标
            </v-card-title>
            <v-card-text class="pa-4">
              <div class="metric-item d-flex align-center justify-space-between mb-4">
                <span class="subtitle-1">行为异常计数</span>
                <v-chip 
                  :color="getAnomalyColor(ipData.anomalyCount)" 
                  text-color="white" 
                  class="font-weight-bold"
                >
                  {{ ipData.anomalyCount }}
                </v-chip>
              </div>
              
              <v-divider class="mb-4"></v-divider>
              
              <div class="time-container">
                <div class="subtitle-1 mb-2">活动时间范围</div>
                <v-row>
                  <v-col cols="12">
                    <v-card flat class="time-card pa-2 grey lighten-4">
                      <div class="text-caption">首次观察</div>
                      <div class="font-weight-medium">{{ ipData.firstSeen }}</div>
                    </v-card>
                  </v-col>
                  <v-col cols="12">
                    <v-card flat class="time-card pa-2 grey lighten-4">
                      <div class="text-caption">最后观察</div>
                      <div class="font-weight-medium">{{ ipData.lastSeen }}</div>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <v-col cols="12">
          <v-card elevation="2">
            <v-tabs 
              v-model="activeTab" 
              background-color="teal"
              dark
              grow
              slider-color="yellow"
            >
              <v-tab>
                <v-icon left>mdi-chart-timeline-variant</v-icon>
                流量分析
              </v-tab>
              <v-tab>
                <v-icon left>mdi-server-network</v-icon>
                网络活动
              </v-tab>
              <v-tab>
                <v-icon left>mdi-timeline-alert-outline</v-icon>
                安全事件
              </v-tab>
            </v-tabs>
            
            <v-tabs-items v-model="activeTab">
              <!-- 流量分析选项卡 -->
              <v-tab-item>
                <v-card flat>
                  <v-card-text>
                    <v-row>
                      <v-col cols="12" md="6">
                        <v-card flat class="grey lighten-4 pa-3">
                          <div class="d-flex align-center justify-space-between mb-2">
                            <div class="subtitle-1 font-weight-medium">发送流量</div>
                            <div class="text-h6 teal--text">{{ ipData.sentTraffic }}</div>
                          </div>
                          <v-progress-linear
                            color="teal"
                            height="8"
                            :value="getSentPercentage(ipData.sentTraffic)"
                            rounded
                          ></v-progress-linear>
                        </v-card>
                      </v-col>
                      <v-col cols="12" md="6">
                        <v-card flat class="grey lighten-4 pa-3">
                          <div class="d-flex align-center justify-space-between mb-2">
                            <div class="subtitle-1 font-weight-medium">接收流量</div>
                            <div class="text-h6 teal--text">{{ ipData.receivedTraffic }}</div>
                          </div>
                          <v-progress-linear
                            color="teal accent-4"
                            height="8"
                            :value="getReceivedPercentage(ipData.receivedTraffic)"
                            rounded
                          ></v-progress-linear>
                        </v-card>
                      </v-col>
                    </v-row>
                    
                    <v-row class="mt-4">
                      <v-col cols="12">
                        <div class="text-center text-h6 mb-4">流量时间分布</div>
                        <div class="traffic-chart">
                          <div class="chart-area">
                            <svg height="200" width="100%" viewBox="0 0 800 200">
                              <!-- 模拟图表背景网格 -->
                              <line x1="0" y1="0" x2="800" y2="0" stroke="#e0e0e0" stroke-width="1" />
                              <line x1="0" y1="50" x2="800" y2="50" stroke="#e0e0e0" stroke-width="1" />
                              <line x1="0" y1="100" x2="800" y2="100" stroke="#e0e0e0" stroke-width="1" />
                              <line x1="0" y1="150" x2="800" y2="150" stroke="#e0e0e0" stroke-width="1" />
                              <line x1="0" y1="200" x2="800" y2="200" stroke="#e0e0e0" stroke-width="1" />
                              
                              <!-- 发送流量折线 -->
                              <polyline
                                fill="none"
                                stroke="#26A69A"
                                stroke-width="3"
                                points="0,180 100,120 200,150 300,100 400,90 500,70 600,110 700,60 800,40"
                              />
                              
                              <!-- 接收流量折线 -->
                              <polyline
                                fill="none"
                                stroke="#00BFA5"
                                stroke-width="3"
                                points="0,160 100,130 200,170 300,140 400,160 500,90 600,130 700,100 800,80"
                                stroke-dasharray="5,5"
                              />
                            </svg>
                          </div>
                          <div class="d-flex justify-center mt-2">
                            <div class="legend-item mr-4">
                              <v-icon small color="teal">mdi-circle</v-icon>
                              <span class="caption ml-1">发送流量</span>
                            </div>
                            <div class="legend-item">
                              <v-icon small color="teal accent-4">mdi-circle</v-icon>
                              <span class="caption ml-1">接收流量</span>
                            </div>
                          </div>
                        </div>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-tab-item>
              
              <!-- 网络活动选项卡 -->
              <v-tab-item>
                <v-card flat>
                  <v-card-text>
                    <v-data-table
                      :headers="flowHeaders"
                      :items="ipData.flows"
                      hide-default-footer
                      class="elevation-0"
                      dense
                    >
                      <template v-slot:header.asClient="{ header }">
                        <v-icon small class="mr-1">mdi-upload</v-icon>
                        {{ header.text }}
                      </template>
                      <template v-slot:header.asServer="{ header }">
                        <v-icon small class="mr-1">mdi-download</v-icon>
                        {{ header.text }}
                      </template>
                    </v-data-table>
                    
                    <v-divider class="my-4"></v-divider>
                    
                    <v-row>
                      <v-col cols="12">
                        <div class="text-h6 mb-3">已联系服务器</div>
                        <v-row>
                          <v-col cols="4" md="2" v-for="(value, service) in ipData.contactedServers" :key="service">
                            <v-card outlined class="text-center pa-2">
                              <div class="caption grey--text">{{ service }}</div>
                              <div class="text-h5 font-weight-bold" :class="value > 0 ? 'teal--text' : ''">
                                {{ value }}
                              </div>
                            </v-card>
                          </v-col>
                        </v-row>
                      </v-col>
                    </v-row>
                    
                    <v-divider class="my-4"></v-divider>
                    
                    <v-row>
                      <v-col cols="12">
                        <div class="text-h6 mb-3">TCP统计</div>
                        <v-data-table
                          :headers="tcpHeaders"
                          :items="ipData.tcpStats"
                          hide-default-footer
                          class="elevation-0"
                          dense
                        ></v-data-table>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-tab-item>
              
              <!-- 安全事件选项卡 -->
              <v-tab-item>
                <v-card flat>
                  <v-card-text class="pa-4">
                    <div class="text-h6 mb-3">主要安全事件</div>
                    
                    <v-timeline dense>
                      <v-timeline-item
                        v-for="(event, i) in securityEvents"
                        :key="i"
                        :color="event.color"
                        small
                      >
                        <div class="d-flex align-start">
                          <div>
                            <div class="font-weight-medium">{{ event.title }}</div>
                            <div class="text-caption">{{ event.time }}</div>
                            <div class="mt-1">{{ event.description }}</div>
                          </div>
                          <v-spacer></v-spacer>
                          <v-chip x-small :color="event.color" text-color="white">
                            {{ event.severity }}
                          </v-chip>
                        </div>
                      </v-timeline-item>
                    </v-timeline>
                    
                    <div class="text-center mt-3" v-if="securityEvents.length === 0">
                      <v-icon color="green" large>mdi-shield-check</v-icon>
                      <div class="mt-2">未检测到安全事件</div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-tab-item>
            </v-tabs-items>
          </v-card>
        </v-col>
      </v-row>
      
      <v-row class="mt-4">
        <v-col cols="12">
          <v-card class="pa-4" elevation="2">
            <div class="d-flex justify-space-between align-center">
              <div class="text-h6">监控与管理</div>
              <div>
                <v-btn
                  color="primary"
                  class="mr-2"
                  @click="addToMonitoring"
                >
                  <v-icon left>mdi-radar</v-icon>
                  添加ICMP监控
                </v-btn>
                <v-btn
                  color="warning"
                  class="mr-2"
                  @click="addToVulnScan"
                >
                  <v-icon left>mdi-magnify-scan</v-icon>
                  添加到漏洞扫描
                </v-btn>
                <v-btn
                  color="grey"
                  text
                  class="mr-2"
                  @click="resetStats"
                >
                  <v-icon left>mdi-refresh</v-icon>
                  重置统计
                </v-btn>
                <v-btn
                  color="grey darken-1"
                  text
                  @click="downloadJson"
                >
                  <v-icon left>mdi-download</v-icon>
                  下载JSON
                </v-btn>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'IPv6AddressAnalysis',
  props: {
    ipAddress: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      activeTab: 0,
      ipData: {
        routerMac: 'Hangzhou_2C:39:8D',
        hostMac: 'Hangzhou_2C:37:92',
        ipAddress: '2001:da8:215:4068:148d:68e7:419e:9536',
        alternateIp: '2001:da8:215:4068:47d6:c263:b5ee:bc22/64',
        location: '中国',
        isRouter: true,
        asnInfo: 'CERNET2 IX at Beijing University of Posts and Telecommunications',
        asnNumber: '24350',
        anomalyCount: 1,
        firstSeen: '03/03/2023 23:17:42 (02:28:18 前)',
        lastSeen: '04/03/2023 01:43:13 (02:47 前)',
        sentTraffic: '63 Pkts / 6.8 KB',
        receivedTraffic: '48 Pkts / 6 KB',
        flows: [
          { type: '活跃 / 总计 / 警报 / 端口无法访问', asClient: '0 — / 18 — / 17 — / 0 —', asServer: '0 — / 18 — / 14 — / 0 —' },
          { type: '带黑名单主机的总流量', asClient: '0 —', asServer: '0 —' },
          { type: '总单向TCP/UDP流量', asClient: '4 (22.2 %)', asServer: '2 (11.1 %)' },
          { type: '活跃对等点', asClient: '0 —', asServer: '1 —' },
          { type: 'TCP/UDP无响应流量(对等IP和服务器端口)', asClient: '2 —', asServer: '2 —' }
        ],
        contactedServers: {
          'DNS': 0,
          'SMTP': 0,
          'POP': 0,
          'IMAP': 0,
          'NTP': 1,
          'HTTP': 0
        },
        tcpStats: [
          { type: '重传 / 乱序 / 丢失 / 保活', sent: '0 Pkts — / 8 Pkts — / 0 Pkts — / 0 Pkts —', received: '0 Pkts — / 4 Pkts — / 0 Pkts — / 0 Pkts —' }
        ]
      },
      flowHeaders: [
        { text: '类型', value: 'type', width: '40%' },
        { text: '作为客户端', value: 'asClient', width: '30%' },
        { text: '作为服务器', value: 'asServer', width: '30%' }
      ],
      tcpHeaders: [
        { text: '类型', value: 'type', width: '40%' },
        { text: '发送', value: 'sent', width: '30%' },
        { text: '接收', value: 'received', width: '30%' }
      ],
      securityEvents: [
        {
          title: 'NTP服务器连接',
          time: '04/03/2023 01:12:45',
          description: '设备与NTP服务器建立连接，正常的时间同步行为。',
          severity: '正常',
          color: 'green'
        }
      ],
      currentAddress: this.$route.query.address || ''
    }
  },
  computed: {
    displayAddress() {
      return this.currentAddress || this.ipAddress || '';
    }
  },
  watch: {
    '$route.query.address': function(newAddress) {
      if (newAddress) {
        this.currentAddress = newAddress;
        this.fetchIPDetails();
      }
    }
  },
  mounted() {
    if (this.displayAddress) {
      this.fetchIPDetails();
    }
  },
  methods: {
    fetchIPDetails() {
      console.log(`获取IP详情: ${this.displayAddress}`);
      
      // 由于没有真实API，创建一个模拟的IP数据生成函数
      this.ipData = this.generateMockDataForIP(this.displayAddress);
      
      // 生成随机的安全事件
      this.generateSecurityEvents();
    },
    
    generateMockDataForIP(ipAddress) {
      // 使用IP地址的某些部分来随机化数据
      const ipParts = ipAddress.split(':');
      const lastPart = ipParts[ipParts.length - 1] || '0000';
      const secondLastPart = ipParts[ipParts.length - 2] || '0000';
      
      // 生成基于IP的伪随机数
      const randomSeed = parseInt(lastPart, 16) % 100;
      
      return {
        routerMac: `Hangzhou_2C:${randomSeed.toString(16).padStart(2, '0')}:8D`,
        hostMac: `Hangzhou_2C:${(randomSeed + 10).toString(16).padStart(2, '0')}:92`,
        ipAddress: ipAddress,
        alternateIp: `${ipParts.slice(0, -2).join(':')}:${secondLastPart}:${parseInt(lastPart, 16) + 100}/64`,
        location: '中国',
        isRouter: randomSeed % 3 === 0,
        asnInfo: 'CERNET2 IX at Beijing University of Posts and Telecommunications',
        asnNumber: '24350',
        anomalyCount: randomSeed % 5,
        firstSeen: `${new Date(Date.now() - 86400000 * (randomSeed % 10)).toLocaleString()}`,
        lastSeen: `${new Date(Date.now() - 3600000 * (randomSeed % 24)).toLocaleString()}`,
        sentTraffic: `${63 + randomSeed} Pkts / ${6.8 + (randomSeed / 10).toFixed(1)} KB`,
        receivedTraffic: `${48 + randomSeed} Pkts / ${6 + (randomSeed / 10).toFixed(1)} KB`,
        flows: [
          { type: '活跃 / 总计 / 警报 / 端口无法访问', asClient: `${randomSeed % 2} — / ${18 + randomSeed % 5} — / ${17 - randomSeed % 3} — / 0 —`, asServer: `${randomSeed % 3} — / ${18 + randomSeed % 4} — / ${14 - randomSeed % 3} — / 0 —` },
          { type: '带黑名单主机的总流量', asClient: `${randomSeed % 2} —`, asServer: `${randomSeed % 2} —` },
          { type: '总单向TCP/UDP流量', asClient: `${4 + randomSeed % 3} (${22.2 + randomSeed} %)`, asServer: `${2 + randomSeed % 3} (${11.1 + randomSeed} %)` },
          { type: '活跃对等点', asClient: `${randomSeed % 3} —`, asServer: `${1 + randomSeed % 2} —` },
          { type: 'TCP/UDP无响应流量(对等IP和服务器端口)', asClient: `${2 + randomSeed % 3} —`, asServer: `${2 + randomSeed % 2} —` }
        ],
        contactedServers: {
          'DNS': randomSeed % 3,
          'SMTP': randomSeed % 2,
          'POP': randomSeed % 2,
          'IMAP': randomSeed % 2,
          'NTP': 1 + randomSeed % 2,
          'HTTP': randomSeed % 4
        },
        tcpStats: [
          { type: '重传 / 乱序 / 丢失 / 保活', 
            sent: `${randomSeed % 3} Pkts — / ${8 + randomSeed % 4} Pkts — / ${randomSeed % 2} Pkts — / ${randomSeed % 2} Pkts —`, 
            received: `${randomSeed % 2} Pkts — / ${4 + randomSeed % 3} Pkts — / ${randomSeed % 2} Pkts — / ${randomSeed % 2} Pkts —` }
        ]
      };
    },
    
    generateSecurityEvents() {
      // 基于anomalyCount生成随机的安全事件
      const anomalyCount = this.ipData.anomalyCount;
      this.securityEvents = [];
      
      // 总是添加NTP连接事件
      this.securityEvents.push({
        title: 'NTP服务器连接',
        time: this.ipData.lastSeen.split('(')[0].trim(),
        description: '设备与NTP服务器建立连接，正常的时间同步行为。',
        severity: '正常',
        color: 'green'
      });
      
      // 如果有异常，添加相应的安全事件
      if (anomalyCount > 0) {
        if (anomalyCount > 1) {
          this.securityEvents.push({
            title: '可疑端口扫描',
            time: new Date(Date.now() - 7200000).toLocaleString(),
            description: '检测到设备对多个常见服务端口进行扫描行为。',
            severity: '中风险',
            color: 'orange'
          });
        }
        
        if (anomalyCount > 2) {
          this.securityEvents.push({
            title: '连接到已知恶意主机',
            time: new Date(Date.now() - 14400000).toLocaleString(),
            description: '设备尝试连接到已知的恶意服务器IP地址。',
            severity: '高风险',
            color: 'red'
          });
        }
      }
    },
    
    getAnomalyColor(count) {
      if (count === 0) return 'green';
      if (count <= 2) return 'orange';
      return 'red';
    },
    
    getSentPercentage(traffic) {
      // 简单解析发送流量并返回百分比值
      const packets = parseInt(traffic.split('Pkts')[0].trim());
      return Math.min(packets, 100);
    },
    
    getReceivedPercentage(traffic) {
      // 简单解析接收流量并返回百分比值
      const packets = parseInt(traffic.split('Pkts')[0].trim());
      return Math.min(packets, 100);
    },
    
    addToMonitoring() {
      this.$message.success(`已将${this.ipData.ipAddress}添加到ICMP监控`);
    },
    
    addToVulnScan() {
      this.$message.success(`已将${this.ipData.ipAddress}添加到漏洞扫描列表`);
    },
    
    resetStats() {
      this.$message.success(`已重置${this.ipData.ipAddress}的统计数据`);
    },
    
    downloadJson() {
      this.$message.success(`正在下载${this.ipData.ipAddress}的JSON数据`);
      
      // 创建一个包含所有数据的对象
      const exportData = {
        ipAddress: this.ipData.ipAddress,
        routerMac: this.ipData.routerMac,
        hostMac: this.ipData.hostMac,
        alternateIp: this.ipData.alternateIp,
        location: this.ipData.location,
        asnInfo: this.ipData.asnInfo,
        trafficStats: {
          sent: this.ipData.sentTraffic,
          received: this.ipData.receivedTraffic
        },
        securityEvents: this.securityEvents,
        flows: this.ipData.flows,
        contactedServers: this.ipData.contactedServers,
        tcpStats: this.ipData.tcpStats,
        timestamp: new Date().toISOString()
      };
      
      // 创建并下载JSON文件
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      
      const exportFileDefaultName = `ipv6-${this.ipData.ipAddress.split(':').pop()}-analysis.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
    }
  }
}
</script>

<style scoped>
.ipv6-address-analysis {
  background-color: #f5f5f5;
  min-height: 100%;
}

.address-card {
  transition: box-shadow 0.3s;
}

.address-card:hover {
  box-shadow: 0 6px 16px rgba(0,0,0,0.1) !important;
}

.primary-address {
  word-break: break-all;
}

.secondary-address {
  word-break: break-all;
}

.traffic-chart {
  background-color: #fafafa;
  border-radius: 8px;
  overflow: hidden;
  padding: 16px;
}

.chart-area {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: white;
}

.time-card {
  transition: all 0.2s;
  border-radius: 4px;
}

.time-card:hover {
  background-color: #e0e0e0 !important;
}

.legend-item {
  display: flex;
  align-items: center;
}

.security-metrics {
  height: 100%;
}
</style> 