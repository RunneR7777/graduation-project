<template>
  <div>
    <v-card-title>
      <v-list-item-action>
        <v-icon class="teal--text">mdi-api</v-icon>
      </v-list-item-action>
      <v-list-item-content class="ml-n3">
        <v-list-item-title class="teal--text">
          <span>API 文档</span>
        </v-list-item-title>
      </v-list-item-content>
    </v-card-title>

    <v-card class="mx-4 mb-4" outlined>
      <v-card-title class="headline">
        NetRiskRadar RESTful API 文档
        <v-chip class="ml-2" color="primary" small>v2.0</v-chip>
      </v-card-title>
      
      <v-divider></v-divider>
      
      <v-card-text>
        <p class="subtitle-1 mb-4">
          使用以下API可以获取网络分析平台的数据和功能
        </p>
        
        <v-select
          v-model="selectedScheme"
          :items="schemes"
          label="协议"
          class="mb-4"
          style="max-width: 200px"
          outlined
          dense
        ></v-select>
        
        <v-expansion-panels>
          <!-- 接口部分 -->
          <v-expansion-panel>
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <v-icon class="mr-2">mdi-lan</v-icon>
                <span class="font-weight-medium">接口 Interfaces</span>
                <span class="ml-2 grey--text text--darken-1">Everything about interfaces</span>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card flat>
                <v-card-text>
                  <p class="mb-2"><code>GET /api/v2/interfaces/list</code> - 获取所有网络接口列表</p>
                  <p class="mb-2"><code>GET /api/v2/interfaces/{ifid}/details</code> - 获取特定接口详情</p>
                  <p class="mb-2"><code>GET /api/v2/interfaces/{ifid}/stats</code> - 获取接口统计数据</p>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
          
          <!-- 主机部分 -->
          <v-expansion-panel>
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <v-icon class="mr-2">mdi-desktop-classic</v-icon>
                <span class="font-weight-medium">主机 Hosts</span>
                <span class="ml-2 grey--text text--darken-1">Everything about hosts</span>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card flat>
                <v-card-text>
                  <p class="mb-2"><code>GET /api/v2/hosts/list</code> - 获取所有主机列表</p>
                  <p class="mb-2"><code>GET /api/v2/hosts/{ip}/details</code> - 获取特定主机详情</p>
                  <p class="mb-2"><code>GET /api/v2/hosts/{ip}/traffic</code> - 获取主机流量数据</p>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
          
          <!-- 告警部分 -->
          <v-expansion-panel>
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <v-icon class="mr-2">mdi-alert</v-icon>
                <span class="font-weight-medium">告警 Alerts</span>
                <span class="ml-2 grey--text text--darken-1">Everything about alerts</span>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card flat>
                <v-card-text>
                  <p class="mb-2"><code>GET /api/v2/alerts/list</code> - 获取所有告警</p>
                  <p class="mb-2"><code>GET /api/v2/alerts/{id}/details</code> - 获取特定告警详情</p>
                  <p class="mb-2"><code>POST /api/v2/alerts/settings</code> - 更新告警设置</p>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
          
          <!-- 流量部分 -->
          <v-expansion-panel>
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <v-icon class="mr-2">mdi-swap-horizontal</v-icon>
                <span class="font-weight-medium">流量 Flows</span>
                <span class="ml-2 grey--text text--darken-1">Everything about flows</span>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card flat>
                <v-card-text>
                  <p class="mb-2"><code>GET /api/v2/flows/list</code> - 获取所有流量记录</p>
                  <p class="mb-2"><code>GET /api/v2/flows/stats</code> - 获取流量统计数据</p>
                  <p class="mb-2"><code>GET /api/v2/flows/top_talkers</code> - 获取主要流量源</p>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
          
          <!-- PCAP部分 -->
          <v-expansion-panel>
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <v-icon class="mr-2">mdi-file-document</v-icon>
                <span class="font-weight-medium">PCAP</span>
                <span class="ml-2 grey--text text--darken-1">Raw PCAP traffic</span>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card flat>
                <v-card-text>
                  <p class="mb-2"><code>GET /api/v2/pcap/capture</code> - 启动数据包捕获</p>
                  <p class="mb-2"><code>GET /api/v2/pcap/download/{id}</code> - 下载捕获的数据包</p>
                  <p class="mb-2"><code>DELETE /api/v2/pcap/{id}</code> - 删除捕获的数据包</p>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
          
          <!-- 用户部分 -->
          <v-expansion-panel>
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <v-icon class="mr-2">mdi-account</v-icon>
                <span class="font-weight-medium">用户 Users</span>
                <span class="ml-2 grey--text text--darken-1">User management</span>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card flat>
                <v-card-text>
                  <p class="mb-2"><code>GET /api/v2/users/list</code> - 获取所有用户</p>
                  <p class="mb-2"><code>POST /api/v2/users/create</code> - 创建新用户</p>
                  <p class="mb-2"><code>PUT /api/v2/users/{id}/update</code> - 更新用户信息</p>
                  <p class="mb-2"><code>DELETE /api/v2/users/{id}</code> - 删除用户</p>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
          
          <!-- 系统健康部分 -->
          <v-expansion-panel>
            <v-expansion-panel-header>
              <div class="d-flex align-center">
                <v-icon class="mr-2">mdi-heart-pulse</v-icon>
                <span class="font-weight-medium">健康状态 Health</span>
                <span class="ml-2 grey--text text--darken-1">Everything about system status</span>
              </div>
            </v-expansion-panel-header>
            <v-expansion-panel-content>
              <v-card flat>
                <v-card-text>
                  <p class="mb-2"><code>GET /api/v2/health/status</code> - 获取系统健康状态</p>
                  <p class="mb-2"><code>GET /api/v2/health/resources</code> - 获取资源使用情况</p>
                  <p class="mb-2"><code>GET /api/v2/health/logs</code> - 获取系统日志</p>
                </v-card-text>
              </v-card>
            </v-expansion-panel-content>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
export default {
  name: 'ApiDocumentation',
  data() {
    return {
      selectedScheme: 'HTTPS',
      schemes: ['HTTPS', 'HTTP'],
    }
  }
}
</script>

<style scoped>
code {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
}
</style> 