import request from './request';

const address = {
    // IPv6地址分析
    getIPv6AddressAnalysis(params) {
        return request.get('address/ipv6-analysis', { params });
    },
    
    // IPv6地址监控
    getIPv6AddressMonitoring(params) {
        return request.get('address/ipv6-monitoring', { params });
    },
    
    // 模式分析
    getPatternAnalysis(params) {
        return request.get('address/pattern-analysis', { params });
    },
    
    // 地址统计
    getAddressStatistics(params) {
        return request.get('address/statistics', { params });
    },
    
    // 活跃检测
    getActiveDetection(params) {
        return request.get('address/active-detection', { params });
    }
};

export default address; 