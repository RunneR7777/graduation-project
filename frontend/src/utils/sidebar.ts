import type { SidebarItem } from '@/types/sidebar'

export default function (): SidebarItem[] {
    return [
        // { divider: true },
        { divider: true },
        { 
            group: true, 
            icon: 'mdi-ip-network', 
            text: '风险活跃地址分析',
            items: [
                // { text: '活跃地址检测', path: '/address/active-detection' },
                // { text: '地址统计', path: '/address/statistics' },
                { text: '生成模式分析', path: '/address/pattern-analysis' },
                // { text: '异常地址检测', path: '/address/address-monitoring' }
            ]
        },
        { divider: true },
        { 
            group: true, 
            icon: 'mdi-shield-search', 
            text: 'IPv6隐蔽信道',
            items: [
                { text: '数据集概览', path: '/anomaly/overview' },
                { text: '数据集管理', path: '/anomaly/dataset' }
            ]
        },


        { divider: true },
        { 
            group: true, 
            icon: 'mdi-chart-timeline-variant', 
            text: '风险流量分析',
            items: [
                { text: '所有流量', path: '/network/traffic' },
                { text: '进站流量', path: '/network/traffic/inbound' },
                { text: '出站流量', path: '/network/traffic/outbound' },
                { text: '危险流量', path: '/network/traffic/risk' },
            ]
        },
        
        { divider: true },
        { 
            group: true, 
            icon: 'mdi-server-network', 
            text: '风险主机分析',
            items: [
                { text: '本地主机', path: '/hosts/host-based' },
                { text: '远端主机', path: '/hosts/remote-hosts' },
                { text: '危险主机', path: '/hosts/risk-hosts' },
                { text: 'AS统计', path: '/hosts/as-distribution' },
                { text: '国家统计', path: '/hosts/country-distribution' }
            ]
        },
        

        
        // { divider: true },
        // { 
        //     group: true, 
        //     icon: 'mdi-shield-alert', 
        //     text: '风险暴露面分析',
        //     items: [
        //         { text: '端口风险', path: '/risk/ports' },
        //         { text: 'IP地理位置图', path: '/network/geo' }
        //     ]
        // },
        

        
        { divider: true },
        { header: true, text: "智能分析" },
        { dc: true, icon: 'mdi-robot', text: 'ChatAI 智能助手', path: '/chatai' },
        
        { divider: true },
        { header: true, text: "开发者" },
        { dc: true, icon: 'mdi-api', text: 'RESTful API', path: '/developer/api' },
    ]
}

