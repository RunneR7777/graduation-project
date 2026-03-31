import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '@/layout/DashboardLayout.vue'
import ChatAILayout from '@/layout/ChatAILayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
      component: DashboardLayout,
      children: [
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/Dashboard.vue')
        },
        {
          path: '/temp',
          name: 'Temp',
          component: () => import('@/views/Temp.vue')
        },
        {
          path: '/settings',
          name: 'Settings',
          component: () => import('@/views/setting/Settings.vue')
        },
        // 网络流量分析路由
        {
          path: '/network/traffic',
          name: 'NetworkTraffic',
          component: () => import('@/views/network/traffic/NetworkTraffic.vue')
        },
        {
          path: '/network/traffic/inbound',
          name: 'InboundTraffic',
          component: () => import('@/views/network/traffic/InboundTraffic.vue')
        },
        {
          path: '/network/traffic/outbound',
          name: 'OutboundTraffic',
          component: () => import('@/views/network/traffic/OutboundTraffic.vue')
        },
        {
          path: '/network/traffic/risk',
          name: 'RiskTraffic',
          component: () => import('@/views/network/traffic/RiskTraffic.vue')
        },
        {
          path: '/network/ipv6',
          name: 'IPv6Analysis',
          component: () => import('@/views/network/ActiveIPAnalysis.vue')
        },
        {
          path: '/network/geo',
          name: 'IPGeoMap',
          component: () => import('@/views/network/IPGeoMap.vue')
        },
        {
          path: '/network/traffic/flow/:id',
          name: 'FlowDetail',
          component: () => import('@/views/network/FlowDetail.vue')
        },
        
        // 主机分析路由
        {
          path: '/hosts/host-based',
          name: 'HostBasedTraffic',
          component: () => import('@/views/hosts/HostBasedTraffic.vue'),
          meta: {
            title: '本地主机流量',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/remote-hosts',
          name: 'RemoteHosts',
          component: () => import('@/views/hosts/RemoteHosts.vue'),
          meta: {
            title: '远端主机',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/as-distribution',
          name: 'AsDistribution',
          component: () => import('@/views/hosts/AsDistribution.vue'),
          meta: {
            title: 'AS分布',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/country-distribution',
          name: 'CountryDistribution',
          component: () => import('@/views/hosts/CountryDistribution.vue'),
          meta: {
            title: '国家分布',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/risk-hosts',
          name: 'RiskHosts',
          component: () => import('@/views/hosts/RiskHosts.vue'),
          meta: {
            title: '危险主机',
            requiresAuth: true
          }
        },
        
        // 地址分析路由
        {
          path: '/address/active-detection',
          name: 'IPv6AddressAnalysis',
          component: () => import('@/views/address/IPv6AddressAnalysis.vue'),
          meta: {
            title: 'IPv6活跃地址检测',
            requiresAuth: true
          }
        },
        {
          path: '/address/pattern-analysis',
          name: 'PatternAnalysis',
          component: () => import('@/views/address/PatternAnalysis.vue'),
          meta: {
            title: 'IPv6活跃地址生成',
            requiresAuth: true
          }
        },
        {
          path: '/address/statistics',
          name: 'AddressStatistics',
          component: () => import('@/views/address/AddressStatistics.vue'),
          meta: {
            title: 'IPv6地址统计',
            requiresAuth: true
          }
        },
        
        // 风险分析路由
        {
          path: '/risk/ports',
          name: 'PortRisk',
          component: () => import('@/views/risk/PortRisk.vue')
        },
        
        // IPv6异常检测路由
        {
          path: '/anomaly/overview',
          name: 'DatasetOverview',
          component: () => import('@/views/anomaly/DatasetOverview.vue'),
          meta: {
            title: '数据集概览',
            requiresAuth: false
          }
        },
        {
          path: '/anomaly/dataset',
          name: 'AnomalyDataset',
          component: () => import('@/views/anomaly/DatasetManagement.vue'),
          meta: {
            title: '数据集管理',
            requiresAuth: false
          }
        },
        
        // 开发者路由
        {
          path: '/developer/api',
          name: 'api-documentation',
          component: () => import('@/views/developer/ApiDocumentation.vue')
        }
      ]
    },
    // ChatAI 路由
    {
      path: '/chatai',
      component: ChatAILayout,
      children: [
        {
          path: '',
          name: 'ChatAI',
          component: () => import('@/views/chatai/ChatAI.vue'),
          meta: {
            title: 'ChatAI 智能分析',
            requiresAuth: true
          }
        }
      ]
    },
    // 登录路由
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue')
    }
  ]
})

export default router

