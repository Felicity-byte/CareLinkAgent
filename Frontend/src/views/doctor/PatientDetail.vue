<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useMedicalStore } from '../../stores/medical'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const medicalStore = useMedicalStore()

const patientId = route.params.id

const sidebarCollapsed = ref(true)
const isMobile = ref(window.innerWidth < 768)

const activeTab = ref('basic')

const menuItems = ref([
    { label: '工作台', icon: 'HomeFilled', active: false, route: '/doctor/workspace' },
    { label: '患者管理', icon: 'User', active: true, route: '/doctor/patients' },
    { label: '挂号预约', icon: 'Calendar', active: false, route: '/doctor/appointments' },
    { label: '个人中心', icon: 'Setting', active: false, route: '/doctor/profile' }
])

const tabs = [
    { key: 'basic', label: '基本信息', icon: 'User' },
    { key: 'medical', label: '病历记录', icon: 'Document' },
    { key: 'consultation', label: '咨询记录', icon: 'ChatDotRound' },
    { key: 'report', label: '检查报告', icon: 'DocumentChecked' }
]

const patientData = computed(() => medicalStore.getPatientById(patientId))

const patientInfo = ref({
    id: patientId,
    name: patientData.value?.name || '张三',
    gender: patientData.value?.gender || '男',
    age: patientData.value?.age || 45,
    phone: patientData.value?.phone || '138****1234',
    idCard: '450***********1234',
    birthDate: '1981-03-15',
    address: '广西壮族自治区桂林市七星区xxx路xxx号',
    emergencyContact: '李四（配偶）',
    emergencyPhone: '139****5678',
    bloodType: 'A型',
    allergy: '青霉素过敏',
    status: patientData.value?.status || 'in_progress',
    diagnosis: patientData.value?.diagnosis || '高血压',
    createTime: '2026-01-15'
})

const medicalRecords = computed(() => medicalStore.getMedicalRecordsByPatientId(patientId))

const consultationRecords = ref([
    {
        id: 1,
        date: '2026-04-05 14:30',
        type: '在线咨询',
        doctor: '王医生',
        content: '患者主诉头晕、头痛3天，血压波动在140-160/90-100mmHg之间',
        reply: '建议调整用药剂量，注意监测血压变化，如症状加重请及时就医'
    },
    {
        id: 2,
        date: '2026-03-20 10:00',
        type: '在线咨询',
        doctor: '王医生',
        content: '服药后血压有所下降，但偶尔仍有头晕症状',
        reply: '继续服药观察，保持规律作息，避免剧烈运动'
    }
])

const reportRecords = ref([
    {
        id: 1,
        date: '2026-04-09',
        type: '血常规',
        result: '正常',
        detail: '白细胞 6.5×10^9/L，红细胞 4.8×10^12/L，血红蛋白 145g/L'
    },
    {
        id: 2,
        date: '2026-04-09',
        type: '生化检查',
        result: '轻度异常',
        detail: '血糖 5.8mmol/L，总胆固醇 5.9mmol/L（偏高），甘油三酯 1.8mmol/L'
    },
    {
        id: 3,
        date: '2026-03-15',
        type: '心电图',
        result: '正常',
        detail: '窦性心律，心率78次/分，心电图大致正常'
    }
])

const handleMenuClick = (index) => {
    menuItems.value.forEach((item, i) => {
        item.active = i === index
    })
    const routePath = menuItems.value[index].route
    if (routePath) {
        router.push(routePath)
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

const goBack = () => {
    router.push('/doctor/patients')
}

const getStatusTag = (status) => {
    const statusMap = {
        'pending': { type: 'warning', text: '待就诊' },
        'in_progress': { type: 'primary', text: '就诊中' },
        'completed': { type: 'success', text: '已完成' }
    }
    return statusMap[status] || { type: 'info', text: '未知' }
}

const getReportTag = (result) => {
    if (result === '正常') return { type: 'success', text: '正常' }
    if (result.includes('异常')) return { type: 'warning', text: result }
    return { type: 'info', text: result }
}

const isEditing = ref(false)
const editForm = ref({})

const startEdit = () => {
    isEditing.value = true
    editForm.value = { ...patientInfo.value }
}

const cancelEdit = () => {
    isEditing.value = false
    editForm.value = {}
}

const saveEdit = () => {
    patientInfo.value = { ...editForm.value }
    medicalStore.updatePatientInfo(patientId, {
        name: editForm.value.name,
        gender: editForm.value.gender,
        age: editForm.value.age,
        status: editForm.value.status,
        diagnosis: editForm.value.diagnosis
    })
    isEditing.value = false
    ElMessage.success('患者信息已更新')
}

const statusOptions = [
    { label: '待就诊', value: 'pending' },
    { label: '就诊中', value: 'in_progress' },
    { label: '已完成', value: 'completed' }
]

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
          <button class="back-btn" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
          </button>
          <span class="welcome-text">{{ patientInfo.name }} - 患者详情</span>
          <el-tag :type="getStatusTag(patientInfo.status).type" size="small">
            {{ getStatusTag(patientInfo.status).text }}
          </el-tag>
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

        <div class="tab-content card">
          <div v-if="activeTab === 'basic'" class="panel basic-info">
            <div class="section-header">
              <div class="section-title">基本信息</div>
              <div class="section-actions">
                <el-button v-if="!isEditing" type="primary" size="small" @click="startEdit">
                  <el-icon><Edit /></el-icon>
                  编辑信息
                </el-button>
                <template v-else>
                  <el-button size="small" @click="cancelEdit">取消</el-button>
                  <el-button type="primary" size="small" @click="saveEdit">保存</el-button>
                </template>
              </div>
            </div>
            
            <div v-if="!isEditing" class="info-grid">
              <div class="info-item">
                <span class="label">姓名</span>
                <span class="value">{{ patientInfo.name }}</span>
              </div>
              <div class="info-item">
                <span class="label">性别</span>
                <span class="value">{{ patientInfo.gender }}</span>
              </div>
              <div class="info-item">
                <span class="label">年龄</span>
                <span class="value">{{ patientInfo.age }}岁</span>
              </div>
              <div class="info-item">
                <span class="label">出生日期</span>
                <span class="value">{{ patientInfo.birthDate }}</span>
              </div>
              <div class="info-item">
                <span class="label">联系电话</span>
                <span class="value">{{ patientInfo.phone }}</span>
              </div>
              <div class="info-item">
                <span class="label">身份证号</span>
                <span class="value">{{ patientInfo.idCard }}</span>
              </div>
              <div class="info-item">
                <span class="label">家庭住址</span>
                <span class="value">{{ patientInfo.address }}</span>
              </div>
              <div class="info-item">
                <span class="label">紧急联系人</span>
                <span class="value">{{ patientInfo.emergencyContact }} {{ patientInfo.emergencyPhone }}</span>
              </div>
            </div>

            <div v-else class="edit-form">
              <el-form :model="editForm" label-width="100px">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="姓名">
                      <el-input v-model="editForm.name" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="性别">
                      <el-select v-model="editForm.gender" style="width: 100%">
                        <el-option label="男" value="男" />
                        <el-option label="女" value="女" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="年龄">
                      <el-input-number v-model="editForm.age" :min="0" :max="150" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="出生日期">
                      <el-date-picker v-model="editForm.birthDate" type="date" style="width: 100%" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="联系电话">
                      <el-input v-model="editForm.phone" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="身份证号">
                      <el-input v-model="editForm.idCard" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-form-item label="家庭住址">
                  <el-input v-model="editForm.address" />
                </el-form-item>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="紧急联系人">
                      <el-input v-model="editForm.emergencyContact" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="紧急电话">
                      <el-input v-model="editForm.emergencyPhone" />
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>

            <div class="section-header" style="margin-top: 24px;">
              <div class="section-title">健康信息</div>
            </div>
            
            <div v-if="!isEditing" class="info-grid">
              <div class="info-item">
                <span class="label">血型</span>
                <span class="value">{{ patientInfo.bloodType }}</span>
              </div>
              <div class="info-item">
                <span class="label">过敏史</span>
                <span class="value highlight">{{ patientInfo.allergy }}</span>
              </div>
              <div class="info-item">
                <span class="label">当前诊断</span>
                <span class="value">{{ patientInfo.diagnosis }}</span>
              </div>
              <div class="info-item">
                <span class="label">病情状态</span>
                <el-tag :type="getStatusTag(patientInfo.status).type" size="small">
                  {{ getStatusTag(patientInfo.status).text }}
                </el-tag>
              </div>
              <div class="info-item">
                <span class="label">建档时间</span>
                <span class="value">{{ patientInfo.createTime }}</span>
              </div>
            </div>

            <div v-else class="edit-form">
              <el-form :model="editForm" label-width="100px">
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="血型">
                      <el-select v-model="editForm.bloodType" style="width: 100%">
                        <el-option label="A型" value="A型" />
                        <el-option label="B型" value="B型" />
                        <el-option label="AB型" value="AB型" />
                        <el-option label="O型" value="O型" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="过敏史">
                      <el-input v-model="editForm.allergy" />
                    </el-form-item>
                  </el-col>
                </el-row>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="当前诊断">
                      <el-input v-model="editForm.diagnosis" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="病情状态">
                      <el-select v-model="editForm.status" style="width: 100%">
                        <el-option
                          v-for="item in statusOptions"
                          :key="item.value"
                          :label="item.label"
                          :value="item.value"
                        />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </div>
          </div>

          <div v-if="activeTab === 'medical'" class="panel medical-records">
            <div class="section-header">
              <div class="section-title">病历记录</div>
              <el-tag type="info" size="small">
                <el-icon><Upload /></el-icon>
                患者端上传
              </el-tag>
            </div>
            
            <div class="upload-notice">
              <el-icon><InfoFilled /></el-icon>
              <span>以下病历记录由患者端上传，医生可查看患者的历史就诊信息</span>
            </div>
            
            <div class="timeline">
              <div v-for="record in medicalRecords" :key="record.id" class="timeline-item">
                <div class="timeline-date">
                  <span class="date">{{ record.date }}</span>
                  <el-tag size="small" :type="record.type === '初诊' ? 'primary' : 'success'">
                    {{ record.type }}
                  </el-tag>
                  <el-tag size="small" :type="record.source === 'doctor' ? 'warning' : 'info'" style="margin-left: 8px">
                    {{ record.source === 'doctor' ? '医生端创建' : '患者端上传' }}
                  </el-tag>
                </div>
                <div class="timeline-content">
                  <div class="record-header">
                    <span class="department">{{ record.department }}</span>
                    <span class="doctor">主治医师：{{ record.doctor }}</span>
                  </div>
                  <div v-if="record.currentSymptoms" class="record-section">
                    <div class="section-label">当前症状</div>
                    <div class="section-content">{{ record.currentSymptoms }}</div>
                  </div>
                  <div class="record-section">
                    <div class="section-label">诊断结果</div>
                    <div class="section-content">{{ record.diagnosis }}</div>
                  </div>
                  <div v-if="record.examinations && record.examinations.length > 0" class="record-section">
                    <div class="section-label">检查项目</div>
                    <div class="examination-list">
                      <el-tag v-for="exam in record.examinations" :key="exam" size="small" style="margin-right: 8px; margin-bottom: 4px">
                        {{ exam }}
                      </el-tag>
                    </div>
                  </div>
                  <div v-if="record.prescription && record.prescription.length > 0" class="record-section">
                    <div class="section-label">处方用药</div>
                    <div class="prescription-list">
                      <div v-for="(drug, idx) in record.prescription" :key="idx" class="drug-item">
                        <span class="drug-name">{{ drug.name }}</span>
                        <span class="drug-spec">{{ drug.spec }}</span>
                        <span class="drug-usage">{{ drug.usage }}</span>
                        <span class="drug-days">{{ drug.days }}天</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="record.advice" class="record-section">
                    <div class="section-label">医嘱</div>
                    <div class="section-content">{{ record.advice }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'consultation'" class="panel consultation-records">
            <div class="section-header">
              <div class="section-title">咨询记录</div>
            </div>
            
            <div class="consultation-list">
              <div v-for="item in consultationRecords" :key="item.id" class="consultation-item">
                <div class="consultation-header">
                  <span class="date">{{ item.date }}</span>
                  <el-tag size="small" type="info">{{ item.type }}</el-tag>
                  <span class="doctor">{{ item.doctor }}</span>
                </div>
                <div class="consultation-body">
                  <div class="message patient-msg">
                    <div class="msg-label">患者提问</div>
                    <div class="msg-content">{{ item.content }}</div>
                  </div>
                  <div class="message doctor-msg">
                    <div class="msg-label">医生回复</div>
                    <div class="msg-content">{{ item.reply }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'report'" class="panel report-records">
            <div class="section-header">
              <div class="section-title">检查报告</div>
            </div>
            
            <el-table :data="reportRecords" style="width: 100%">
              <el-table-column prop="date" label="检查日期" width="120" align="center" />
              <el-table-column prop="type" label="检查类型" width="120" align="center" />
              <el-table-column prop="result" label="结果" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="getReportTag(row.result).type" size="small">
                    {{ getReportTag(row.result).text }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="detail" label="详情" min-width="300">
                <template #default="{ row }">
                  <span class="report-detail">{{ row.detail }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" align="center">
                <template #default>
                  <el-button type="primary" link size="small">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>
    </main>
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

.back-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background: #f5f7fa;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #555;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #e8e8e8;
  color: #333;
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

.panel {
  min-height: 100%;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 3px solid #4f8cff;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.upload-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #e6f7ff;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #1890ff;
}

.edit-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 12px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.info-item .label {
  width: 100px;
  font-size: 14px;
  color: #909399;
  flex-shrink: 0;
}

.info-item .value {
  font-size: 14px;
  color: #333;
}

.info-item .value.highlight {
  color: #f56c6c;
  font-weight: 500;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.timeline-item {
  display: flex;
  gap: 20px;
}

.timeline-date {
  width: 120px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.timeline-date .date {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.timeline-content {
  flex: 1;
  padding: 16px 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border-left: 3px solid #4f8cff;
}

.record-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.record-header .department {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.record-header .doctor {
  font-size: 13px;
  color: #909399;
}

.record-section {
  margin-bottom: 12px;
}

.record-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.section-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.prescription-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drug-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #fff;
  border-radius: 8px;
  font-size: 13px;
}

.drug-name {
  font-weight: 500;
  color: #333;
}

.drug-spec {
  color: #909399;
}

.drug-usage {
  color: #666;
}

.drug-days {
  color: #4f8cff;
  margin-left: auto;
}

.consultation-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.consultation-item {
  padding: 16px 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.consultation-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.consultation-header .date {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.consultation-header .doctor {
  font-size: 13px;
  color: #909399;
  margin-left: auto;
}

.consultation-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
}

.message.patient-msg {
  background: #fff;
  border-left: 3px solid #67c23a;
}

.message.doctor-msg {
  background: #ecf5ff;
  border-left: 3px solid #4f8cff;
}

.msg-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.msg-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.report-detail,
.followup-content {
  font-size: 13px;
  color: #606266;
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

  .info-grid {
    grid-template-columns: 1fr;
  }

  .timeline-item {
    flex-direction: column;
    gap: 8px;
  }

  .timeline-date {
    width: 100%;
    flex-direction: row;
    align-items: center;
  }
}
</style>
