import { defineStore } from 'pinia'
import request from '../api/request'
import { useAuthStore } from './auth'

export const usePatientStore = defineStore('patient', {
    state: () => ({
        patients: [],
        loading: false,
        error: null,
        currentPatient: null
    }),
    actions: {
        async fetchQueue() {
            this.loading = true
            this.error = null
            const authStore = useAuthStore()

            try {
                const res = await request.get('/doctor/patients')
                if (res.base && res.base.code === '10000') {
                    this.patients = res.data || []
                }
            } catch (err) {
                console.error('Fetch patients failed:', err)
                this.error = err.message || '获取患者列表失败'
            } finally {
                this.loading = false
            }
        },

        async registerPatient(phone_number, password, username) {
            try {
                const formData = new URLSearchParams()
                formData.append('phone_number', phone_number)
                formData.append('password', password)
                formData.append('username', username)

                const res = await request.post('/doctor/patient/register', formData, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                })

                if (res.base && res.base.code === '10000') {
                    await this.fetchQueue()
                    return { success: true, ...res.data }
                }
                return { success: false, msg: res.base?.msg }
            } catch (err) {
                console.error('Register patient failed:', err)
                throw err
            }
        },

        async bindPatient(phone_number) {
            try {
                const formData = new URLSearchParams()
                formData.append('phone_number', phone_number)

                const res = await request.post('/doctor/patient/bind', formData, {
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
                })

                if (res.base && res.base.code === '10000') {
                    await this.fetchQueue()
                    return true
                }
                return false
            } catch (err) {
                console.error('Bind patient failed:', err)
                throw err
            }
        },

        async submitDiagnosis(recordId, text) {
            try {
                await request.post('/doctor/report', {
                    record_id: recordId,
                    text: text
                })
                return true
            } catch (err) {
                console.error('Submit report failed', err)
                throw err
            }
        }
    }
})
