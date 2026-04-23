<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../../api/request'

const router = useRouter()
const appointments = ref([])
const doctorInvitations = ref([])
const departments = ref([])
const doctors = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const formLoading = ref(false)
const activeTab = ref('patient')

const form = ref({
    doctorId: '',
    doctorName: '',
    date: '',
    time: '',
    reason: ''
})

const fetchAppointments = async () => {
    loading.value = true
    try {
        const res = await request.get('/appointments')
        const all = res.data.appointments || []
        appointments.value = all.filter(a => a.appointment_type === 'patient')
        doctorInvitations.value = all.filter(a => a.appointment_type === 'doctor')
    } catch (err) {
        console.error('获取预约失败', err)
    } finally {
        loading.value = false
    }
}

const fetchDepartmentsAndDoctors = async () => {
    try {
        const [deptRes, docRes] = await Promise.all([
            request.get('/department/list'),
            request.get('/appointments/doctors')
        ])
        departments.value = deptRes.data || []
        doctors.value = docRes.data || []
    } catch (err) {
        console.error('获取科室/医生列表失败', err)
    }
}

const goBack = () => {
    router.push({ name: 'ai-chat' })
}

const openNewAppointmentDialog = () => {
    form.value = {
        doctorId: '',
        doctorName: '',
        date: '',
        time: '',
        reason: ''
    }
    dialogVisible.value = true
}

const onDoctorChange = (doctorId) => {
    const doc = doctors.value.find(d => d.id === doctorId)
    form.value.doctorName = doc ? doc.name : ''
}

const handleCreate = async () => {
    if (!form.value.doctorId || !form.value.date || !form.value.time) {
        alert('请选择医生、日期和时间')
        return
    }

    formLoading.value = true
    try {
        const params = new URLSearchParams()
        params.append('appointment_type', 'patient')
        params.append('appointment_date', form.value.date)
        params.append('appointment_time', form.value.time)
        params.append('reason', form.value.reason || '')
        params.append('doctor_id', form.value.doctorId)

        await request.post('/appointments', params)
        dialogVisible.value = false
        alert('预约成功')
        await fetchAppointments()
    } catch (err) {
        console.error('创建预约失败', err)
        alert('创建预约失败，请重试')
    } finally {
        formLoading.value = false
    }
}

const confirmInvitation = async (id) => {
    try {
        const params = new URLSearchParams()
        params.append('status', 'confirmed')
        await request.put(`/appointments/${id}/status`, params)
        await fetchAppointments()
    } catch (err) {
        console.error('确认预约失败', err)
        alert('操作失败')
    }
}

const cancelAppointment = async (id) => {
    if (!confirm('确定要取消这个预约吗？')) return
    try {
        await request.delete(`/appointments/${id}`)
        await fetchAppointments()
    } catch (err) {
        console.error('取消预约失败', err)
        alert('操作失败')
    }
}

const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]}`
}

const getStatusText = (status) => {
    const statusMap = {
        'pending': '待就诊',
        'completed': '已完成',
        'cancelled': '已取消',
        'confirmed': '已确认'
    }
    return statusMap[status] || status
}

onMounted(() => {
    fetchAppointments()
    fetchDepartmentsAndDoctors()
})
</script>

<template>
  <div class="appointment-page">
    <header class="page-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </button>
      <h1 class="page-title">挂号预约</h1>
      <button class="new-appointment-btn-header" @click="openNewAppointmentDialog">
        <el-icon><Plus /></el-icon>
        <span>新增预约</span>
      </button>
    </header>

    <main class="page-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="animate-spin text-4xl"><Loading /></el-icon>
        <p class="mt-4">正在加载...</p>
      </div>

      <div v-else class="appointments-container">
        <div class="tabs">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'patient' }"
            @click="activeTab = 'patient'"
          >
            我的预约
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'doctor' }"
            @click="activeTab = 'doctor'"
          >
            医生邀请
          </button>
        </div>

        <div v-if="activeTab === 'patient'" class="tab-content">
          <div v-if="appointments.length === 0" class="empty-state">
            <el-icon class="text-5xl"><Calendar /></el-icon>
            <p class="mt-4">暂无预约记录</p>
            <p class="empty-hint">点击右上角 + 按钮新建预约</p>
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
                  <span>患者预约</span>
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

                <div v-if="appointment.reason" class="appointment-reason">
                  <span class="reason-label">预约原因：</span>
                  <span>{{ appointment.reason }}</span>
                </div>
              </div>

              <div v-if="appointment.status === 'pending'" class="appointment-actions">
                <button class="action-btn cancel-btn" @click="cancelAppointment(appointment.id)">
                  取消预约
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'doctor'" class="tab-content">
          <div v-if="doctorInvitations.length === 0" class="empty-state">
            <el-icon class="text-5xl"><Bell /></el-icon>
            <p class="mt-4">暂无医生邀请</p>
          </div>

          <div v-else class="appointments-list">
            <div
              v-for="invitation in doctorInvitations"
              :key="invitation.id"
              class="appointment-card doctor-invitation"
            >
              <div class="appointment-header">
                <div class="appointment-type">
                  <el-icon class="type-icon"><User /></el-icon>
                  <span>医生邀请</span>
                </div>
                <span
                  class="appointment-status"
                  :class="{
                    'status-pending': invitation.status === 'pending',
                    'status-confirmed': invitation.status === 'confirmed'
                  }"
                >
                  {{ getStatusText(invitation.status) }}
                </span>
              </div>

              <div class="appointment-body">
                <div class="appointment-info">
                  <div class="info-item">
                    <el-icon><OfficeBuilding /></el-icon>
                    <span>{{ invitation.department }}</span>
                  </div>
                  <div class="info-item">
                    <el-icon><User /></el-icon>
                    <span>{{ invitation.doctor }}</span>
                  </div>
                </div>

                <div class="appointment-time">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatDate(invitation.date) }} {{ invitation.time }}</span>
                </div>

                <div v-if="invitation.reason" class="appointment-reason">
                  <span class="reason-label">邀请原因：</span>
                  <span>{{ invitation.reason }}</span>
                </div>
              </div>

              <div v-if="invitation.status === 'pending'" class="appointment-actions">
                <button class="action-btn confirm-btn" @click="confirmInvitation(invitation.id)">
                  确认预约
                </button>
                <button class="action-btn cancel-btn" @click="cancelAppointment(invitation.id)">
                  婉拒
                </button>
              </div>
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

    <el-dialog
      v-model="dialogVisible"
      title="新建预约"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="医生">
          <el-select v-model="form.doctorId" placeholder="请选择医生" style="width: 100%" @change="onDoctorChange">
            <el-option v-for="doc in doctors" :key="doc.id" :label="`${doc.name} (${doc.department_name || doc.title || '医生'})`" :value="doc.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期">
          <el-date-picker
            v-model="form.date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="时间">
          <el-select v-model="form.time" placeholder="请选择时间" style="width: 100%">
            <el-option label="09:00" value="09:00" />
            <el-option label="09:30" value="09:30" />
            <el-option label="10:00" value="10:00" />
            <el-option label="10:30" value="10:30" />
            <el-option label="11:00" value="11:00" />
            <el-option label="14:00" value="14:00" />
            <el-option label="14:30" value="14:30" />
            <el-option label="15:00" value="15:00" />
            <el-option label="15:30" value="15:30" />
            <el-option label="16:00" value="16:00" />
          </el-select>
        </el-form-item>

        <el-form-item label="预约原因">
          <el-input v-model="form.reason" type="textarea" placeholder="请输入预约原因（选填）" rows="3" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="formLoading">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.appointment-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #e8f4ff 0%, #ffffff 50%, #e8f4ff 100%);
}

.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.5);
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

.new-appointment-btn-header {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    border-radius: 20px;
    border: none;
    background: linear-gradient(135deg, #4f8cff 0%, #6c5ce7 100%);
    color: #fff;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
}

.new-appointment-btn-header:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(79, 140, 255, 0.35);
}

.new-appointment-btn-header .el-icon {
    font-size: 16px;
}

.tabs {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 4px;
    border-radius: 10px;
}

.tab-btn {
    flex: 1;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #666;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.tab-btn.active {
    background: #fff;
    color: #4f8cff;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.tab-content {
    min-height: 300px;
}

.appointment-reason {
    margin-top: 12px;
    padding: 10px 12px;
    background: #f5f5f5;
    border-radius: 8px;
    font-size: 14px;
    color: #666;
}

.reason-label {
    font-weight: 500;
    color: #333;
}

.confirm-btn {
    background: #4f8cff;
    color: #fff;
}

.confirm-btn:hover {
    background: #3d7ae8;
}

.status-confirmed {
    background: #d4edda;
    color: #155724;
}

.doctor-invitation {
    border-left: 4px solid #4f8cff;
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

.empty-hint {
    font-size: 13px;
    color: #bbb;
    margin-top: 8px;
}

.appointments-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.appointment-card {
    padding: 20px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
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
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
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
    content: '\2022';
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
