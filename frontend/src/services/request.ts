import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { useRouter } from 'vue-router'

// API基础配置
// 开发环境和生产环境都使用相对路径，由Vite代理或Nginx处理
let API_PATH = "/api/"

// 创建axios实例
const request: AxiosInstance = axios.create({
    baseURL: API_PATH,
    timeout: 20000,
    withCredentials: false,
    headers: {
        'Content-Type': 'application/json'
    }
})




// 请求拦截器
request.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token')
        if (token) {
            config.headers['token'] = token
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
request.interceptors.response.use(
    (response: AxiosResponse) => {
        // 检查业务状态码（后端格式: { code, data, message }）
        if (response.data && response.data.code) {
            const statusCode = response.data.code
            if (statusCode === 10401) {
                window.localStorage.removeItem('access_token')
                // 动态导入消息工具以避免循环依赖
                import('@/utils/message').then(({ default: message }) => {
                    message.error('请求令牌已过期')
                })
                // 跳转到登录页
                window.location.href = '/login'
            }
        }
        return response
    },
    (error) => {
        // 动态导入消息工具
        import('@/utils/message').then(({ default: message }) => {
            if (error.response) {
                const statusCode = error.response.status
                if (statusCode === 401) {
                    window.localStorage.removeItem('access_token')
                    message.error('请求令牌已过期')
                    window.location.href = '/login'
                } else if (statusCode === 500) {
                    message.error('服务器内部错误')
                } else if (statusCode === 404) {
                    message.error('请求的资源不存在')
                } else if (statusCode === 403) {
                    message.error('没有访问权限')
                } else {
                    message.error(error.response.data?.message || '请求失败')
                }
            } else if (error.code === 'ECONNABORTED') {
                message.error('请求超时，请稍后重试')
            } else {
                message.error('网络连接异常，请检查网络')
            }
        })
        return Promise.reject(error.response ? error.response.data : error)
    }
)

export default request

// 通用API响应类型（匹配后端实际返回格式: { code, data, message }）
export interface ApiResponse<T = any> {
    code: number
    data: T
    message: string
}

