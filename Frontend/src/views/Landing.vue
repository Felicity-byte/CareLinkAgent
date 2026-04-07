<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import request from '../api/request'

const router = useRouter()
const authStore = useAuthStore()

const loginType = ref('doctor')
const doctorForm = ref({ username: '', password: '' })
const patientForm = ref({ username: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')
const isSwitching = ref(false)

const showRegisterDialog = ref(false)
const showDoctorForgotDialog = ref(false)
const showPatientForgotDialog = ref(false)

const registerForm = ref({ phone: '', password: '', confirmPassword: '', username: '', departmentId: '' })
const forgotForm = ref({ username: '', phone: '' })
const departmentList = ref([])

const fetchDepartments = async () => {
  try {
    const res = await request.get('/department/list')
    if (res.base && res.base.code === '10000') {
      departmentList.value = res.data || []
    }
  } catch (error) {
    console.error('获取科室列表失败:', error)
  }
}

onMounted(() => {
  fetchDepartments()
})

const handleLogin = async () => {
  const form = loginType.value === 'doctor' ? doctorForm.value : patientForm.value
  
  if (!form.username || !form.password) {
    errorMsg.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const success = await authStore.login(form.username, form.password, loginType.value)
    if (success) {
      if (loginType.value === 'patient') {
        router.push({ name: 'ai-chat' })
      } else {
        router.push({ name: 'dashboard' })
      }
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.msg || err.message || '登录失败，请重试'
  } finally {
    loading.value = false
  }
}

const switchToPatient = () => {
  isSwitching.value = true
  loginType.value = 'patient'
  errorMsg.value = ''
  setTimeout(() => {
    isSwitching.value = false
  }, 500)
}

const switchToDoctor = () => {
  isSwitching.value = true
  loginType.value = 'doctor'
  errorMsg.value = ''
  setTimeout(() => {
    isSwitching.value = false
  }, 500)
}

const handleRegister = async () => {
  if (!registerForm.value.phone || !registerForm.value.password || !registerForm.value.username || !registerForm.value.departmentId) {
    errorMsg.value = '请填写完整信息'
    return
  }
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const formData = new URLSearchParams()
    formData.append('phone_number', registerForm.value.phone)
    formData.append('password', registerForm.value.password)
    formData.append('username', registerForm.value.username)
    formData.append('department_id', registerForm.value.departmentId)

    await request.post('/doctor/register', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    ElMessage.success('注册成功，请登录')
    showRegisterDialog.value = false
    registerForm.value = { phone: '', password: '', confirmPassword: '', username: '', departmentId: '' }
  } catch (err) {
    errorMsg.value = err.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}

const handleForgotPassword = (type) => {
  if (type === 'doctor') {
    showDoctorForgotDialog.value = false
  } else {
    showPatientForgotDialog.value = false
  }
  forgotForm.value = { username: '', phone: '' }
}
</script>

<template>
  <div class="login-container">
    <div class="login-card">
      <div class="form-panel doctor-form">
        <div class="form-header doctor-header">
          <el-icon class="header-icon"><UserFilled /></el-icon>
          <h1 class="title">医智 MedMind</h1>
          <p class="subtitle">医生端登录</p>
        </div>
        <div class="form-body">
          <transition name="fade" mode="out-in">
            <div v-if="isSwitching && loginType === 'patient'" key="skeleton" class="skeleton-wrapper">
              <div class="skeleton-item skeleton-label"></div>
              <div class="skeleton-item skeleton-input"></div>
              <div class="skeleton-item skeleton-label"></div>
              <div class="skeleton-item skeleton-input"></div>
              <div class="skeleton-item skeleton-btn"></div>
            </div>
            <div v-else key="form" class="form-content">
              <div class="form-group">
                <label>手机号</label>
                <input
                  v-model="doctorForm.username"
                  type="text"
                  class="form-input"
                  placeholder="输入您的手机号"
                  @keyup.enter="handleLogin"
                >
              </div>
              <div class="form-group">
                <label>密码</label>
                <input
                  v-model="doctorForm.password"
                  type="password"
                  class="form-input"
                  placeholder="输入您的密码"
                  @keyup.enter="handleLogin"
                >
              </div>
              <button class="login-btn doctor-btn" :disabled="loading" @click="handleLogin">
                {{ loading ? '登录中...' : '登录系统' }}
              </button>
              <div class="form-links">
                <span class="link-label">遇到问题了？</span>
                <div class="link-right">
                  <span class="link-item" @click="showRegisterDialog = true">注册账号</span>
                  <span class="link-divider">|</span>
                  <span class="link-item" @click="showDoctorForgotDialog = true">忘记密码</span>
                </div>
              </div>
              <div v-if="errorMsg && loginType === 'doctor'" class="error-msg-bottom">
                {{ errorMsg }}
              </div>
            </div>
          </transition>
        </div>
      </div>

      <div class="form-panel patient-form">
        <div class="form-header patient-header">
          <el-icon class="header-icon"><UserFilled /></el-icon>
          <h1 class="title">医智 MedMind</h1>
          <p class="subtitle">患者端登录</p>
        </div>
        <div class="form-body">
          <transition name="fade" mode="out-in">
            <div v-if="isSwitching && loginType === 'doctor'" key="skeleton" class="skeleton-wrapper">
              <div class="skeleton-item skeleton-label"></div>
              <div class="skeleton-item skeleton-input"></div>
              <div class="skeleton-item skeleton-label"></div>
              <div class="skeleton-item skeleton-input"></div>
              <div class="skeleton-item skeleton-btn"></div>
            </div>
            <div v-else key="form" class="form-content">
              <div class="form-group">
                <label>手机号</label>
                <input
                  v-model="patientForm.username"
                  type="text"
                  class="form-input"
                  placeholder="输入您的手机号"
                  @keyup.enter="handleLogin"
                >
              </div>
              <div class="form-group">
                <label>密码</label>
                <input
                  v-model="patientForm.password"
                  type="password"
                  class="form-input"
                  placeholder="输入您的密码"
                  @keyup.enter="handleLogin"
                >
              </div>
              <button class="login-btn patient-btn" :disabled="loading" @click="handleLogin">
                {{ loading ? '登录中...' : '登录系统' }}
              </button>
              <div class="form-links">
                <span class="link-label">遇到问题了？</span>
                <div class="link-right">
                  <span class="link-item" @click="showPatientForgotDialog = true">忘记密码</span>
                </div>
              </div>
              <div v-if="errorMsg && loginType === 'patient'" class="error-msg-bottom">
                {{ errorMsg }}
              </div>
            </div>
          </transition>
        </div>
      </div>

      <div class="switch-overlay" :class="{ 'slide-left': loginType === 'patient' }">
        <div class="switch-panel" :class="{ 'patient-panel': loginType === 'patient' }">
          <transition name="fade" mode="out-in">
            <div v-if="loginType === 'doctor'" key="patient" class="switch-info">
              <el-icon class="switch-icon"><User /></el-icon>
              <h2 class="switch-title">我是患者</h2>
              <p class="switch-desc">术后随访 · AI问诊 · 健康管理</p>
              <button class="switch-btn patient-btn" @click="switchToPatient">切换登录</button>
            </div>
            <div v-else key="doctor" class="switch-info">
              <el-icon class="switch-icon"><FirstAidKit /></el-icon>
              <h2 class="switch-title">我是医生</h2>
              <p class="switch-desc">患者管理 · 辅助诊断 · 工作台</p>
              <button class="switch-btn doctor-btn" @click="switchToDoctor">切换登录</button>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <div class="security-note">
      <el-icon><Shield /></el-icon>
      <span>医疗数据安全加密保障</span>
    </div>

    <el-dialog v-model="showRegisterDialog" title="医生注册" width="400px" :close-on-click-modal="false">
      <el-form :model="registerForm" label-width="80px">
        <el-form-item label="手机号">
          <el-input v-model="registerForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="registerForm.username" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="科室">
          <el-select v-model="registerForm.departmentId" placeholder="请选择科室" style="width: 100%">
            <el-option
              v-for="dept in departmentList"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegisterDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRegister">注册</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showDoctorForgotDialog" title="找回密码" width="400px" :close-on-click-modal="false">
      <el-form :model="forgotForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="forgotForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="forgotForm.phone" placeholder="请输入绑定的手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDoctorForgotDialog = false">取消</el-button>
        <el-button type="primary" @click="handleForgotPassword('doctor')">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPatientForgotDialog" title="找回密码" width="400px" :close-on-click-modal="false">
      <el-form :model="forgotForm" label-width="80px">
        <el-form-item label="手机号">
          <el-input v-model="forgotForm.phone" placeholder="请输入注册手机号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPatientForgotDialog = false">取消</el-button>
        <el-button type="primary" @click="handleForgotPassword('patient')">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
/* 页面容器 - 全屏居中布局，白色到浅蓝渐变背景 */
.login-container {
  background: linear-gradient(135deg, #ffffff 0%, #91c7ea 100%);
  min-height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 登录卡片 - 主容器，固定尺寸，圆角阴影 */
.login-card {
  width: 800px;
  height: 500px;
  background: white;
  border-radius: 30px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  position: relative;
}

/* 表单面板 - 左右两侧登录表单的基础样式 */
.form-panel {
  width: 50%;
  position: absolute;
  top: 0;
  height: 100%;
  background: white;
  display: flex;
  flex-direction: column;
}

/* 医生表单 - 定位在左侧 */
.doctor-form {
  left: 0;
}

/* 患者表单 - 定位在右侧 */
.patient-form {
  right: 0;
}

/* 表单头部 - 包含图标、标题、副标题 */
.form-header {
  padding: 24px 20px;
  text-align: center;
  color: white;
}

/* 医生端头部 - 浅蓝色背景 */
.doctor-header {
  background: #7fbce6;
}

/* 患者端头部 - 绿色背景 */
.patient-header {
  background: #46c890;
}

/* 头部图标大小 */
.header-icon {
  font-size: 40px;
}

/* 标题样式 */
.title {
  font-size: 22px;
  font-weight: bold;
  margin: 8px 0 4px;
}

/* 副标题样式 */
.subtitle {
  font-size: 14px;
  opacity: 0.9;
}

/* 表单主体区域 - 包含输入框和按钮，自动填充剩余空间 */
.form-body {
  padding: 20px 32px;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* 表单内容容器 */
.form-content {
  width: 100%;
}

/* 表单组 - 每个输入框的容器，左右布局 */
.form-group {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 表单标签样式 */
.form-group label {
  flex-shrink: 0;
  width: 56px;
  color: #374151;
  font-size: 14px;
}

/* 输入框样式 */
.form-input {
  border: 1px solid #D1D5DB;
  border-radius: 30px;
  padding: 12px 14px;
  flex: 1;
  font-size: 14px;
  box-sizing: border-box;
  transition: border-color 0.3s;
}

/* 输入框聚焦状态 - 蓝色边框和阴影 */
.form-input:focus {
  border-color: #722222;
  outline: none;
  box-shadow: 0 0 0 3px rgba(44, 125, 177, 0.15);
}

/* 底部错误提示 */
.error-msg-bottom {
  color: #EF4444;
  font-size: 13px;
  text-align: center;
  margin-top: 12px;
  min-height: 18px;
}

/* 登录按钮基础样式 */
.login-btn {
  color: white;
  padding: 12px;
  border-radius: 30px;
  font-weight: 600;
  font-size: 15px;
  width: 100%;
  border: none;
  cursor: pointer;
  transition: background 0.3s;
}

/* 医生端按钮 - 蓝色 */
.doctor-btn {
  background: #63b2e2;
}

/* 医生端按钮悬停效果 */
.doctor-btn:hover:not(:disabled) {
  background: #24618d;
}

/* 患者端按钮 - 绿色 */
.patient-btn {
  background: #4fd6a9;
}

/* 患者端按钮悬停效果 */
.patient-btn:hover:not(:disabled) {
  background: #059669;
}

/* 按钮禁用状态 */
.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 表单链接区域 */
.form-links {
  margin-top: 12px;
  display: flex;
  align-items: center;
  font-size: 13px;
  gap: 8px;
  justify-content: flex-end;
}

/* 链接标签 */
.link-label {
  color: #9CA3AF;
}

/* 链接右侧区域 */
.link-right {
  display: flex;
  align-items: center;
}

/* 链接项 */
.link-item {
  cursor: pointer;
  color: #2C7DB1;
  transition: color 0.3s;
}

.link-item:hover {
  color: #1a4a6e;
}

/* 链接分隔符 */
.link-divider {
  margin: 0 8px;
  color: #D1D5DB;
}

/* 安全提示文字 - 页面底部居中 */
.security-note {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  color: #9CA3AF;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

/* 切换面板容器 - 可滑动的覆盖层 */
.switch-overlay {
  width: 50%;
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 10;
}

/* 切换面板左滑状态 - 切换到患者端时触发 */
.switch-overlay.slide-left {
  transform: translateX(-100%);
}

/* 切换面板内容 - 渐变背景 */
.switch-panel {
  width: 100%;
  height: 100%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(to right, #7fbce6 0%, #46c890 100%);
  transition: all 0.5s ease;
}

/* 患者端切换面板 - 同样的浅蓝到浅绿渐变 */
.switch-panel.patient-panel {
  background: linear-gradient(to right, #7fbce6 0%, #46c890 100%);
}

/* 切换面板内容区域 */
.switch-info {
  text-align: center;
  padding: 20px;
}

/* 切换面板图标 */
.switch-icon {
  font-size: 56px;
}

/* 切换面板标题 */
.switch-title {
  font-size: 22px;
  font-weight: bold;
  margin: 12px 0 4px;
}

/* 切换面板描述文字 */
.switch-desc {
  font-size: 13px;
  opacity: 0.8;
}

/* 切换按钮样式 */
.switch-btn {
  margin-top: 24px;
  padding: 12px 36px;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid white;
  color: white;
  border-radius: 50px;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

/* 切换按钮悬停效果 */
.switch-btn:hover {
  background: white;
  color: #ffffff;
}

/* 患者端切换按钮悬停效果 - 绿色文字 */
.switch-btn.patient-btn:hover {
  color: #ffffff;
}

/* 骨架屏容器 */
.skeleton-wrapper {
  padding: 0;
}

/* 骨架屏元素基础样式 */
.skeleton-item {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 4px;
}

/* 骨架屏标签 */
.skeleton-label {
  height: 14px;
  width: 60px;
  margin-bottom: 6px;
}

/* 骨架屏输入框 */
.skeleton-input {
  height: 44px;
  width: 100%;
  margin-bottom: 20px;
}

/* 骨架屏按钮 */
.skeleton-btn {
  height: 44px;
  width: 100%;
  margin-top: 0;
}

/* 骨架屏动画 */
@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* Vue过渡动画 - 淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

/* Vue过渡动画 - 开始和结束状态 */
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
