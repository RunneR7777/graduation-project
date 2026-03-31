import request from './request';

const dashboard = {

    
    // 获取主机流量分布饼图数据
    getTopHostsChart() {
        return request.get('/dashboard/top-hosts-chart');
    },
    
    // 获取应用协议分布饼图数据
    getTopAppsChart() {
        return request.get('/dashboard/top-apps-chart');
    },
    
    // 获取流量安全分类饼图数据
    getTrafficClassChart() {
        return request.get('/dashboard/traffic-class-chart');
    },
    
    // 获取主机详细列表数据
    getTopHostsList() {
        return request.get('/dashboard/top-hosts-list');
    },
    
    // 获取前缀分布数据
    getTopPrefixesChart() {
        return request.get('/dashboard/top-prefixes-chart');
    }
};

export default dashboard;
