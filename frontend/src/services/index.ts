// 统一导出所有API服务
export { networkServices as networkApi } from './network'
export { analyticsServices as analyticsApi } from './analytics'
export { chartServices as chartsApi } from './charts'
export { chataiApi } from './chataiApi'
export { authApi } from './authApi'
export { settingApi } from './settingApi'

export { default as request } from './request'

// 服务器地址配置
let SERVER_ADDRESS = import.meta.env.VITE_API_BASE_URL
if (!SERVER_ADDRESS) {
    SERVER_ADDRESS = window.location.protocol + "//" + window.location.host
}

// Token管理工具
const getToken = () => localStorage.getItem('access_token')
const setToken = (token: string) => localStorage.setItem('access_token', token)
const removeToken = () => localStorage.removeItem('access_token')

export {
    SERVER_ADDRESS,
    getToken,
    setToken,
    removeToken
}

