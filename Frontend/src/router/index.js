import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'login',
            component: () => import('../views/Landing.vue')
        },
        {
            path: '/login',
            redirect: '/'
        },
        {
            path: '/doctor/login',
            redirect: '/'
        },
        {
            path: '/patient/login',
            redirect: '/'
        },
        {
            path: '/doctor/workspace',
            name: 'workspace',
            component: () => import('../views/doctor/Workspace.vue'),
            meta: { requiresAuth: true, role: 'doctor' }
        },
        {
            path: '/doctor/dashboard',
            name: 'dashboard',
            redirect: '/doctor/workspace'
        },
        {
            path: '/doctor/patient/:id',
            name: 'patient-detail',
            component: () => import('../views/PatientDetail.vue'),
            meta: { requiresAuth: true, role: 'doctor' }
        },
        {
            path: '/patient/register',
            name: 'patient-register',
            component: () => import('../views/patient/Register.vue')
        },
        {
            path: '/patient/bind-info',
            name: 'patient-bind',
            component: () => import('../views/patient/BindInfo.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/patient/history',
            name: 'patient-history',
            component: () => import('../views/patient/HistoryList.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/patient/record/:id',
            name: 'record-detail',
            component: () => import('../views/patient/RecordDetail.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/patient/home',
            name: 'patient-home',
            component: () => import('../views/patient/Home.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/patient/departments',
            name: 'department-list',
            component: () => import('../views/patient/DepartmentList.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/patient/questionnaire/:deptId',
            name: 'questionnaire',
            component: () => import('../views/patient/Questionnaire.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/patient/chat',
            name: 'ai-chat',
            component: () => import('../views/patient/Chat.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/patient/appointment',
            name: 'patient-appointment',
            component: () => import('../views/patient/Appointment.vue'),
            meta: { requiresAuth: true, role: 'patient' }
        },
        {
            path: '/:pathMatch(.*)*',
            redirect: '/'
        }
    ]
})

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()

    if (to.meta.requiresAuth) {
        if (!authStore.isLoggedIn) {
            next({ name: 'login' })
            return
        }
    }

    next()
})

export default router
