import request from './request';

const hosts = {
    // AS分布分析
    getAsDistribution() {
        return request.get('/as-distribution');
    },
    
    // 国家分布分析
    getCountryDistribution() {
        return request.get('/country-distribution');
    },
    
    // 基于主机的流量分析
    getHostBasedTraffic(params) {
        // 使用调试日志
        // console.log('调用API /host，参数:', params);
        return request.get('/host', { params });
    },
    
    // 远程主机分析
    getRemoteHosts(params) {
        console.log('调用远端主机API，参数:', params);
        const { params: queryParams } = params;
        console.log('解析后的查询参数:', queryParams);
        return request.get('/remote-host', { params: queryParams });
    },
    
    // 风险主机分析
    getRiskHosts(params) {
        return request.get('/risk-hosts', { params });
    }
};

export default hosts; 