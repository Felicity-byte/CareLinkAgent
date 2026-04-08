<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../../api/request'

const router = useRouter()
const appointments = ref([])
const loading = ref(true)

const fetchAppointments = async () => {
    loading.value = true
    try {
        const res = await request.get('/appointments')
        appointments.value = res.data.appointments || []
    } catch (err) {
        console.error('Fetch appointments failed', err)
        appointments.value = [
            {
                id: '1',
                department: '内科',
                doctor: '张医生',
                date: '2024-01-20',
                time: '09:30',
                status: 'pending',
                type: '复诊'
            },
            {
                id: '2',
                department: '外科',
                doctor: '李医生',
                date: '2024-01-15',
                time: '14:00',
                status: 'completed',
                type: '复诊'
            }
        ]
    } finally {
        loading.value = false
    }
}

const goBack = () => {
    router.push({ name: 'patient-home' })
}

const createAppointment = () => {
    router.push({ name: 'patient-home' })
}

const cancelAppointment = async (id) => {
    if (confirm('确定要取消这个预约吗？')) {
        try {
            await request.delete(`/appointments/${id}`)
            appointments.value = appointments.value.filter(a => a.id !== id)
        } catch (err) {
            console.error('取消预约失败', err)
            alert('取消预约失败，请重试')
        }
    }
}

const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]}`
}

const getStatusText = (status) => {
    const statusMap = {
        'pending': '待就诊',
        'completed': '已完成',
        'cancelled': '已取消'
    }
    return statusMap[status] || status
}

onMounted(() => {
    fetchAppointments()
})
</script>

<template>
  <div class="appointment-page">
    <header class="page-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </button>
      <h1 class="page-title">复查预约</h1>
      <div class="header-right"></div>
    </header>

    <main class="page-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="animate-spin text-4xl"><Loading /></el-icon>
        <p class="mt-4">正在加载...</p>
      </div>

      <div v-else class="appointments-container">
        <div class="section-header">
          <h2>我的预约</h2>
          <button class="new-appointment-btn" @click="createAppointment">
            <el-icon><Plus /></el-icon>
            <span>新建预约</span>
          </button>
        </div>

        <div v-if="appointments.length === 0" class="empty-state">
          <el-icon class="text-5xl"><Calendar /></el-icon>
          <p class="mt-4">暂无预约记录</p>
          <p class="text-sm text-gray-400 mt-2">完成问诊后可预约复查</p>
        </div>

        <div v-else class="appointments-list">
          <div 
            v-for="appointment in appointments" 
            :key="appointment.id" 
            class="appointment-card"
            :class="{ 'completed': appointment.status === 'completed' }"
          >
            <div class="appointment-header">
              <div class="appointment-type">
                <el-icon class="type-icon"><Calendar /></el-icon>
                <span>{{ appointment.type }}</span>
              </div>
              <span 
                class="appointment-status"
                :class="{
                  'status-pending': appointment.status === 'pending',
                  'status-completed': appointment.status === 'completed',
                  'status-cancelled': appointment.status === 'cancelled'
                }"
              >
                {{ getStatusText(appointment.status) }}
              </span>
            </div>

            <div class="appointment-body">
              <div class="appointment-info">
                <div class="info-item">
                  <el-icon><OfficeBuilding /></el-icon>
                  <span>{{ appointment.department }}</span>
                </div>
                <div class="info-item">
                  <el-icon><User /></el-icon>
                  <span>{{ appointment.doctor }}</span>
                </div>
              </div>

              <div class="appointment-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatDate(appointment.date) }} {{ appointment.time }}</span>
              </div>
            </div>

            <div v-if="appointment.status === 'pending'" class="appointment-actions">
              <button class="action-btn cancel-btn" @click="cancelAppointment(appointment.id)">
                取消预约
              </button>
              <button class="action-btn modify-btn">
                修改时间
              </button>
            </div>
          </div>
        </div>

        <div class="tips-section">
          <h3>预约须知</h3>
          <ul>
            <li>请提前15分钟到达诊室报到</li>
            <li>如需取消预约，请提前24小时操作</li>
            <li>复查时请携带之前的检查报告</li>
            <li>如有疑问请联系导诊台</li>
          </ul>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.appointment-page {
    min-height: 100vh;
    background: #fff;
}

.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: #fff;
    border-bottom: 1px solid #e5e5e5;
    position: sticky;
    top: 0;
    z-index: 10;
}

.back-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #666;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.back-btn:hover {
    background: #f5f5f5;
    color: #333;
}

.back-btn .el-icon {
    font-size: 20px;
}

.page-title {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
}

.header-right {
    width: 80px;
}

.page-content {
    padding: 24px;
    max-width: 900px;
    margin: 0 auto;
}

.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    color: #999;
}

.appointments-container {
    max-width: 900px;
    margin: 0 auto;
}

.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}

.section-header h2 {
    font-size: 20px;
    font-weight: 600;
    color: #1a1a1a;
}

.new-appointment-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: #4f8cff;
    color: #fff;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.new-appointment-btn:hover {
    background: #3d7ae8;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    color: #999;
}

.appointments-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.appointment-card {
    padding: 20px;
    border-radius: 16px;
    background: #fff;
    border: 1px solid #e5e5e5;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: all 0.2s;
}

.appointment-card:hover {
    border-color: #4f8cff;
    box-shadow: 0 4px 12px rgba(79, 140, 255, 0.1);
}

.appointment-card.completed {
    opacity: 0.7;
}

.appointment-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.appointment-type {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
}

.type-icon {
    font-size: 20px;
    color: #4f8cff;
}

.appointment-status {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}

.status-pending {
    background: #fff3cd;
    color: #856404;
}

.status-completed {
    background: #d4edda;
    color: #155724;
}

.status-cancelled {
    background: #f8d7da;
    color: #721c24;
}

.appointment-body {
    margin-bottom: 16px;
}

.appointment-info {
    display: flex;
    gap: 24px;
    margin-bottom: 12px;
}

.info-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    color: #666;
}

.info-item .el-icon {
    font-size: 18px;
    color: #999;
}

.appointment-time {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 15px;
    font-weight: 500;
    color: #1a1a1a;
    padding: 12px;
    background: #f5f5f5;
    border-radius: 8px;
}

.appointment-time .el-icon {
    font-size: 20px;
    color: #4f8cff;
}

.appointment-actions {
    display: flex;
    gap: 12px;
    padding-top: 16px;
    border-top: 1px solid #e5e5e5;
}

.action-btn {
    flex: 1;
    padding: 10px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.cancel-btn {
    background: #fff;
    border: 1px solid #e5e5e5;
    color: #666;
}

.cancel-btn:hover {
    background: #f5f5f5;
    border-color: #ff4757;
    color: #ff4757;
}

.modify-btn {
    background: #4f8cff;
    color: #fff;
}

.modify-btn:hover {
    background: #3d7ae8;
}

.tips-section {
    margin-top: 32px;
    padding: 20px;
    background: #f5f5f5;
    border-radius: 12px;
}

.tips-section h3 {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 12px;
}

.tips-section ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.tips-section li {
    position: relative;
    padding-left: 16px;
    font-size: 13px;
    color: #666;
    line-height: 2;
}

.tips-section li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: #4f8cff;
}

@media (max-width: 768px) {
    .page-header {
        padding: 12px 16px;
    }
    
    .page-content {
        padding: 16px;
    }
    
    .appointment-info {
        flex-direction: column;
        gap: 8px;
    }
    
    .header-right {
        width: 60px;
    }
}
</style>
