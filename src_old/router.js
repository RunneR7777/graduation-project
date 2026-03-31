import Vue from 'vue'
import Router from 'vue-router'

import DashboardLayout from "./layout/DashboardLayout";
import ChatAILayout from "./layout/ChatAILayout";
import Login from "./views/Login";
import ChatAI from "./views/chatai/ChatAI";
import Dashboard from "./views/dashboard/Dashboard";
import Temp from "./views/Temp";
import Settings from "./views/setting/Settings";

import NetworkTraffic from "./views/network/traffic/NetworkTraffic";
import ActiveIPAnalysis from "./views/network/ActiveIPAnalysis";
import IPGeoMap from "./views/network/IPGeoMap";
import FlowDetail from "./views/network/FlowDetail";
import InboundTraffic from "./views/network/traffic/InboundTraffic";
import OutboundTraffic from "./views/network/traffic/OutboundTraffic";
import RiskTraffic from "./views/network/traffic/RiskTraffic";

import PortRisk from "./views/risk/PortRisk";
import ApiDocumentation from "./views/developer/ApiDocumentation";

import PatternAnalysis from "./views/address/PatternAnalysis.vue";
import IPv6AddressMonitoring from "./views/address/IPv6AddressMonitoring.vue";
import IPv6AddressAnalysis from "./views/address/IPv6AddressAnalysis.vue";

import AsDistribution from "./views/hosts/AsDistribution.vue";
import CountryDistribution from "./views/hosts/CountryDistribution.vue";
import RemoteHosts from "./views/hosts/RemoteHosts";
import RiskHosts from "./views/hosts/RiskHosts";
import HostBasedTraffic from "./views/hosts/HostBasedTraffic.vue";



import AddressStatistics from "./views/address/AddressStatistics";

const routerPush = Router.prototype.push;
Router.prototype.push = function push(location) {
  return routerPush.call(this, location).catch(error=> error)
};

Vue.use(Router);

export default new Router({
  linkExactActiveClass: 'active',
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
      component: DashboardLayout,
      children: [
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: Dashboard
        },{
          path: '/temp',
          name: 'Temp',
          component: Temp
        },{
          path: '/settings',
          name: 'Settings',
          component: Settings
        },
        {
          path: '/network/traffic',
          name: 'NetworkTraffic',
          component: NetworkTraffic
        },
        {
          path: '/network/ipv6',
          name: 'IPv6Analysis',
          component: ActiveIPAnalysis
        },
        {
          path: '/network/geo',
          name: 'IPGeoMap',
          component: IPGeoMap
        },
        {
          path: '/network/traffic/flow/:id',
          name: 'FlowDetail',
          component: FlowDetail
        },
        
        {
          path: '/risk/ports',
          name: 'PortRisk',
          component: PortRisk
        },
        {
          path: '/risk/ipv6-monitoring',
          name: 'IPv6AddressMonitoring',
          component: IPv6AddressMonitoring,
          meta: { title: 'IPv6地址监控', icon: 'mdi-ip-network' }
        },
        
        {
          path: '/developer/api',
          name: 'api-documentation',
          component: ApiDocumentation
        },
        {
          path: '/address/address-monitoring',
          name: 'IPv6AddressMonitoring',
          component: IPv6AddressMonitoring
        },
        {
          path: '/address/pattern-analysis',
          name: 'PatternAnalysis',
          component: PatternAnalysis,
          meta: {
            title: 'IPv6活跃地址生成',
            requiresAuth: true
          }
        },
        {
          path: '/address/active-detection',
          name: 'IPv6AddressAnalysis',
          component: IPv6AddressAnalysis,
          props: route => ({ ipAddress: route.query.ipAddress || route.query.address }),
          meta: {
            title: 'IPv6地址分析',
            requiresAuth: true
          }
        },
        
        {
          path: '/hosts/as-distribution',
          name: 'AsDistribution',
          component: AsDistribution,
          meta: {
            title: 'AS分布统计',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/country-distribution',
          name: 'CountryDistribution',
          component: CountryDistribution,
          meta: {
            title: '国家分布统计',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/host-based',
          name: 'HostBasedTraffic',
          component: HostBasedTraffic,
          meta: {
            title: '基于主机的流量分析',
            requiresAuth: true
          }
        },
        {
          path: '/network/traffic/inbound',
          name: 'InboundTraffic',
          component: InboundTraffic,
          meta: {
            title: '进站流量',
            requiresAuth: true
          }
        },
        {
          path: '/network/traffic/outbound',
          name: 'OutboundTraffic',
          component: OutboundTraffic,
          meta: {
            title: '出站流量',
            requiresAuth: true
          }
        },
        {
          path: '/network/traffic/risk',
          name: 'RiskTraffic',
          component: RiskTraffic,
          meta: {
            title: '危险流量',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/remote-hosts',
          name: 'RemoteHosts',
          component: RemoteHosts,
          meta: {
            title: '远端主机',
            requiresAuth: true
          }
        },
        {
          path: '/hosts/risk-hosts',
          name: 'RiskHosts',
          component: RiskHosts,
          meta: {
            title: '危险主机',
            requiresAuth: true
          }
        },
        {
          path: '/address/statistics',
          name: 'AddressStatistics',
          component: AddressStatistics,
          meta: {
            title: 'IPv6地址统计',
            requiresAuth: true
          }
        }
      ]
    },
    {
      path: '/chatai',
      component: ChatAILayout,
      children: [
        {
          path: '',  // 确保根路径匹配
          name: 'ChatAI',
          component: ChatAI,
          meta: {
            title: 'ChatAI 智能分析',
            requiresAuth: true
          }
        }
      ]
    },
    {
      path: '/login',
      component: Login
    }
  ]
});
