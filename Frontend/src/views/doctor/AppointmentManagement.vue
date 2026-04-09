<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useMedicalStore } from '../../stores/medical'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const medicalStore = useMedicalStore()

const sidebarCollapsed = ref(true)
const isMobile = ref(window.innerWidth < 768)

const activeTab = ref('appointments')

const menuItems = ref([
    { label: '工作台', icon: 'HomeFilled', active: false, route: '/doctor/workspace' },
    { label: '患者管理', icon: 'User', active: false, route: '/doctor/patients' },
    { label: '挂号预约', icon: 'Calendar', active: true, route: '/doctor/appointments' },
    { label: '个人中心', icon: 'Setting', active: false, route: '/doctor/profile' }
])

const tabs = [
    { key: 'appointments', label: '预约订单管理', icon: 'List' },
    { key: 'schedule', label: '出诊设置', icon: 'Setting' },
    { key: 'slots', label: '号源管理', icon: 'DataLine' }
]

const appointmentFilter = ref('today')

const appointments = computed(() => medicalStore.appointments)

const filteredAppointments = computed(() => {
    const today = new Date().toISOString().split('T')[0]
    const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0]
    
    let result = appointments.value
    
    if (appointmentFilter.value === 'today') {
        result = result.filter(a => a.appointmentDate === today || a.appointmentDate === '2026-04-09')
    } else if (appointmentFilter.value === 'tomorrow') {
        result = result.filter(a => a.appointmentDate === tomorrow || a.appointmentDate === '2026-04-10')
    }
    
    return result
})

const scheduleSettings = ref({
    morningStart: '08:00',
    morningEnd: '12:00',
    afternoonStart: '14:00',
    afternoonEnd: '17:30',
    slotDuration: 30,
    slotsPerPeriod: 10,
    workingDays: [1, 2, 3, 4, 5]
})

const scheduleDates = computed(() => {
    const dates = []
    const storeSlots = medicalStore.scheduleSlots
    for (const [date, slots] of Object.entries(storeSlots)) {
        dates.push({
            date,
            morning: slots.morning,
            afternoon: slots.afternoon,
            status: 'normal'
        })
    }
    return dates.sort((a, b) => a.date.localeCompare(b.date))
})

const slotStats = computed(() => {
    const total = scheduleDates.value.reduce((sum, d) => sum + d.morning.total + d.afternoon.total, 0)
    const booked = scheduleDates.value.reduce((sum, d) => sum + d.morning.booked + d.afternoon.booked, 0)
    const available = total - booked
    return { total, booked, available }
})

const getStatusTag = (status) => {
    const statusMap = {
        'pending': { type: 'warning', text: '待确认' },
        'confirmed': { type: 'primary', text: '已确认' },
        'completed': { type: 'success', text: '已就诊' },
        'cancelled': { type: 'info', text: '已取消' }
    }
    return statusMap[status] || { type: 'info', text: '未知' }
}

const getDateStatusTag = (status) => {
    const statusMap = {
        'normal': { type: 'success', text: '正常' },
        'suspended': { type: 'warning', text: '停诊' },
        'holiday': { type: 'info', text: '休假' }
    }
    return statusMap[status] || { type: 'info', text: '未知' }
}

const handleMenuClick = (index) => {
    menuItems.value.forEach((item, i) => {
        item.active = i === index
    })
    const route = menuItems.value[index].route
    if (route) {
        router.push(route)
    }
}

const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
}

const handleResize = () => {
    isMobile.value = window.innerWidth < 768
    if (isMobile.value) {
        sidebarCollapsed.value = true
    } else {
        sidebarCollapsed.value = false
    }
}

const confirmAppointment = (appointment) => {
    medicalStore.updateAppointmentStatus(appointment.id, 'confirmed')
    ElMessage.success('预约已确认')
}

const cancelAppointment = (appointment) => {
    medicalStore.updateAppointmentStatus(appointment.id, 'cancelled')
    ElMessage.warning('预约已取消')
}

const markCompleted = (appointment) => {
    medicalStore.updateAppointmentStatus(appointment.id, 'completed')
    ElMessage.success('已标记为就诊完成')
}

const toggleDateStatus = (dateItem) => {
    const statusOrder = ['normal', 'suspended', 'holiday']
    const currentIndex = statusOrder.indexOf(dateItem.status)
    dateItem.status = statusOrder[(currentIndex + 1) % statusOrder.length]
}

const addSlots = (dateItem, period) => {
    medicalStore.updateScheduleSlots(dateItem.date, period, 2)
}

const reduceSlots = (dateItem, period) => {
    const slot = period === 'morning' ? dateItem.morning : dateItem.afternoon
    if (slot.total > 0) {
        medicalStore.updateScheduleSlots(dateItem.date, period, -1)
    }
}

const showMedicalRecordDialog = ref(false)
const currentAppointment = ref(null)
const medicalRecordForm = ref({
    patientId: '',
    patientName: '',
    patientAge: '',
    patientGender: '',
    currentSymptoms: '',
    preliminaryDiagnosis: '',
    examinations: [],
    prescription: [],
    advice: ''
})

const examinationOptions = [
    '血常规',
    '尿常规',
    '肝功能',
    '肾功能',
    '血糖',
    '血脂',
    '心电图',
    '胸部X光',
    '腹部B超',
    '心脏彩超',
    '头颅CT',
    '头颅MRI',
    '胃镜',
    '肠镜'
]

const openMedicalRecordDialog = (appointment) => {
    currentAppointment.value = appointment
    medicalRecordForm.value = {
        patientId: appointment.id,
        patientName: appointment.patientName,
        patientAge: '',
        patientGender: '',
        currentSymptoms: appointment.symptoms,
        preliminaryDiagnosis: '',
        examinations: [],
        prescription: [],
        advice: ''
    }
    showMedicalRecordDialog.value = true
}

const addPrescriptionItem = () => {
    medicalRecordForm.value.prescription.push({
        name: '',
        spec: '',
        usage: '',
        days: 7
    })
}

const removePrescriptionItem = (index) => {
    medicalRecordForm.value.prescription.splice(index, 1)
}

const saveMedicalRecord = () => {
    if (!medicalRecordForm.value.preliminaryDiagnosis) {
        ElMessage.warning('请填写初步诊断')
        return
    }
    
    medicalStore.addMedicalRecord(currentAppointment.value.patientId, {
        department: '内科',
        doctor: authStore.doctor?.username || '医生',
        diagnosis: medicalRecordForm.value.preliminaryDiagnosis,
        currentSymptoms: medicalRecordForm.value.currentSymptoms,
        examinations: medicalRecordForm.value.examinations,
        prescription: medicalRecordForm.value.prescription,
        advice: medicalRecordForm.value.advice
    })
    
    medicalStore.updateAppointmentStatus(currentAppointment.value.id, 'completed')
    
    ElMessage.success('病历已保存')
    showMedicalRecordDialog.value = false
}

onMounted(() => {
    window.addEventListener('resize', handleResize)
    handleResize()
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="workspace">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, 'mobile-open': !sidebarCollapsed && isMobile }">
      <div class="card logo-card">
        <div class="logo-icon">
          <el-icon><FirstAidKit /></el-icon>
        </div>
        <span v-if="!sidebarCollapsed" class="logo-text">医生工作站</span>
        <button v-if="isMobile && !sidebarCollapsed" class="close-sidebar-btn" @click="toggleSidebar">
          <el-icon><Close /></el-icon>
        </button>
      </div>

      <div v-if="!sidebarCollapsed" class="card nav-card">
        <div
          v-for="(item, index) in menuItems"
          :key="item.label"
          class="nav-item"
          :class="{ active: item.active }"
          @click="handleMenuClick(index)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </div>
      </div>

      <div class="card user-card" @click="handleMenuClick(3)">
        <div class="user-avatar">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div v-if="!sidebarCollapsed" class="user-info">
          <div class="user-name">{{ authStore.doctor?.username || '医生姓名' }}</div>
          <div class="user-role">主治医师</div>
        </div>
      </div>
    </aside>

    <div v-if="isMobile && !sidebarCollapsed" class="sidebar-overlay" @click="toggleSidebar"></div>

    <main class="main-content">
      <div class="card welcome-bar">
        <div class="welcome-left">
          <button v-if="isMobile" class="menu-btn" @click="toggleSidebar">
            <el-icon><Fold /></el-icon>
          </button>
          <span class="welcome-text">挂号预约</span>
        </div>
        <div class="welcome-actions">
          <span class="date-display">{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}</span>
        </div>
      </div>

      <div class="content-grid">
        <div class="tabs-wrapper">
          <div 
            v-for="tab in tabs" 
            :key="tab.key"
            class="tab-item"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            <el-icon><component :is="tab.icon" /></el-icon>
            <span>{{ tab.label }}</span>
          </div>
        </div>

        <div v-if="activeTab === 'appointments'" class="tab-content card">
          <div class="section-header">
            <div class="filter-group">
              <el-radio-group v-model="appointmentFilter" size="default">
                <el-radio-button label="today">今日预约</el-radio-button>
                <el-radio-button label="tomorrow">明日预约</el-radio-button>
                <el-radio-button label="all">全部预约</el-radio-button>
              </el-radio-group>
            </div>
            <div class="stats-info">
              <span class="stat-item">待确认: {{ appointments.filter(a => a.status === 'pending').length }}</span>
              <span class="stat-item">已确认: {{ appointments.filter(a => a.status === 'confirmed').length }}</span>
              <span class="stat-item">已就诊: {{ appointments.filter(a => a.status === 'completed').length }}</span>
            </div>
          </div>

          <el-table :data="filteredAppointments" style="width: 100%">
            <el-table-column prop="patientName" label="患者姓名" width="100" align="center">
              <template #default="{ row }">
                <span class="patient-name">{{ row.patientName }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="patientPhone" label="联系电话" width="120" align="center" />
            <el-table-column prop="appointmentDate" label="预约日期" width="110" align="center" />
            <el-table-column prop="appointmentTime" label="预约时段" width="110" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.period === '上午' ? 'primary' : 'success'">
                  {{ row.appointmentTime }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="symptoms" label="症状描述" min-width="180">
              <template #default="{ row }">
                <span class="symptoms-text">{{ row.symptoms }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="getStatusTag(row.status).type" size="small">
                  {{ getStatusTag(row.status).text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" align="center" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button 
                    v-if="row.status === 'pending'" 
                    type="primary" 
                    link 
                    size="small" 
                    @click="confirmAppointment(row)"
                  >确认</el-button>
                  <el-button 
                    v-if="row.status === 'confirmed'" 
                    type="success" 
                    link 
                    size="small" 
                    @click="markCompleted(row)"
                  >已就诊</el-button>
                  <el-button 
                    v-if="row.status === 'pending' || row.status === 'confirmed'" 
                    type="danger" 
                    link 
                    size="small" 
                    @click="cancelAppointment(row)"
                  >取消</el-button>
                  <el-button 
                    type="primary" 
                    link 
                    size="small" 
                    @click="openMedicalRecordDialog(row)"
                  >写病历</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="activeTab === 'schedule'" class="tab-content card">
          <div class="section-header">
            <div class="section-title">出诊时间设置</div>
          </div>

          <div class="schedule-form">
            <div class="form-row">
              <div class="form-item">
                <label>上午时段</label>
                <div class="time-range">
                  <el-time-select
                    v-model="scheduleSettings.morningStart"
                    start="06:00"
                    step="00:30"
                    end="12:00"
                    placeholder="开始时间"
                  />
                  <span class="separator">至</span>
                  <el-time-select
                    v-model="scheduleSettings.morningEnd"
                    start="06:00"
                    step="00:30"
                    end="12:00"
                    placeholder="结束时间"
                  />
                </div>
              </div>
              <div class="form-item">
                <label>下午时段</label>
                <div class="time-range">
                  <el-time-select
                    v-model="scheduleSettings.afternoonStart"
                    start="12:00"
                    step="00:30"
                    end="22:00"
                    placeholder="开始时间"
                  />
                  <span class="separator">至</span>
                  <el-time-select
                    v-model="scheduleSettings.afternoonEnd"
                    start="12:00"
                    step="00:30"
                    end="22:00"
                    placeholder="结束时间"
                  />
                </div>
              </div>
            </div>

            <div class="form-row">
              <div class="form-item">
                <label>每时段时长（分钟）</label>
                <el-input-number v-model="scheduleSettings.slotDuration" :min="10" :max="60" :step="5" />
              </div>
              <div class="form-item">
                <label>每时段号源数量</label>
                <el-input-number v-model="scheduleSettings.slotsPerPeriod" :min="1" :max="20" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-item full-width">
                <label>出诊日期</label>
                <el-checkbox-group v-model="scheduleSettings.workingDays">
                  <el-checkbox :label="1">周一</el-checkbox>
                  <el-checkbox :label="2">周二</el-checkbox>
                  <el-checkbox :label="3">周三</el-checkbox>
                  <el-checkbox :label="4">周四</el-checkbox>
                  <el-checkbox :label="5">周五</el-checkbox>
                  <el-checkbox :label="6">周六</el-checkbox>
                  <el-checkbox :label="0">周日</el-checkbox>
                </el-checkbox-group>
              </div>
            </div>

            <div class="form-actions">
              <el-button type="primary">保存设置</el-button>
            </div>
          </div>

          <div class="section-header" style="margin-top: 24px;">
            <div class="section-title">停诊/休假设置</div>
          </div>

          <el-table :data="scheduleDates" style="width: 100%">
            <el-table-column prop="date" label="日期" width="120" align="center" />
            <el-table-column label="上午号源" align="center">
              <template #default="{ row }">
                <div class="slot-info">
                  <span>总数: {{ row.morning.total }}</span>
                  <span>已约: {{ row.morning.booked }}</span>
                  <span class="available">剩余: {{ row.morning.available }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="下午号源" align="center">
              <template #default="{ row }">
                <div class="slot-info">
                  <span>总数: {{ row.afternoon.total }}</span>
                  <span>已约: {{ row.afternoon.booked }}</span>
                  <span class="available">剩余: {{ row.afternoon.available }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getDateStatusTag(row.status).type" size="small">
                  {{ getDateStatusTag(row.status).text }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" align="center">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="toggleDateStatus(row)">
                  切换状态
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div v-if="activeTab === 'slots'" class="tab-content card">
          <div class="section-header">
            <div class="section-title">号源统计</div>
          </div>

          <div class="stats-cards">
            <div class="stat-card">
              <div class="stat-icon total">
                <el-icon><DataLine /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ slotStats.total }}</div>
                <div class="stat-label">总号源</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon booked">
                <el-icon><User /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ slotStats.booked }}</div>
                <div class="stat-label">已预约</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon available">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ slotStats.available }}</div>
                <div class="stat-label">剩余号源</div>
              </div>
            </div>
          </div>

          <div class="section-header" style="margin-top: 24px;">
            <div class="section-title">号源调整</div>
          </div>

          <el-table :data="scheduleDates" style="width: 100%">
            <el-table-column prop="date" label="日期" width="120" align="center" />
            <el-table-column label="上午号源" align="center">
              <template #default="{ row }">
                <div class="slot-control">
                  <el-button size="small" @click="reduceSlots(row, 'morning')">-</el-button>
                  <span class="slot-number">{{ row.morning.available }}/{{ row.morning.total }}</span>
                  <el-button size="small" @click="addSlots(row, 'morning')">+</el-button>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="下午号源" align="center">
              <template #default="{ row }">
                <div class="slot-control">
                  <el-button size="small" @click="reduceSlots(row, 'afternoon')">-</el-button>
                  <span class="slot-number">{{ row.afternoon.available }}/{{ row.afternoon.total }}</span>
                  <el-button size="small" @click="addSlots(row, 'afternoon')">+</el-button>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="getDateStatusTag(row.status).type" size="small">
                  {{ getDateStatusTag(row.status).text }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </main>

    <el-dialog 
      v-model="showMedicalRecordDialog" 
      title="填写病历" 
      width="800px" 
      :close-on-click-modal="false"
    >
      <el-form :model="medicalRecordForm" label-width="100px">
        <div class="form-section">
          <div class="section-title">患者基本信息</div>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="姓名">
                <el-input v-model="medicalRecordForm.patientName" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="年龄">
                <el-input v-model="medicalRecordForm.patientAge" placeholder="请输入年龄" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="性别">
                <el-select v-model="medicalRecordForm.patientGender" placeholder="请选择" style="width: 100%">
                  <el-option label="男" value="男" />
                  <el-option label="女" value="女" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </div>

        <div class="form-section">
          <div class="section-title">就诊信息</div>
          <el-form-item label="当前症状" required>
            <el-input 
              v-model="medicalRecordForm.currentSymptoms" 
              type="textarea" 
              :rows="3" 
              placeholder="请描述患者当前症状..."
            />
          </el-form-item>
          <el-form-item label="初步诊断" required>
            <el-input 
              v-model="medicalRecordForm.preliminaryDiagnosis" 
              placeholder="请输入初步诊断结果"
            />
          </el-form-item>
        </div>

        <div class="form-section">
          <div class="section-title">
            <span>检查项目</span>
          </div>
          <el-form-item label="开具检查">
            <el-checkbox-group v-model="medicalRecordForm.examinations">
              <el-checkbox 
                v-for="exam in examinationOptions" 
                :key="exam" 
                :label="exam"
              >{{ exam }}</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </div>

        <div class="form-section">
          <div class="section-title">
            <span>处方用药</span>
            <el-button type="primary" size="small" @click="addPrescriptionItem" style="margin-left: 10px">
              添加药品
            </el-button>
          </div>
          <div v-if="medicalRecordForm.prescription.length > 0" class="prescription-list">
            <div v-for="(item, index) in medicalRecordForm.prescription" :key="index" class="prescription-item">
              <el-row :gutter="10">
                <el-col :span="8">
                  <el-input v-model="item.name" placeholder="药品名称" />
                </el-col>
                <el-col :span="4">
                  <el-input v-model="item.spec" placeholder="规格" />
                </el-col>
                <el-col :span="6">
                  <el-input v-model="item.usage" placeholder="用法用量" />
                </el-col>
                <el-col :span="4">
                  <el-input-number v-model="item.days" :min="1" :max="90" placeholder="天数" style="width: 100%" />
                </el-col>
                <el-col :span="2">
                  <el-button type="danger" size="small" @click="removePrescriptionItem(index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-col>
              </el-row>
            </div>
          </div>
          <div v-else class="empty-prescription">
            <span>暂无处方，点击上方"添加药品"按钮添加</span>
          </div>
        </div>

        <div class="form-section">
          <div class="section-title">医嘱</div>
          <el-form-item label="医嘱">
            <el-input 
              v-model="medicalRecordForm.advice" 
              type="textarea" 
              :rows="2" 
              placeholder="请输入医嘱..."
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="showMedicalRecordDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMedicalRecord">保存病历</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.workspace {
  width: 100%;
  height: 100vh;
  display: flex;
  background: #f0f2f5;
  overflow: hidden;
}

.card {
  background: linear-gradient(135deg, #f0f7ff, #cce5ff);
  border-radius: 25px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.sidebar {
  width: 260px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: transparent;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

.sidebar.collapsed {
  width: 80px;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    transform: translateX(-100%);
    width: 260px;
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .sidebar.collapsed {
    width: 260px;
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 999;
  }
}

.logo-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
  background: rgba(255,255,255,0.2);
  flex-shrink: 0;
}

.logo-text {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}

.close-sidebar-btn {
  margin-left: auto;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: rgba(255,255,255,0.2);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-card {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 14px;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #555;
}

.nav-item:hover {
  background: #ffffff;
}

.nav-item.active {
  background: linear-gradient(135deg, #4f8cff15, #6c5ce715);
  color: #4f8cff;
  font-weight: 500;
}

.nav-item .el-icon {
  font-size: 18px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-top: auto;
}

.user-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  background: linear-gradient(135deg, #00b894, #00cec9);
  color: #fff;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.user-role {
  font-size: 13px;
  color: #999;
  margin-top: 1px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 20px;
  overflow: hidden;
}

.welcome-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
}

.welcome-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.welcome-text {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.welcome-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: #f5f7fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #555;
}

.date-display {
  font-size: 14px;
  color: #888;
}

.content-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.tabs-wrapper {
  display: flex;
  gap: 8px;
  padding: 8px;
  background: #fff;
  border-radius: 12px;
  flex-shrink: 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.tab-item:hover {
  background: #f5f7fa;
}

.tab-item.active {
  background: linear-gradient(135deg, #4f8cff, #6c5ce7);
  color: #fff;
}

.tab-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: #fff;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  padding-left: 12px;
  border-left: 3px solid #4f8cff;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-info {
  display: flex;
  gap: 16px;
}

.stats-info .stat-item {
  font-size: 13px;
  color: #909399;
}

.patient-name {
  font-weight: 500;
  color: #333;
}

.symptoms-text {
  font-size: 13px;
  color: #606266;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.schedule-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
}

.form-row {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.form-item {
  flex: 1;
}

.form-item.full-width {
  flex: none;
  width: 100%;
}

.form-item label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.time-range {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-range .separator {
  color: #909399;
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.slot-info {
  display: flex;
  gap: 12px;
  justify-content: center;
  font-size: 13px;
  color: #606266;
}

.slot-info .available {
  color: #67c23a;
  font-weight: 500;
}

.stats-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.total {
  background: #e6f7ff;
  color: #1890ff;
}

.stat-icon.booked {
  background: #fff7e6;
  color: #fa8c16;
}

.stat-icon.available {
  background: #f6ffed;
  color: #52c41a;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.slot-control {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.slot-number {
  min-width: 60px;
  text-align: center;
  font-weight: 500;
  color: #333;
}

.form-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.form-section .section-title {
  font-size: 15px;
  font-weight: 500;
  color: #333;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.prescription-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.prescription-item {
  padding: 10px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.empty-prescription {
  padding: 20px;
  text-align: center;
  color: #909399;
  background: #fff;
  border-radius: 6px;
  border: 1px dashed #dcdfe6;
}

@media (max-width: 768px) {
  .main-content {
    overflow-y: auto;
  }

  .welcome-bar {
    padding: 12px 16px;
  }

  .welcome-text {
    font-size: 16px;
  }

  .date-display {
    display: none;
  }

  .tabs-wrapper {
    overflow-x: auto;
    flex-wrap: nowrap;
  }

  .tab-item {
    padding: 8px 14px;
    white-space: nowrap;
  }

  .form-row {
    flex-direction: column;
    gap: 16px;
  }

  .stats-cards {
    flex-direction: column;
  }

  .stats-info {
    display: none;
  }
}
</style>
