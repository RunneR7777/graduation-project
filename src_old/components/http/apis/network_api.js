import request from './request'

// 网络流量API基础地址配置
// const API_BASE_URL = 'http://10.3.242.4:5000/api';

const network = {
    // 网络流量分析接口
    getTrafficList(params) {
        return request.get('/network/traffic', { params });
    },
    
    // 流量详情
    getFlowDetail(id) {
        return request.get(`/network/traffic/flow/${id}`);
    },
    
    // IPv6分析
    getIPv6Analysis() {
        return request.get('/network/ipv6/analysis');
    },
    
    // 活跃IP分析
    getActiveIPAnalysis() {
        return request.get('/network/active-ip/analysis');
    },
    
    // IP地理位置分析
    getIPGeoData() {
        return request.get('/network/ip-geo/data');
    },
    
    // 实时IP地理位置
    getIPGeoRealtime() {
        return request.get('/network/ip-geo/realtime');
    },
    
    // 特定位置详情
    getIPGeoLocationDetail(location) {
        return request.get(`/network/ip-geo/location/${location}`);
    },

    // 获取流量统计
    getTrafficStats() {
        return request.get("/network/traffic/stats");
    },

    // IPv6风险分析接口
    getIPv6List(params) {
        return request.get("/network/ipv6/list", { params });
    },
    getIPv6Detail(address) {
        return request.get(`/network/ipv6/detail/${address}`);
    },
    getIPv6Stats() {
        return request.get("/network/ipv6/stats");
    },
    enableIPv6Privacy(params) {
        return request.post("/network/ipv6/privacy/enable", params);
    },

    // IP地理位置分布接口
    getIPGeoTrend(params) {
        return request.get("/network/geo/trend", { params });
    },

    // 端口风险分析接口
    getPortRiskList() {
        return request.get("/network/port/risk/list");
    },
    getPortRiskDetail(port) {
        return request.get(`/network/port/risk/detail/${port}`);
    },

    // 检查API健康状态
    checkHealth() {
        return request.get("/network/health");
    },

    // 进站流量接口
    getInboundTraffic(params) {
        return request.get('/network/traffic/inbound', { params });
    },

    // 出站流量接口
    getOutboundTraffic(params) {
        return request.get('/network/traffic/outbound', { params });
    },

    // 危险流量接口
    getRiskTraffic(params) {
        return request.get('/network/traffic/risk', { params });
    }
};



export default network; 