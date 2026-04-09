import { defineStore } from 'pinia'

export const useMedicalStore = defineStore('medical', {
    state: () => ({
        patients: [
            { id: '1', name: '张三', age: 45, gender: '男', phone: '138****1234', lastVisit: '2026-04-09', status: 'in_progress', diagnosis: '高血压' },
            { id: '2', name: '李四', age: 32, gender: '女', phone: '139****5678', lastVisit: '2026-04-08', status: 'pending', diagnosis: '糖尿病' },
            { id: '3', name: '王五', age: 58, gender: '男', phone: '137****9012', lastVisit: '2026-04-07', status: 'completed', diagnosis: '冠心病' },
            { id: '4', name: '赵六', age: 28, gender: '女', phone: '136****3456', lastVisit: '2026-04-06', status: 'pending', diagnosis: '胃炎' },
            { id: '5', name: '钱七', age: 65, gender: '男', phone: '135****7890', lastVisit: '2026-04-05', status: 'completed', diagnosis: '关节炎' }
        ],
        appointments: [
            {
                id: 1,
                patientId: '1',
                patientName: '张三',
                patientPhone: '138****1234',
                patientAge: 45,
                patientGender: '男',
                appointmentDate: '2026-04-09',
                appointmentTime: '09:00-09:30',
                period: '上午',
                status: 'pending',
                symptoms: '头晕、头痛3天，血压偏高',
                createTime: '2026-04-08 14:30'
            },
            {
                id: 2,
                patientId: '2',
                patientName: '李四',
                patientPhone: '139****5678',
                patientAge: 32,
                patientGender: '女',
                appointmentDate: '2026-04-09',
                appointmentTime: '09:30-10:00',
                period: '上午',
                status: 'confirmed',
                symptoms: '胸闷、心悸1周',
                createTime: '2026-04-08 10:15'
            },
            {
                id: 3,
                patientId: '3',
                patientName: '王五',
                patientPhone: '137****9012',
                patientAge: 58,
                patientGender: '男',
                appointmentDate: '2026-04-09',
                appointmentTime: '10:00-10:30',
                period: '上午',
                status: 'completed',
                symptoms: '咳嗽、咳痰5天',
                createTime: '2026-04-07 16:20'
            },
            {
                id: 4,
                patientId: '4',
                patientName: '赵六',
                patientPhone: '136****3456',
                patientAge: 28,
                patientGender: '女',
                appointmentDate: '2026-04-10',
                appointmentTime: '14:00-14:30',
                period: '下午',
                status: 'pending',
                symptoms: '胃痛、反酸2周',
                createTime: '2026-04-08 18:45'
            },
            {
                id: 5,
                patientId: '5',
                patientName: '钱七',
                patientPhone: '135****7890',
                patientAge: 65,
                patientGender: '男',
                appointmentDate: '2026-04-10',
                appointmentTime: '15:00-15:30',
                period: '下午',
                status: 'cancelled',
                symptoms: '关节疼痛1月',
                createTime: '2026-04-06 09:00'
            }
        ],
        medicalRecords: {
            '1': [
                {
                    id: 1,
                    date: '2026-04-09',
                    type: '复诊',
                    source: 'patient',
                    department: '心血管内科',
                    doctor: '王医生',
                    diagnosis: '高血压2级',
                    currentSymptoms: '头晕、头痛',
                    examinations: ['血压测量', '心电图'],
                    prescription: [
                        { name: '硝苯地平缓释片', spec: '30mg', usage: '每日1次，每次1片', days: 30 },
                        { name: '阿司匹林肠溶片', spec: '100mg', usage: '每日1次，每次1片', days: 30 }
                    ],
                    advice: '低盐低脂饮食，定期监测血压，适量运动'
                },
                {
                    id: 2,
                    date: '2026-03-15',
                    type: '初诊',
                    source: 'patient',
                    department: '心血管内科',
                    doctor: '王医生',
                    diagnosis: '高血压1级',
                    currentSymptoms: '头晕',
                    examinations: ['血压测量'],
                    prescription: [
                        { name: '硝苯地平缓释片', spec: '30mg', usage: '每日1次，每次1片', days: 15 }
                    ],
                    advice: '注意休息，避免情绪激动，一周后复查'
                }
            ],
            '2': [
                {
                    id: 1,
                    date: '2026-04-08',
                    type: '初诊',
                    source: 'patient',
                    department: '内分泌科',
                    doctor: '李医生',
                    diagnosis: '糖尿病',
                    currentSymptoms: '多饮、多尿',
                    examinations: ['血糖', '糖化血红蛋白'],
                    prescription: [
                        { name: '二甲双胍片', spec: '0.5g', usage: '每日2次，每次1片', days: 30 }
                    ],
                    advice: '控制饮食，适量运动，定期监测血糖'
                }
            ],
            '3': [],
            '4': [],
            '5': []
        },
        scheduleSlots: {
            '2026-04-09': {
                morning: { total: 10, booked: 3, available: 7 },
                afternoon: { total: 8, booked: 2, available: 6 }
            },
            '2026-04-10': {
                morning: { total: 10, booked: 5, available: 5 },
                afternoon: { total: 8, booked: 4, available: 4 }
            },
            '2026-04-11': {
                morning: { total: 10, booked: 0, available: 10 },
                afternoon: { total: 8, booked: 0, available: 8 }
            },
            '2026-04-12': {
                morning: { total: 10, booked: 0, available: 10 },
                afternoon: { total: 8, booked: 0, available: 8 }
            },
            '2026-04-13': {
                morning: { total: 10, booked: 0, available: 10 },
                afternoon: { total: 8, booked: 0, available: 8 }
            }
        }
    }),
    getters: {
        getPatientById: (state) => (id) => {
            return state.patients.find(p => p.id === id)
        },
        getAppointmentsByPatientId: (state) => (patientId) => {
            return state.appointments.filter(a => a.patientId === patientId)
        },
        getMedicalRecordsByPatientId: (state) => (patientId) => {
            return state.medicalRecords[patientId] || []
        },
        getAvailableSlots: (state) => (date, period) => {
            const daySlots = state.scheduleSlots[date]
            if (!daySlots) return 0
            return period === 'morning' ? daySlots.morning.available : daySlots.afternoon.available
        },
        getTodayAppointments: (state) => {
            const today = new Date().toISOString().split('T')[0]
            return state.appointments.filter(a => a.appointmentDate === today || a.appointmentDate === '2026-04-09')
        },
        getTomorrowAppointments: (state) => {
            const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0]
            return state.appointments.filter(a => a.appointmentDate === tomorrow || a.appointmentDate === '2026-04-10')
        }
    },
    actions: {
        addAppointment(appointment) {
            const newId = Math.max(...this.appointments.map(a => a.id), 0) + 1
            const newAppointment = {
                id: newId,
                ...appointment,
                status: 'pending',
                createTime: new Date().toLocaleString('zh-CN')
            }
            this.appointments.push(newAppointment)
            
            const patient = this.patients.find(p => p.id === appointment.patientId)
            if (patient && patient.status === 'completed') {
                patient.status = 'pending'
            }
            
            const dateSlots = this.scheduleSlots[appointment.appointmentDate]
            if (dateSlots) {
                const period = appointment.period === '上午' ? 'morning' : 'afternoon'
                if (dateSlots[period].available > 0) {
                    dateSlots[period].available -= 1
                    dateSlots[period].booked += 1
                }
            }
            
            return newAppointment
        },
        
        updateAppointmentStatus(appointmentId, status) {
            const appointment = this.appointments.find(a => a.id === appointmentId)
            if (appointment) {
                appointment.status = status
                
                if (status === 'completed') {
                    const patient = this.patients.find(p => p.id === appointment.patientId)
                    if (patient) {
                        patient.status = 'completed'
                        patient.lastVisit = appointment.appointmentDate
                    }
                }
            }
        },
        
        addMedicalRecord(patientId, record) {
            if (!this.medicalRecords[patientId]) {
                this.medicalRecords[patientId] = []
            }
            const newId = Math.max(...this.medicalRecords[patientId].map(r => r.id), 0) + 1
            const newRecord = {
                id: newId,
                date: new Date().toISOString().split('T')[0],
                type: '门诊',
                source: 'doctor',
                ...record
            }
            this.medicalRecords[patientId].unshift(newRecord)
            
            const patient = this.patients.find(p => p.id === patientId)
            if (patient) {
                patient.diagnosis = record.diagnosis
            }
            
            return newRecord
        },
        
        updatePatientInfo(patientId, info) {
            const patient = this.patients.find(p => p.id === patientId)
            if (patient) {
                Object.assign(patient, info)
            }
        },
        
        updateScheduleSlots(date, period, change) {
            if (!this.scheduleSlots[date]) {
                this.scheduleSlots[date] = {
                    morning: { total: 10, booked: 0, available: 10 },
                    afternoon: { total: 8, booked: 0, available: 8 }
                }
            }
            const slot = this.scheduleSlots[date][period]
            slot.total += change
            slot.available += change
        }
    }
})
