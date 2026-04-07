import { defineStore } from 'pinia'
import request from '../api/request'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('token') || '',
        refresh_token: localStorage.getItem('refresh_token') || '',
        doctor: JSON.parse(localStorage.getItem('doctor') || 'null'),
        user: JSON.parse(localStorage.getItem('user') || 'null'),
        role: localStorage.getItem('role') || ''
    }),
    getters: {
        isLoggedIn: (state) => !!state.token
    },
    actions: {
        setTokens(token, refreshToken) {
            this.token = token
            this.refresh_token = refreshToken
            localStorage.setItem('token', token)
            localStorage.setItem('refresh_token', refreshToken)
        },
        async refreshToken() {
            if (!this.refresh_token) return false
            try {
                const formData = new URLSearchParams()
                formData.append('refresh_token', this.refresh_token)

                const endpoint = this.role === 'patient' ? '/user/refresh' : '/doctor/refresh'
                const res = await request.post(endpoint, formData, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                })

                if (res.base && res.base.code === '10000') {
                    this.setTokens(res.data.token, res.data.refresh_token)
                    return true
                }
            } catch (error) {
                console.error('Token refresh failed:', error)
            }
            return false
        },
        // 医生登录
        async doctorLogin(username, password) {
            try {
                const res = await request.post('/doctor/login', null, {
                    params: { phone_number: username, password }
                })

                const data = res.data
                this.setTokens(data.token, data.refresh_token)
                this.doctor = data.doctor
                this.role = 'doctor'

                localStorage.setItem('doctor', JSON.stringify(this.doctor))
                localStorage.setItem('role', 'doctor')

                return true
            } catch (error) {
                console.error('Doctor login failed:', error)
                throw error
            }
        },
        // 患者登录
        async patientLogin(username, password) {
            try {
                const formData = new URLSearchParams()
                formData.append('phone_number', username)
                formData.append('password', password)

                const res = await request.post('/user/login', formData, {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                })

                const data = res.data
                this.setTokens(data.token, data.refresh_token)
                this.user = data.user
                this.role = 'patient'

                localStorage.setItem('user', JSON.stringify(this.user))
                localStorage.setItem('role', 'patient')

                return true
            } catch (error) {
                console.error('Patient login failed:', error)
                throw error
            }
        },
        // 统一登录方法 - 根据角色调用不同接口
        async login(username, password, role = 'doctor') {
            if (role === 'patient') {
                return await this.patientLogin(username, password)
            } else {
                return await this.doctorLogin(username, password)
            }
        },
        logout() {
            this.token = ''
            this.refresh_token = ''
            this.doctor = null
            this.user = null
            this.role = ''
            localStorage.removeItem('token')
            localStorage.removeItem('refresh_token')
            localStorage.removeItem('doctor')
            localStorage.removeItem('user')
            localStorage.removeItem('role')
        }
    }
})
