import request from './request';

const risk = {
    // 获取端口风险分析
    getPortRiskAnalysis() {
        return request.get('/risk/port/analysis');
    },
    
    // 获取特定端口的风险详情
    getPortRiskDetail(port) {
        return request.get(`/risk/port/detail/${port}`);
    },
    
    // 获取风险主机列表
    getRiskHosts(params) {
        return request.get('/risk/hosts', { params });
    },
    
    // 获取风险趋势
    getRiskTrend(params) {
        return request.get('/risk/trend', { params });
    }
};

export default risk; 