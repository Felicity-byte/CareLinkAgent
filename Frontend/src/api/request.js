import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const service = axios.create({
    baseURL: '/api',
    timeout: 120000
})

let isRefreshing = false
let refreshSubscribers = []

function subscribeTokenRefresh(callback) {
    refreshSubscribers.push(callback)
}

function onTokenRefreshed(token) {
    refreshSubscribers.forEach(callback => callback(token))
    refreshSubscribers = []
}

// Request interceptor
service.interceptors.request.use(
    (config) => {
        const authStore = useAuthStore()
        if (authStore.token) {
            config.headers['Authorization'] = `Bearer ${authStore.token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor
service.interceptors.response.use(
    (response) => {
        const res = response.data
        if (res.base && res.base.code !== '10000') {
            console.error('Error:', res.base.msg)

            if (res.base.code === '401' || res.base.code === '10003') {
                const authStore = useAuthStore()
                authStore.logout()
                location.reload()
            }

            return Promise.reject(new Error(res.base.msg || 'Error'))
        } else {
            return res
        }
    },
    async (error) => {
        const authStore = useAuthStore()
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                return new Promise((resolve) => {
                    subscribeTokenRefresh((token) => {
                        originalRequest.headers['Authorization'] = `Bearer ${token}`
                        resolve(service(originalRequest))
                    })
                })
            }

            originalRequest._retry = true
            isRefreshing = true

            try {
                const success = await authStore.refreshToken()
                if (success) {
                    const newToken = authStore.token
                    onTokenRefreshed(newToken)
                    originalRequest.headers['Authorization'] = `Bearer ${newToken}`
                    return service(originalRequest)
                } else {
                    authStore.logout()
                    location.reload()
                }
            } catch (err) {
                authStore.logout()
                location.reload()
            } finally {
                isRefreshing = false
            }
        }

        return Promise.reject(error)
    }
)

export default service
