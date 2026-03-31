import request from './request'

const setting = {
    // 获取系统设置
    getSystemSettings() {
        return request.get('/api/settings/system');
    },
    
    // 更新系统设置
    updateSystemSettings(params) {
        return request.post('/api/settings/system', params);
    },
    
    // 获取用户设置
    getUserSettings() {
        return request.get('/api/settings/user');
    },
    
    // 更新用户设置
    updateUserSettings(params) {
        return request.post('/api/settings/user', params);
    }
};

export default setting; 