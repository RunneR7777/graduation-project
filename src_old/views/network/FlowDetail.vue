<template>
  <div>
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-transit-connection-variant</v-icon>
      <span class="text-h6">Flow: {{ flowId }}</span>
      <v-spacer></v-spacer>
      <v-btn icon :to="'/network/traffic'">
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
    </v-card-title>
    
    <v-card class="mx-4 mb-4" outlined>
      <v-card-text>
        <v-row>
          <v-col cols="12">
            <v-data-table
              :headers="flowHeaders"
              :items="flowData"
              hide-default-header
              hide-default-footer
              class="elevation-1"
              disable-sort
              disable-pagination
            >
              <template v-slot:item="{ item }">
                <tr>
                  <td width="20%" class="font-weight-medium">{{ item.name }}</td>
                  <td>
                    <div v-if="item.type === 'peer'">
                      <div class="d-flex align-center">
                        <span>{{ item.source }}</span>
                        <v-chip x-small class="mx-2" color="red">{{ item.sourcePort }}</v-chip>
                        <v-icon small>mdi-swap-horizontal</v-icon>
                        <v-chip x-small class="mx-2" color="blue">{{ item.destPort }}</v-chip>
                        <span>{{ item.destination }}</span>
                      </div>
                    </div>
                    <div v-else-if="item.type === 'protocol'">
                      <span>{{ item.protocol }} / {{ item.application }}</span>
                      <v-chip v-if="item.confidence" small color="green" class="ml-2">{{ item.confidence }}</v-chip>
                    </div>
                    <div v-else-if="item.type === 'time'" class="d-flex justify-space-between">
                      <div>
                        <span>{{ item.firstSeen }}</span>
                        <span class="grey--text">[{{ item.firstAge }} ago]</span>
                      </div>
                      <div>
                        <span>{{ item.lastSeen }}</span>
                        <span class="grey--text">[{{ item.lastAge }} ago]</span>
                      </div>
                    </div>
                    <div v-else-if="item.type === 'traffic'" class="d-flex justify-space-between">
                      <div>
                        <span>Total: {{ item.total }}</span>
                      </div>
                      <div>
                        <v-chip color="primary" x-small>{{ item.percentage }}</v-chip>
                        <v-icon small color="success" v-if="item.direction === 'up'">mdi-arrow-up</v-icon>
                      </div>
                    </div>
                    <div v-else-if="item.type === 'packets'" class="d-flex justify-space-between">
                      <div>
                        <span>Client → Server: {{ item.clientToServer }}</span>
                      </div>
                      <div>
                        <span>Client ← Server: {{ item.clientFromServer }}</span>
                      </div>
                    </div>
                    <div v-else-if="item.type === 'latency'">
                      <span>{{ item.value }} ms</span>
                    </div>
                    <div v-else-if="item.type === 'packetTime'" class="d-flex justify-space-between">
                      <div>
                        <span>Client → Server: {{ item.clientToServer }}</span>
                      </div>
                      <div>
                        <span>Client ← Server: {{ item.serverToClient }}</span>
                      </div>
                    </div>
                    <div v-else-if="item.type === 'tcpState'" class="d-flex align-center">
                      <div>
                        <span>Client → Server:</span>
                        <v-chip v-for="flag in item.clientFlags" 
                               :key="flag" 
                               x-small 
                               class="mx-1" 
                               :color="getFlagColor(flag)">
                          {{ flag }}
                        </v-chip>
                      </div>
                      <v-spacer></v-spacer>
                      <div>
                        <span>Client ← Server:</span>
                        <v-chip v-for="flag in item.serverFlags" 
                               :key="flag" 
                               x-small 
                               class="mx-1" 
                               :color="getFlagColor(flag)">
                          {{ flag }}
                        </v-chip>
                      </div>
                    </div>
                    <div v-else-if="item.type === 'http'" class="d-flex justify-space-between">
                      <span>{{ item.method }}</span>
                      <span>{{ item.url }}</span>
                    </div>
                    <div v-else-if="item.type === 'agent'">
                      <span>{{ item.value }}</span>
                    </div>
                    <div v-else-if="item.type === 'throughput'" class="d-flex align-center">
                      <span>{{ item.actual }} bps — / {{ item.average }} bps / {{ item.peak }} kbps</span>
                    </div>
                    <div v-else-if="item.type === 'asn'" class="d-flex justify-space-between">
                      <div>
                        <span>{{ item.client }}</span>
                      </div>
                      <div>
                        <span>{{ item.server }}</span>
                      </div>
                    </div>
                    <div v-else>
                      <span>{{ item.value }}</span>
                    </div>
                  </td>
                </tr>
              </template>
            </v-data-table>
          </v-col>
        </v-row>
        
        <v-row v-if="payloadData">
          <v-col cols="12">
            <v-card outlined>
              <v-card-title class="py-2">
                <span>HTTP Payload</span>
              </v-card-title>
              <v-card-text>
                <v-textarea
                  outlined
                  readonly
                  :value="payloadData"
                  rows="10"
                  class="font-monospace"
                ></v-textarea>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'FlowDetail',
  data() {
    return {
      flowId: this.$route.params.id || '2001:da8:215:8f02:4c9d:57cb:9f0f:5d06:36376',
      flowHeaders: [
        { text: 'Parameter', value: 'name', width: '20%' },
        { text: 'Value', value: 'value', width: '80%' }
      ],
      flowData: [
        { 
          name: 'Flow Peers [ Client / Server ]', 
          type: 'peer',
          source: '2001:da8:215:8f02:4c9d:57cb:9f0f:5d06',
          sourcePort: '36376',
          destination: 'tiebapic.baidu.com',
          destPort: '80'
        },
        {
          name: 'Protocol / Application',
          type: 'protocol',
          protocol: 'TCP',
          application: 'HTTP (Web)',
          confidence: '99'
        },
        {
          name: 'First / Last Seen',
          type: 'time',
          firstSeen: '04/03/2025 00:50:02',
          firstAge: '00:37 sec',
          lastSeen: '04/03/2025 00:50:20',
          lastAge: '00:19 sec'
        },
        {
          name: 'Flow Duration',
          type: 'duration',
          value: '00:18 sec'
        },
        {
          name: 'Total Traffic',
          type: 'traffic',
          total: '22 KB',
          percentage: '89.8 %',
          direction: 'up'
        },
        {
          name: 'Packet Distribution',
          type: 'packets',
          clientToServer: '15 Pkts / 2.3 KB',
          clientFromServer: '16 Pkts / 19.8 KB'
        },
        {
          name: 'Application Latency',
          type: 'latency',
          value: '4.39'
        },
        {
          name: 'Packet Inter-Arrival Time',
          type: 'packetTime',
          clientToServer: '< 1 ms / 62.22 ms / 527 ms',
          serverToClient: '< 1 ms / 77.29 ms / 533 ms'
        },
        {
          name: 'TCP Flags and Connection State',
          type: 'tcpState',
          clientFlags: ['S', 'A', 'P'],
          serverFlags: ['A']
        },
        {
          name: 'HTTP Method',
          type: 'http',
          method: 'GET',
          url: 'tiebapic.baidu.com'
        },
        {
          name: 'User Agent',
          type: 'agent',
          value: 'tieba image flow version : 12.79.1.0 cuid : 5E235B5F943E8617DA57E884A5F2FC2BIVNOK36JET'
        },
        {
          name: 'URL',
          type: 'url',
          value: 'tiebapic.baidu.com/forum/w%3D720%3Bq%3D60%3Bg%3D0/sign=3e14567d9e1e9324fdc5eb0320a02d22c3fe49bc...'
        },
        {
          name: 'Actual / Peak / Average Throughput',
          type: 'throughput',
          actual: '0',
          average: '0',
          peak: '9.5'
        },
        {
          name: 'ASN [ Client / Server ]',
          type: 'asn',
          client: '24350 (CERNET2 IX at Beijing University of Posts and Telecommunications)',
          server: '4134 (Chinanet)'
        }
      ],
      payloadData: `GET /forum/w%3D720%3Bq%3D60%3Bg%3D0/sign=3e1456e9e160924idcf3af27c3fe49bc... HTTP/1.1
User-Agent: tieba image flow version : 12.79.1.0 cuid : 5E235B5F943E8617DA57E884A5F2FC2BIVNOK36JET
X-Bd-Traceid: c5132e16df1f4f6b5d0e4f5f6f5f65
Host: tiebapic.baidu.com
Connection: Keep-Alive
Accept-Encoding: gzip`
    };
  },
  methods: {
    getFlagColor(flag) {
      const colors = {
        'S': 'blue', // SYN
        'A': 'green', // ACK
        'P': 'orange', // PSH
        'F': 'red', // FIN
        'R': 'red-darken-2', // RST
        'U': 'purple' // URG
      };
      return colors[flag] || 'grey';
    }
  },
  mounted() {
    // 这里可以添加代码从API获取流量详情
    // this.fetchFlowDetail(this.flowId);
  }
};
</script>

<style scoped>
.font-monospace {
  font-family: monospace;
}
</style> 