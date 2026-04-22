<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useMedicalStore } from '../../stores/medical'
import { ElMessage } from 'element-plus'
import request from '../../api/request'

const router = useRouter()
const authStore = useAuthStore()
const medicalStore = useMedicalStore()

const sidebarCollapsed = ref(true)
const showMobileMenu = ref(false)
const isMobile = ref(window.innerWidth < 768)

const welcomeText = ref('患者管理')

const notificationCount = ref(3)

const menuItems = ref([
    { label: '工作台', icon: 'HomeFilled', active: false, route: '/doctor/workspace' },
    { label: '患者管理', icon: 'User', active: true, route: '/doctor/patients' },
    { label: '挂号预约', icon: 'Calendar', active: false, route: '/doctor/appointments' },
    { label: '个人中心', icon: 'Setting', active: false, route: '/doctor/profile' }
])

const handleMenuClick = (index) => {
    menuItems.value.forEach((item, i) => {
        item.active = i === index
    })
    showMobileMenu.value = false
    if (isMobile.value) {
        sidebarCollapsed.value = true
    }
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

onMounted(() => {
    window.addEventListener('resize', handleResize)
    handleResize()
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
})

const searchQuery = ref('')
const statusFilter = ref('')

const statusOptions = [
    { label: '全部', value: '' },
    { label: '待就诊', value: 'pending' },
    { label: '就诊中', value: 'in_progress' },
    { label: '已完成', value: 'completed' }
]

const patients = computed(() => medicalStore.patients)

const filteredPatients = ref([...patients.value])

const handleSearch = () => {
    let result = [...patients.value]
    
    if (searchQuery.value) {
        result = result.filter(p => 
            p.name.includes(searchQuery.value) || 
            p.diagnosis.includes(searchQuery.value)
        )
    }
    
    if (statusFilter.value) {
        result = result.filter(p => p.status === statusFilter.value)
    }
    
    filteredPatients.value = result
}

const handleStatusChange = () => {
    handleSearch()
}

watch(patients, () => {
    handleSearch()
}, { deep: true })

const getStatusTag = (status) => {
    const statusMap = {
        'pending': { type: 'warning', text: '待就诊' },
        'in_progress': { type: 'primary', text: '就诊中' },
        'completed': { type: 'success', text: '已完成' }
    }
    return statusMap[status] || { type: 'info', text: '未知' }
}

const viewPatientDetail = (patient) => {
    router.push(`/doctor/patient/${patient.id}/detail`)
}

const showAppointmentDialog = ref(false)
const currentPatient = ref(null)
const appointmentForm = ref({
    patientId: '',
    patientName: '',
    appointmentDate: '',
    appointmentTime: '',
    period: 'morning',
    symptoms: ''
})

const timeSlots = [
    { value: '08:00-08:30', label: '08:00-08:30' },
    { value: '08:30-09:00', label: '08:30-09:00' },
    { value: '09:00-09:30', label: '09:00-09:30' },
    { value: '09:30-10:00', label: '09:30-10:00' },
    { value: '10:00-10:30', label: '10:00-10:30' },
    { value: '10:30-11:00', label: '10:30-11:00' },
    { value: '11:00-11:30', label: '11:00-11:30' },
    { value: '11:30-12:00', label: '11:30-12:00' },
    { value: '14:00-14:30', label: '14:00-14:30' },
    { value: '14:30-15:00', label: '14:30-15:00' },
    { value: '15:00-15:30', label: '15:00-15:30' },
    { value: '15:30-16:00', label: '15:30-16:00' },
    { value: '16:00-16:30', label: '16:00-16:30' },
    { value: '16:30-17:00', label: '16:30-17:00' },
    { value: '17:00-17:30', label: '17:00-17:30' }
]

const openAppointmentDialog = (patient) => {
    currentPatient.value = patient
    appointmentForm.value = {
        patientId: patient.id,
        patientName: patient.name,
        appointmentDate: '',
        appointmentTime: '',
        period: 'morning',
        symptoms: ''
    }
    showAppointmentDialog.value = true
}

const submitAppointment = () => {
    if (!appointmentForm.value.appointmentDate || !appointmentForm.value.appointmentTime) {
        ElMessage.warning('请选择预约日期和时段')
        return
    }
    
    const formattedDate = appointmentForm.value.appointmentDate instanceof Date 
        ? appointmentForm.value.appointmentDate.toISOString().split('T')[0]
        : appointmentForm.value.appointmentDate
    
    const availableSlots = medicalStore.getAvailableSlots(formattedDate, appointmentForm.value.period)
    if (availableSlots <= 0) {
        ElMessage.warning('该时段已无剩余号源，请选择其他时段')
        return
    }
    
    medicalStore.addAppointment({
        patientId: appointmentForm.value.patientId,
        patientName: appointmentForm.value.patientName,
        patientPhone: currentPatient.value.phone,
        patientAge: currentPatient.value.age,
        patientGender: currentPatient.value.gender,
        appointmentDate: formattedDate,
        appointmentTime: appointmentForm.value.appointmentTime,
        period: appointmentForm.value.period,
        symptoms: appointmentForm.value.symptoms
    })
    
    ElMessage.success(`已为患者 ${appointmentForm.value.patientName} 成功预约挂号`)
    showAppointmentDialog.value = false
}

const getAvailableSlotsForDate = (date, period) => {
    const formattedDate = date instanceof Date ? date.toISOString().split('T')[0] : date
    return medicalStore.getAvailableSlots(formattedDate, period)
}

const showAddPatientDialog = ref(false)
const addPatientLoading = ref(false)
const addPatientForm = ref({
    phone_number: '',
    password: '',
    username: '',
    gender: '',
    responsible_doctor_id: '',
    birth: '',
    ethnicity: '',
    origin: ''
})

const departments = ref([])
const doctors = ref([])
const selectedDepartmentId = ref('')

const fetchDepartments = async () => {
    try {
        const response = await request.get('/doctor/departments')
        if (response.base.code === '10000') {
            departments.value = response.data
        }
    } catch (error) {
        console.error('获取科室列表失败', error)
    }
}

const fetchDoctors = async (departmentId = null) => {
    try {
        let url = '/doctor/doctors'
        if (departmentId) {
            url += `?department_id=${departmentId}`
        }
        const response = await request.get(url)
        if (response.base.code === '10000') {
            doctors.value = response.data
        }
    } catch (error) {
        console.error('获取医生列表失败', error)
    }
}

const handleDepartmentChange = (departmentId) => {
    selectedDepartmentId.value = departmentId
    addPatientForm.value.responsible_doctor_id = ''
    fetchDoctors(departmentId)
}

const openAddPatientDialog = async () => {
    addPatientForm.value = {
        phone_number: '',
        password: '',
        username: '',
        gender: '',
        responsible_doctor_id: '',
        birth: '',
        ethnicity: '',
        origin: ''
    }
    selectedDepartmentId.value = ''
    showAddPatientDialog.value = true
    await fetchDepartments()
    await fetchDoctors()
}

const submitAddPatient = async () => {
    if (!addPatientForm.value.phone_number) {
        ElMessage.warning('请填写手机号')
        return
    }
    if (!/^1[3-9]\d{9}$/.test(addPatientForm.value.phone_number)) {
        ElMessage.warning('手机号格式不正确')
        return
    }
    if (!addPatientForm.value.password) {
        ElMessage.warning('请填写密码')
        return
    }
    if (addPatientForm.value.password.length < 6) {
        ElMessage.warning('密码至少6位')
        return
    }
    if (!addPatientForm.value.username) {
        ElMessage.warning('请填写姓名')
        return
    }
    if (!addPatientForm.value.gender) {
        ElMessage.warning('请选择性别')
        return
    }
    if (!addPatientForm.value.responsible_doctor_id) {
        ElMessage.warning('请选择负责医生')
        return
    }
    
    addPatientLoading.value = true
    
    try {
        const formData = new FormData()
        formData.append('phone_number', addPatientForm.value.phone_number)
        formData.append('password', addPatientForm.value.password)
        formData.append('username', addPatientForm.value.username)
        formData.append('gender', addPatientForm.value.gender)
        formData.append('responsible_doctor_id', addPatientForm.value.responsible_doctor_id)
        if (addPatientForm.value.birth) {
            formData.append('birth', addPatientForm.value.birth)
        }
        if (addPatientForm.value.ethnicity) {
            formData.append('ethnicity', addPatientForm.value.ethnicity)
        }
        if (addPatientForm.value.origin) {
            formData.append('origin', addPatientForm.value.origin)
        }
        
        const response = await request.post('/doctor/patient/create', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
        
        if (response.base.code === '10000') {
            ElMessage.success(`患者 ${response.data.username} 创建成功，可使用手机号和密码登录患者端`)
            showAddPatientDialog.value = false
            
            medicalStore.addPatient({
                id: response.data.id,
                name: response.data.username,
                gender: response.data.gender,
                age: response.data.birth ? calculateAge(response.data.birth) : 0,
                phone: response.data.phone_number,
                diagnosis: '待诊断',
                status: 'pending',
                lastVisit: new Date().toLocaleDateString('zh-CN')
            })
        } else {
            ElMessage.error(response.base.msg || '创建失败')
        }
    } catch (error) {
        ElMessage.error(error.message || '创建失败，请重试')
    } finally {
        addPatientLoading.value = false
    }
}

const calculateAge = (birthDate) => {
    const birth = new Date(birthDate)
    const today = new Date()
    let age = today.getFullYear() - birth.getFullYear()
    const monthDiff = today.getMonth() - birth.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--
    }
    return age > 0 ? age : 0
}
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
          <span class="welcome-text">{{ welcomeText }}</span>
        </div>
        <div class="welcome-actions">
          <el-badge :value="notificationCount" :hidden="notificationCount === 0" :max="99">
            <button class="notify-btn">
              <el-icon><Bell /></el-icon>
            </button>
          </el-badge>
          <span class="date-display">{{ new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }) }}</span>
        </div>
      </div>

      <div class="content-grid">
        <div class="card content-card patient-card">
          <div class="filter-bar">
            <div class="search-box">
              <el-input
                v-model="searchQuery"
                placeholder="搜索患者姓名或病情..."
                clearable
                @input="handleSearch"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
            <div class="filter-group">
              <span class="filter-label">病情状态：</span>
              <el-select v-model="statusFilter" placeholder="全部" @change="handleStatusChange" style="width: 120px;">
                <el-option
                  v-for="option in statusOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </div>
            <el-button type="primary" @click="openAddPatientDialog">
              <el-icon><Plus /></el-icon>
              新增患者
            </el-button>
            <div class="patient-count">
              共 {{ filteredPatients.length }} 位患者
            </div>
          </div>

          <div class="patient-table-wrapper">
            <el-table 
              :data="filteredPatients" 
              style="width: 100%"
              :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
              row-key="id"
            >
              <el-table-column prop="name" label="姓名" width="120" align="center">
                <template #default="{ row }">
                  <div class="patient-name">
                    <el-avatar :size="32" class="avatar">
                      {{ row.name.charAt(0) }}
                    </el-avatar>
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="gender" label="性别" width="80" align="center" />
              <el-table-column prop="age" label="年龄" width="80" align="center">
                <template #default="{ row }">
                  {{ row.age }}岁
                </template>
              </el-table-column>
              <el-table-column prop="phone" label="联系电话" width="130" align="center" />
              <el-table-column prop="diagnosis" label="诊断" min-width="120">
                <template #default="{ row }">
                  <span class="diagnosis-text">{{ row.diagnosis }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="lastVisit" label="最近就诊" width="120" align="center">
                <template #default="{ row }">
                  <span class="visit-date">{{ row.lastVisit }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="病情状态" width="110" align="center">
                <template #default="{ row }">
                  <el-tag :type="getStatusTag(row.status).type" size="small">
                    {{ getStatusTag(row.status).text }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180" align="center" fixed="right">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button type="primary" link size="small" @click="viewPatientDetail(row)">
                      查看详情
                    </el-button>
                    <el-button type="success" link size="small" @click="openAppointmentDialog(row)">
                      挂号预约
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div v-if="filteredPatients.length === 0" class="empty-state">
            <el-empty description="暂无患者数据" />
          </div>
        </div>
      </div>
    </main>

    <el-dialog v-model="showAppointmentDialog" title="挂号预约" width="500px" :close-on-click-modal="false">
      <el-form :model="appointmentForm" label-width="100px">
        <el-form-item label="患者姓名">
          <el-input v-model="appointmentForm.patientName" disabled />
        </el-form-item>
        <el-form-item label="预约日期" required>
          <el-date-picker
            v-model="appointmentForm.appointmentDate"
            type="date"
            placeholder="选择预约日期"
            style="width: 100%"
            :disabled-date="(time) => time.getTime() < Date.now() - 86400000"
          />
        </el-form-item>
        <el-form-item label="就诊时段" required>
          <el-radio-group v-model="appointmentForm.period" style="width: 100%">
            <el-radio-button label="上午">
              上午
              <span v-if="appointmentForm.appointmentDate" class="slot-count">
                (剩余: {{ getAvailableSlotsForDate(appointmentForm.appointmentDate, 'morning') }}号)
              </span>
            </el-radio-button>
            <el-radio-button label="下午">
              下午
              <span v-if="appointmentForm.appointmentDate" class="slot-count">
                (剩余: {{ getAvailableSlotsForDate(appointmentForm.appointmentDate, 'afternoon') }}号)
              </span>
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="预约时间" required>
          <el-select v-model="appointmentForm.appointmentTime" placeholder="选择时段" style="width: 100%">
            <el-option
              v-for="slot in timeSlots"
              :key="slot.value"
              :label="slot.label"
              :value="slot.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="症状描述">
          <el-input
            v-model="appointmentForm.symptoms"
            type="textarea"
            :rows="3"
            placeholder="请输入患者症状描述..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAppointmentDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAppointment">确认预约</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showAddPatientDialog" title="新增患者" width="600px" :close-on-click-modal="false">
      <div class="form-tips">
        <el-icon><InfoFilled /></el-icon>
        <span>带 <span class="required-mark">*</span> 的为必填项，患者可使用手机号和密码登录患者端</span>
      </div>
      <el-form :model="addPatientForm" label-width="100px" style="margin-top: 16px;">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号" required>
              <el-input v-model="addPatientForm.phone_number" placeholder="请输入11位手机号" maxlength="11">
                <template #prepend>+86</template>
              </el-input>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="密码" required>
              <el-input v-model="addPatientForm.password" type="password" placeholder="至少6位密码" show-password maxlength="20" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" required>
              <el-input v-model="addPatientForm.username" placeholder="请输入患者姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别" required>
              <el-radio-group v-model="addPatientForm.gender">
                <el-radio label="男">男</el-radio>
                <el-radio label="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">负责医生</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="科室筛选">
              <el-select 
                v-model="selectedDepartmentId" 
                placeholder="选择科室筛选医生" 
                clearable 
                style="width: 100%"
                @change="handleDepartmentChange"
              >
                <el-option
                  v-for="dept in departments"
                  :key="dept.id"
                  :label="dept.name"
                  :value="dept.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责医生" required>
              <el-select 
                v-model="addPatientForm.responsible_doctor_id" 
                placeholder="请选择负责医生" 
                style="width: 100%"
              >
                <el-option
                  v-for="doc in doctors"
                  :key="doc.id"
                  :label="`${doc.username}${doc.title ? ' - ' + doc.title : ''}${doc.department_name ? ' (' + doc.department_name + ')' : ''}`"
                  :value="doc.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">选填信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="出生日期">
              <el-date-picker
                v-model="addPatientForm.birth"
                type="date"
                placeholder="选择出生日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="民族">
              <el-input v-model="addPatientForm.ethnicity" placeholder="如：汉族" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="籍贯">
          <el-input v-model="addPatientForm.origin" placeholder="如：北京市" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPatientDialog = false">取消</el-button>
        <el-button type="primary" :loading="addPatientLoading" @click="submitAddPatient">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.form-tips {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: #f0f9ff;
    border-radius: 8px;
    color: #0369a1;
    font-size: 13px;
}

.form-tips .el-icon {
    font-size: 16px;
}

.required-mark {
    color: #f56c6c;
    font-weight: bold;
}

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

.notify-btn {
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
  transition: all 0.2s;
}

.notify-btn:hover {
  background: #e8e8e8;
  color: #333;
}

.content-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.patient-card {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.search-box {
  width: 280px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.patient-count {
  margin-left: auto;
  font-size: 14px;
  color: #909399;
}

.patient-table-wrapper {
  flex: 1;
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  padding: 16px;
}

.patient-name {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}

.avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.diagnosis-text {
  color: #606266;
}

.visit-date {
  color: #909399;
  font-size: 13px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border-radius: 12px;
  padding: 40px;
}

.slot-count {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
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

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .search-box {
    width: 100%;
  }

  .patient-count {
    margin-left: 0;
    text-align: center;
  }
}
</style>
