<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import request from '../../api/request'
import { PictureFilled, Loading, Setting, SwitchButton, Document, Close, Bell } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const chatContainer = ref(null)
const textareaRef = ref(null)
const isDarkMode = ref(false)
const isMobile = ref(false)
const sidebarCollapsed = ref(false)
const chatTitle = ref('AI 智能导诊')
const showProfileMenu = ref(false)
const showSettingsDialog = ref(false)
const showNotificationsDialog = ref(false)
const selectedNotification = ref(null)
const settingsActiveTab = ref('general')
const notifications = ref([
    {
        id: 1,
        type: 'appointment',
        title: '预约提醒',
        content: '您预约的内科门诊将于明天上午9:00开始，请准时就诊。',
        detail: '门诊楼3楼内科诊室 · 携带身份证和医保卡',
        time: new Date(Date.now() - 1000 * 60 * 30),
        read: false
    },
    {
        id: 2,
        type: 'system',
        title: '健康档案更新',
        content: '您的健康档案已更新完成，可以在个人中心查看详细信息。',
        time: new Date(Date.now() - 1000 * 60 * 60 * 24),
        read: true
    },
    {
        id: 3,
        type: 'appointment',
        title: '就诊提醒',
        content: '您有一个预约将在后天进行，请注意时间安排。',
        time: new Date(Date.now() - 1000 * 60 * 60 * 48),
        read: false
    }
])
const userInfo = ref({
    username: '',
    phone_number: '',
    password: '',
    confirmPassword: '',
    avatar_url: '',
    gender: '',
    birth: '',
    ethnicity: '',
    origin: '',
    email: ''
})
const responsibleDoctor = ref(null)
const surgeryRecords = ref([])
const avatarInputRef = ref(null)
const uploadingAvatar = ref(false)

// 图片分析相关状态
const fileInputRef = ref(null)
const analyzingImage = ref(false)
const pendingQuestions = ref([])
const waitingForAnswers = ref(false)
const currentSessionId = ref(`sess_${Date.now()}`)

// AI导诊会话
const aiSessionId = ref('')

const historyList = ref([])

const notificationCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
})

const todayHistory = computed(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return historyList.value.filter(item => item.timestamp >= today.getTime())
})

const weekHistory = computed(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const weekAgo = today.getTime() - 7 * 86400000
    return historyList.value.filter(item => item.timestamp >= weekAgo && item.timestamp < today.getTime())
})

const olderHistory = computed(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const weekAgo = today.getTime() - 7 * 86400000
    return historyList.value.filter(item => item.timestamp < weekAgo)
})

const fetchHistoryList = async () => {
    try {
        const res = await request.get('/ai/sessions')
        const sessions = res.data.sessions || []
        historyList.value = sessions.map(s => ({
            id: s.id,
            title: s.title || 'AI问诊',
            time: s.updated_at ? formatHistoryTime(s.updated_at) : '',
            timestamp: s.updated_at ? new Date(s.updated_at).getTime() : 0
        }))
    } catch (err) {
        console.error('获取历史记录失败', err)
    }
}

const formatHistoryTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (minutes < 60) return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    if (hours < 24) return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const scrollToBottom = async () => {
    await nextTick()
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
}

const addMessage = (content, isUser = false) => {
    const msg = {
        id: Date.now(),
        content,
        isUser,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    }
    messages.value.push(msg)
    scrollToBottom()
    return msg
}

const createAISession = async () => {
    try {
        console.log('[DEBUG] 创建AI会话, patient_id:', authStore.user?.id)
        const res = await request.post('/ai/create-session', {
            patient_id: authStore.user?.id,
            patient_name: authStore.user?.username || '患者'
        })
        console.log('[DEBUG] AI会话创建成功:', res.data)
        aiSessionId.value = res.data.session_id
        if (res.data.welcome_message) {
            addMessage(res.data.welcome_message, false)
        }
    } catch (err) {
        console.error('创建AI会话失败', err)
        addMessage('您好！我是 AI 智能导诊助手。请告诉我您的症状或健康问题，我会为您提供专业的医疗建议和分诊指导。', false)
    }
}

const handleSend = async () => {
    const text = inputText.value.trim()
    if (!text || loading.value) return

    if (waitingForAnswers.value) {
        await handlePatientAnswer(text)
        return
    }

    if (!aiSessionId.value) {
        await createAISession()
    }

    if (messages.value.length === 0 || chatTitle.value === 'AI 智能导诊') {
        chatTitle.value = text.slice(0, 15) + (text.length > 15 ? '...' : '')
    }

    inputText.value = ''
    addMessage(text, true)
    loading.value = true

    const aiMessageIndex = messages.value.length
    messages.value.push({
        id: Date.now(),
        content: '',
        isUser: false,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })

    try {
        const response = await fetch('/api/ai/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authStore.token}`
            },
            body: JSON.stringify({
                session_id: aiSessionId.value,
                message: text,
                is_end: false
            })
        })

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value)
            const lines = chunk.split('\n')

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6))
                        if (data.error) {
                            console.error('AI回复错误:', data.error)
                            messages.value[aiMessageIndex].content += '\n[错误: ' + data.error + ']'
                        } else if (data.content) {
                            messages.value[aiMessageIndex].content += data.content
                            scrollToBottom()
                        }
                    } catch (e) {
                        console.warn('解析SSE数据失败:', e)
                    }
                }
            }
        }
    } catch (err) {
        console.error('AI回复失败', err)
        messages.value[aiMessageIndex].content = '抱歉，我暂时无法回复。请稍后再试。'
    } finally {
        loading.value = false
        await nextTick()
        if (textareaRef.value) {
            textareaRef.value.focus()
        }
    }
}

// 图片上传相关方法
const triggerFileInput = () => {
    fileInputRef.value?.click()
}

const handleImageUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // 检查文件类型
    if (!file.type.startsWith('image/')) {
        addMessage('请选择图片文件（JPG/PNG/GIF）', false)
        return
    }

    // 检查文件大小（10MB）
    if (file.size > 10 * 1024 * 1024) {
        addMessage('图片大小不能超过10MB', false)
        return
    }

    analyzingImage.value = true
    addMessage(`正在分析图片: ${file.name}`, true)

    try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('session_id', currentSessionId.value)

        const response = await request.post('/wound/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })

        const data = response.data

        if (data.need_confirmation && data.image_valid) {
            // 显示图片预览和确认问题
            pendingQuestions.value = data.questions || []
            waitingForAnswers.value = true
            
            let questionText = `📷 图片已接收并完成初步分析\n\n`
            questionText += `**初步发现：**\n`
            if (data.preliminary_findings?.suspected_body_part) {
                questionText += `- 可能部位：${data.preliminary_findings.suspected_body_part}\n`
                questionText += `- 置信度：${data.preliminary_findings.suspected_body_part_confidence}\n`
            }
            
            questionText += `\n**请回答以下问题以帮助我更准确地评估：**\n\n`
            data.questions.forEach((q, i) => {
                questionText += `${i + 1}. ${q.question}\n`
            })
            questionText += `\n请直接输入您的回答即可。`

            addMessage(questionText, false)
        } else if (!data.image_valid) {
            addMessage(`⚠️ 无法识别该图片：${data.invalid_reason || '请重新上传清晰的伤口照片'}`, false)
        }
        
    } catch (error) {
        console.error('图片分析失败:', error)
        addMessage('图片分析失败，请稍后重试', false)
    } finally {
        analyzingImage.value = false
        event.target.value = '' // 重置文件输入
    }
}

const handlePatientAnswer = async (answer) => {
    inputText.value = ''
    addMessage(answer, true)
    loading.value = true

    try {
        // 构建答案对象
        const answers = {}
        pendingQuestions.value.forEach((q, i) => {
            answers[String(i)] = answer
        })

        const response = await request.post('/wound/answers', {
            session_id: currentSessionId.value,
            answers: answers
        })

        const data = response.data

        let resultText = '📋 **伤口评估报告**\n\n'
        
        if (data.wound_assessment) {
            const wa = data.wound_assessment
            resultText += `**确认部位：** ${wa.confirmed_body_part}\n\n`
            
            if (wa.wound_assessment) {
                resultText += `**外观描述：** ${wa.wound_assessment.appearance}\n`
                resultText += `**渗液情况：** ${wa.wound_assessment.exudate}\n`
                resultText += `**周围皮肤：** ${wa.wound_assessment.surrounding_skin}\n`
            }
            
            resultText += `\n**愈合状态：** ${wa.healing_status}\n`
            
            if (wa.risk_alerts?.length > 0) {
                resultText += `\n⚠️ **风险提示：**\n`
                wa.risk_alerts.forEach(alert => {
                    resultText += `- ${alert}\n`
                })
            }
            
            if (wa.recommendation) {
                resultText += `\n💡 **建议措施：** ${wa.recommendation}\n`
            }
        }

        addMessage(resultText, false)
        
        // 重置状态
        waitingForAnswers.value = false
        pendingQuestions.value = []
        
    } catch (error) {
        console.error('处理回答失败:', error)
        addMessage('处理失败，请稍后重试', false)
    } finally {
        loading.value = false
    }
}

const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
    }
}

const startNewChat = async () => {
    if (aiSessionId.value) {
        try {
            await request.post('/ai/end-session', {
                session_id: aiSessionId.value
            })
        } catch (err) {
            console.error('结束AI会话失败', err)
        }
    }
    
    messages.value = []
    chatTitle.value = 'AI 智能导诊'
    aiSessionId.value = ''
    
    await createAISession()
    fetchHistoryList()
}

const openSettings = async () => {
    showProfileMenu.value = false
    showSettingsDialog.value = true
    settingsActiveTab.value = 'general'
    
    try {
        const res = await request.get('/user/info')
        const userData = res.data
        userInfo.value = {
            username: userData.username || '',
            phone_number: userData.phone_number || '',
            password: '',
            confirmPassword: '',
            avatar_url: userData.avatar_url || '',
            gender: userData.gender || '',
            birth: userData.birth || '',
            ethnicity: userData.ethnicity || '',
            origin: userData.origin || '',
            email: userData.email || ''
        }
        responsibleDoctor.value = userData.responsible_doctor
        surgeryRecords.value = userData.surgery_records || []
    } catch (err) {
        console.error('获取用户信息失败', err)
        userInfo.value = {
            username: authStore.user?.username || '',
            phone_number: authStore.user?.phone_number || '',
            password: '',
            confirmPassword: '',
            avatar_url: authStore.user?.avatar_url || '',
            gender: '',
            birth: '',
            ethnicity: '',
            origin: '',
            email: ''
        }
    }
}

const closeSettings = () => {
    showSettingsDialog.value = false
}

const setTheme = (theme) => {
    isDarkMode.value = theme === 'dark'
}

const triggerAvatarUpload = () => {
    avatarInputRef.value?.click()
}

const handleAvatarUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件')
        return
    }

    if (file.size > 5 * 1024 * 1024) {
        alert('图片大小不能超过5MB')
        return
    }

    uploadingAvatar.value = true
    try {
        const formData = new FormData()
        formData.append('file', file)

        const res = await request.post('/user/avatar', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })

        userInfo.value.avatar_url = res.data.avatar_url
        authStore.user = { ...authStore.user, avatar_url: res.data.avatar_url }
        localStorage.setItem('user', JSON.stringify(authStore.user))
        alert('头像上传成功')
    } catch (err) {
        console.error('头像上传失败', err)
        alert('头像上传失败')
    } finally {
        uploadingAvatar.value = false
        event.target.value = ''
    }
}

const saveUserInfo = async () => {
    const hasPassword = userInfo.value.password && userInfo.value.password.trim()
    const hasConfirmPassword = userInfo.value.confirmPassword && userInfo.value.confirmPassword.trim()
    
    if (hasPassword && !hasConfirmPassword) {
        alert('请确认新密码')
        return
    }
    
    if (hasPassword && hasConfirmPassword && userInfo.value.password !== userInfo.value.confirmPassword) {
        alert('两次输入的密码不一致')
        return
    }

    try {
        const updateData = new URLSearchParams()
        if (userInfo.value.username) updateData.append('username', userInfo.value.username)
        if (hasPassword) updateData.append('password', userInfo.value.password.trim())
        if (userInfo.value.gender) updateData.append('gender', userInfo.value.gender)
        if (userInfo.value.birth) updateData.append('birth', userInfo.value.birth)
        if (userInfo.value.ethnicity) updateData.append('ethnicity', userInfo.value.ethnicity)
        if (userInfo.value.origin) updateData.append('origin', userInfo.value.origin)
        if (userInfo.value.email) updateData.append('email', userInfo.value.email)
        
        const res = await request.post('/user/update', updateData)
        authStore.user = { 
            ...authStore.user, 
            username: userInfo.value.username,
            gender: userInfo.value.gender,
            avatar_url: userInfo.value.avatar_url
        }
        localStorage.setItem('user', JSON.stringify(authStore.user))
        alert('保存成功')
    } catch (err) {
        console.error(err)
        alert('保存失败')
    }
}

const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
}

const deleteHistory = async (id) => {
    if (!confirm('确定要删除这条对话记录吗？')) return
    
    try {
        await request.delete(`/ai/sessions/${id}`)
        historyList.value = historyList.value.filter(item => item.id !== id)
        if (aiSessionId.value === id) {
            messages.value = []
            aiSessionId.value = ''
            await createAISession()
        }
    } catch (err) {
        console.error('删除失败', err)
        alert('删除失败')
    }
}

const goToProfile = () => {
    showProfileMenu.value = !showProfileMenu.value
}

const goToNotifications = () => {
    showProfileMenu.value = false
    showNotificationsDialog.value = true
}

const closeNotifications = () => {
    showNotificationsDialog.value = false
}

const markNotificationAsRead = (notification) => {
    notification.read = true
    selectedNotification.value = notification
}

const closeNotificationDetail = () => {
    selectedNotification.value = null
}

const markAllNotificationsAsRead = () => {
    notifications.value.forEach(n => n.read = true)
}

const formatNotificationTime = (date) => {
    const now = new Date()
    const diff = now - date
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 7) return `${days}天前`
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const getNotificationTypeInfo = (type) => {
    const types = {
        appointment: { 
            color: '#1677ff', 
            bg: 'linear-gradient(135deg, #1677ff 0%, #4096ff 100%)',
            label: '预约' 
        },
        system: { 
            color: '#722ed1', 
            bg: 'linear-gradient(135deg, #722ed1 0%, #9254de 100%)',
            label: '系统' 
        }
    }
    return types[type] || { color: '#666', bg: '#666', label: '通知' }
}

const closeProfileMenu = () => {
    showProfileMenu.value = false
}

const goToAppointment = () => {
    router.push({ name: 'patient-appointment' })
}

const logout = () => {
    showProfileMenu.value = false
    authStore.logout()
    router.push({ name: 'login' })
}

const loadHistorySession = async (sessionId) => {
    try {
        loading.value = true
        const res = await request.get(`/ai/sessions/${sessionId}`)
        const data = res.data
        
        aiSessionId.value = sessionId
        chatTitle.value = data.session?.title || 'AI问诊'
        
        messages.value = data.messages.map(msg => ({
            id: msg.id,
            content: msg.content,
            isUser: msg.role === 'user',
            time: msg.time
        }))
        
        scrollToBottom()
    } catch (err) {
        console.error('加载历史会话失败', err)
        alert('加载会话失败，请重试')
    } finally {
        loading.value = false
    }
}

onMounted(async () => {
    fetchHistoryList()
    
    const sessionId = route.query.session_id
    if (sessionId) {
        await loadHistorySession(sessionId)
    } else {
        await createAISession()
    }
    
    isMobile.value = window.innerWidth <= 768
    sidebarCollapsed.value = isMobile.value
    
    window.addEventListener('resize', () => {
        isMobile.value = window.innerWidth <= 768
        if (isMobile.value) {
            sidebarCollapsed.value = true
        } else {
            sidebarCollapsed.value = false
        }
    })
})
</script>

<template>
  <div class="ds-chat" :class="{ 'dark-mode': isDarkMode, 'light-mode': !isDarkMode }">
    <aside class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="sidebar-top">
        <div class="sidebar-logo">
          <img src="../../img/logo.png" class="logo-img" alt="logo" />
          <button v-if="!sidebarCollapsed" class="sidebar-toggle" @click="toggleSidebar">
            <el-icon><ArrowLeft /></el-icon>
          </button>
        </div>
        
        <button v-if="sidebarCollapsed" class="expand-btn" @click="toggleSidebar" title="展开侧边栏">
          <el-icon><Expand /></el-icon>
        </button>
        
        <button class="new-chat-btn" @click="startNewChat" :title="sidebarCollapsed ? '开启新导诊' : ''">
          <el-icon><Plus /></el-icon>
          <span v-if="!sidebarCollapsed">开启新导诊</span>
        </button>
      </div>
      
      <div class="sidebar-history" v-if="!sidebarCollapsed">
        <div class="history-list" v-if="todayHistory.length > 0">
          <div class="history-group-title">今天</div>
          <div
            v-for="item in todayHistory"
            :key="item.id"
            class="history-item"
            @click="loadHistorySession(item.id)"
          >
            <div class="history-info">
              <div class="history-name">{{ item.title }}</div>
              <div class="history-time">{{ item.time }}</div>
            </div>
            <button class="delete-btn" @click.stop="deleteHistory(item.id)">
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
        <div class="history-list" v-if="weekHistory.length > 0">
          <div class="history-group-title">七天内</div>
          <div
            v-for="item in weekHistory"
            :key="item.id"
            class="history-item"
            @click="loadHistorySession(item.id)"
          >
            <div class="history-info">
              <div class="history-name">{{ item.title }}</div>
              <div class="history-time">{{ item.time }}</div>
            </div>
            <button class="delete-btn" @click.stop="deleteHistory(item.id)">
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
        <div class="history-list" v-if="olderHistory.length > 0">
          <div class="history-group-title">更早</div>
          <div
            v-for="item in olderHistory"
            :key="item.id"
            class="history-item"
            @click="loadHistorySession(item.id)"
          >
            <div class="history-info">
              <div class="history-name">{{ item.title }}</div>
              <div class="history-time">{{ item.time }}</div>
            </div>
            <button class="delete-btn" @click.stop="deleteHistory(item.id)">
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
        <div class="history-empty" v-if="historyList.length === 0">
          暂无历史对话
        </div>
      </div>
      
      <div class="sidebar-bottom">
        <button class="appointment-btn" v-if="!sidebarCollapsed" @click="goToAppointment">
          <el-icon class="appointment-icon"><Calendar /></el-icon>
          <span class="appointment-text">挂号预约</span>
          <el-icon class="appointment-arrow"><ArrowRight /></el-icon>
        </button>
        
        <button v-if="sidebarCollapsed" class="appointment-avatar-mini" @click="goToAppointment" title="挂号预约">
          <el-icon><Calendar /></el-icon>
        </button>
        
        <div class="user-area-wrapper" v-if="!sidebarCollapsed">
          <div class="user-area" @click="goToProfile">
            <div class="user-avatar">
              <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" alt="头像" class="user-avatar-img" />
              <el-icon v-else><User /></el-icon>
            </div>
            <div class="user-info">
              <div class="user-name">{{ authStore.user?.username || '未登录' }}</div>
            </div>
          </div>
          
          <div v-if="showProfileMenu" class="profile-menu">
            <div class="profile-menu-item" @click="openSettings">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </div>
            <div class="profile-menu-item" @click="goToNotifications">
              <el-icon><Bell /></el-icon>
              <span>消息通知</span>
              <span v-if="notificationCount > 0" class="menu-badge">{{ notificationCount }}</span>
            </div>
            <div class="profile-menu-item logout-item" @click="logout">
              <el-icon><SwitchButton /></el-icon>
              <span>退出登录</span>
            </div>
          </div>
        </div>
        
        <div class="user-mini-wrapper" v-if="sidebarCollapsed">
          <button class="user-avatar-mini" @click="goToProfile" title="个人中心">
            <el-icon><User /></el-icon>
          </button>
          
          <div v-if="showProfileMenu" class="profile-menu profile-menu-mini">
            <div class="profile-menu-item" @click="openSettings">
              <el-icon><Setting /></el-icon>
              <span>系统设置</span>
            </div>
            <div class="profile-menu-item logout-item" @click="logout">
              <el-icon><SwitchButton /></el-icon>
              <span>退出登录</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
    
    <div v-if="isMobile && !sidebarCollapsed" class="sidebar-overlay" @click="toggleSidebar"></div>

    <div class="main-area">
      <header class="ds-header">
        <div class="header-left">
          <button @click="toggleSidebar" class="nav-btn mobile-toggle">
            <el-icon><Expand /></el-icon>
          </button>
        </div>
        
        <div class="header-center">
          <span class="chat-title">{{ chatTitle }}</span>
        </div>
        
        <div class="header-right">
        </div>
      </header>

      <main class="ds-main" ref="chatContainer">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">
            <el-icon><Service /></el-icon>
          </div>
          <h2>AI 智能导诊助手</h2>
          <p>我可以帮您分析症状、推荐科室、提供健康建议</p>
          
          <div class="quick-actions">
            <button 
              v-for="suggestion in ['头痛怎么办', '发烧如何处理', '胃痛挂什么科', '咳嗽多久该就医']" 
              :key="suggestion"
              @click="inputText = suggestion; handleSend()"
              class="suggestion-chip"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>

        <div v-else class="messages-list">
          <div 
            v-for="msg in messages" 
            :key="msg.id" 
            class="msg-row"
            :class="{ 'user-row': msg.isUser }"
          >
            <template v-if="!msg.isUser">
              <div class="ai-message-wrapper">
                <div class="ai-header">
                  <span class="ai-label">AI智能导诊助手</span>
                </div>
                <div class="ai-content">
                  <pre class="message-text">{{ msg.content }}</pre>
                </div>
                <span class="msg-time">{{ msg.time }}</span>
              </div>
            </template>
            <template v-else>
              <div class="msg-avatar user-msg-avatar">
                <img v-if="authStore.user?.avatar_url" :src="authStore.user.avatar_url" alt="头像" class="user-avatar-img" />
                <el-icon v-else class="user-avatar-icon"><UserFilled /></el-icon>
              </div>
              <div class="msg-body user-msg-body">
                <div class="user-message">
                  <pre class="message-text">{{ msg.content }}</pre>
                </div>
                <span class="msg-time">{{ msg.time }}</span>
              </div>
            </template>
          </div>
          
          <div v-if="loading" class="msg-row ai-row">
            <div class="ai-message-wrapper">
              <div class="ai-header">
                <span class="ai-label">AI智能导诊助手</span>
              </div>
              <div class="typing-bubble">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer class="ds-footer">
        <div class="input-box">
          <input
            type="file"
            ref="fileInputRef"
            @change="handleImageUpload"
            accept="image/*"
            style="display: none"
          />
          
          <textarea 
            ref="textareaRef"
            v-model="inputText"
            @keydown="handleKeyDown"
            :placeholder="waitingForAnswers ? '请回答上述问题...' : '输入您的症状或问题...'"
            rows="2"
            :disabled="loading"
          ></textarea>
          
          <button 
            class="image-btn" 
            @click="triggerFileInput"
            :disabled="loading || analyzingImage"
            title="上传伤口图片"
          >
            <el-icon v-if="!analyzingImage"><PictureFilled /></el-icon>
            <el-icon v-else class="loading-icon"><Loading /></el-icon>
          </button>
          
          <button 
            class="send-btn" 
            @click="handleSend"
            :disabled="!inputText.trim() || loading"
          >
            <el-icon><Promotion /></el-icon>
          </button>
        </div>
      </footer>
    </div>

    <div v-if="showSettingsDialog" class="settings-overlay" @click="closeSettings">
      <div class="settings-dialog" @click.stop>
        <div class="settings-sidebar">
          <h3 class="settings-title">系统设置</h3>
          <div class="settings-menu">
            <div 
              class="settings-menu-item" 
              :class="{ active: settingsActiveTab === 'general' }"
              @click="settingsActiveTab = 'general'"
            >
              <el-icon><Setting /></el-icon>
              <span>通用设置</span>
            </div>
            <div 
              class="settings-menu-item" 
              :class="{ active: settingsActiveTab === 'account' }"
              @click="settingsActiveTab = 'account'"
            >
              <el-icon><User /></el-icon>
              <span>账号管理</span>
            </div>
            <div 
              class="settings-menu-item" 
              :class="{ active: settingsActiveTab === 'agreement' }"
              @click="settingsActiveTab = 'agreement'"
            >
              <el-icon><Document /></el-icon>
              <span>服务协议</span>
            </div>
          </div>
        </div>
        
        <div class="settings-content">
          <div class="settings-header">
            <h2>{{ settingsActiveTab === 'general' ? '通用设置' : settingsActiveTab === 'account' ? '账号管理' : '服务协议' }}</h2>
            <button class="settings-close" @click="closeSettings">
              <el-icon><Close /></el-icon>
            </button>
          </div>
          
          <div class="settings-body">
            <div v-if="settingsActiveTab === 'general'" class="general-settings">
              <div class="setting-item">
                <div class="setting-label">主题模式</div>
                <div class="theme-options">
                  <div 
                    class="theme-option" 
                    :class="{ active: !isDarkMode }"
                    @click="setTheme('light')"
                  >
                    <div class="theme-preview light-preview"></div>
                    <span>浅色</span>
                  </div>
                  <div 
                    class="theme-option" 
                    :class="{ active: isDarkMode }"
                    @click="setTheme('dark')"
                  >
                    <div class="theme-preview dark-preview"></div>
                    <span>深色</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="settingsActiveTab === 'account'" class="account-settings">
              <div class="avatar-section">
                <div class="avatar-preview" @click="triggerAvatarUpload">
                  <img v-if="userInfo.avatar_url" :src="userInfo.avatar_url" alt="头像" class="avatar-img" />
                  <el-icon v-else class="avatar-placeholder"><User /></el-icon>
                  <div class="avatar-overlay">
                    <span v-if="!uploadingAvatar">更换头像</span>
                    <span v-else>上传中...</span>
                  </div>
                </div>
                <input ref="avatarInputRef" type="file" accept="image/*" @change="handleAvatarUpload" style="display: none" />
              </div>
              
              <div class="form-item">
                <label>用户名</label>
                <input v-model="userInfo.username" type="text" placeholder="请输入用户名" />
              </div>
              <div class="form-item">
                <label>手机号</label>
                <input v-model="userInfo.phone_number" type="text" placeholder="请输入手机号" disabled />
              </div>
              <div class="form-item">
                <label>性别</label>
                <select v-model="userInfo.gender" class="form-select">
                  <option value="">请选择</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>
              <div class="form-item">
                <label>出生日期</label>
                <input v-model="userInfo.birth" type="date" placeholder="请选择出生日期" />
              </div>
              <div class="form-item">
                <label>民族</label>
                <input v-model="userInfo.ethnicity" type="text" placeholder="请输入民族" />
              </div>
              <div class="form-item">
                <label>籍贯</label>
                <input v-model="userInfo.origin" type="text" placeholder="请输入籍贯" />
              </div>
              <div class="form-item">
                <label>邮箱</label>
                <input v-model="userInfo.email" type="email" placeholder="请输入邮箱" autocomplete="off" />
              </div>
              <div class="form-item">
                <label>新密码</label>
                <input v-model="userInfo.password" type="password" placeholder="请输入新密码（不修改请留空）" autocomplete="new-password" />
              </div>
              <div v-if="userInfo.password" class="form-item">
                <label>确认密码</label>
                <input v-model="userInfo.confirmPassword" type="password" placeholder="请再次输入新密码" autocomplete="new-password" />
              </div>
              
              <div v-if="responsibleDoctor" class="doctor-section">
                <label class="section-label">负责医生 <span class="readonly-hint">(系统分配，不可修改)</span></label>
                <div class="doctor-card">
                  <div class="doctor-avatar">
                    <el-icon><User /></el-icon>
                  </div>
                  <div class="doctor-info">
                    <div class="doctor-name">{{ responsibleDoctor.username }}</div>
                    <div class="doctor-detail">
                      <span v-if="responsibleDoctor.department_name">{{ responsibleDoctor.department_name }}</span>
                      <span v-if="responsibleDoctor.department_name && responsibleDoctor.title"> · </span>
                      <span>{{ responsibleDoctor.title || '医生' }}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="surgeryRecords.length > 0" class="surgery-section">
                <label class="section-label">手术记录 <span class="readonly-hint">(系统记录，不可修改)</span></label>
                <div class="surgery-list">
                  <div v-for="surgery in surgeryRecords" :key="surgery.id" class="surgery-item">
                    <div class="surgery-info">
                      <div class="surgery-name">{{ surgery.surgery_name }}</div>
                      <div class="surgery-hospital" v-if="surgery.hospital">{{ surgery.hospital }}</div>
                    </div>
                    <div class="surgery-date">{{ surgery.surgery_date }}</div>
                  </div>
                </div>
              </div>
              
              <button class="save-btn" @click="saveUserInfo">保存修改</button>
            </div>
            
            <div v-if="settingsActiveTab === 'agreement'" class="agreement-settings">
              <div class="agreement-content">
                <h4>用户服务协议</h4>
                <p>欢迎使用CareLink智能医疗服务平台。在使用本服务前，请仔细阅读以下协议：</p>
                <h5>一、服务内容</h5>
                <p>本平台提供AI智能导诊、在线预约、健康咨询等服务。所有医疗建议仅供参考，不能替代专业医生的诊断和治疗。</p>
                <h5>二、用户责任</h5>
                <p>1. 用户应提供真实、准确的个人信息。</p>
                <p>2. 用户不得利用本平台从事违法违规活动。</p>
                <p>3. 用户应妥善保管账号密码，对账号安全负责。</p>
                <h5>三、隐私保护</h5>
                <p>我们重视用户隐私保护，将按照相关法律法规保护用户个人信息。未经用户同意，不会向第三方披露用户信息。</p>
                <h5>四、免责声明</h5>
                <p>本平台提供的医疗建议仅供参考，不构成医疗诊断。如有健康问题，请及时就医。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showNotificationsDialog" class="notifications-overlay" @click="closeNotifications">
      <div class="notifications-dialog" @click.stop>
        <div class="notifications-header">
          <h2>消息通知</h2>
          <div class="header-actions">
            <span v-if="notificationCount > 0" class="unread-badge">{{ notificationCount }}条未读</span>
            <button v-if="notificationCount > 0" class="mark-all-btn" @click="markAllNotificationsAsRead">
              全部已读
            </button>
            <button class="close-btn" @click="closeNotifications">
              <el-icon><Close /></el-icon>
            </button>
          </div>
        </div>
        
        <div class="notifications-body">
          <div v-if="notifications.length === 0" class="empty-state">
            <div class="empty-icon">
              <el-icon><Bell /></el-icon>
            </div>
            <p>暂无消息</p>
          </div>
          
          <div v-else class="notification-list">
            <div 
              v-for="notification in notifications" 
              :key="notification.id" 
              class="notification-item"
              :class="{ unread: !notification.read }"
              @click="markNotificationAsRead(notification)"
            >
              <div class="item-icon" :style="{ background: getNotificationTypeInfo(notification.type).bg }">
                <el-icon v-if="notification.type === 'appointment'"><Calendar /></el-icon>
                <el-icon v-else-if="notification.type === 'system'"><Bell /></el-icon>
                <el-icon v-else><Document /></el-icon>
              </div>
              
              <div class="item-content">
                <div class="item-header">
                  <span class="item-type" :style="{ color: getNotificationTypeInfo(notification.type).color }">
                    {{ getNotificationTypeInfo(notification.type).label }}
                  </span>
                  <span class="item-time">{{ formatNotificationTime(notification.time) }}</span>
                </div>
                <h4 class="item-title">{{ notification.title }}</h4>
                <p class="item-text">{{ notification.content }}</p>
              </div>
              
              <div v-if="!notification.read" class="unread-dot"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="selectedNotification" class="notification-detail-overlay" @click="closeNotificationDetail">
      <div class="notification-detail-dialog" @click.stop>
        <div class="detail-header">
          <div class="detail-icon" :style="{ background: getNotificationTypeInfo(selectedNotification.type).bg }">
            <el-icon v-if="selectedNotification.type === 'appointment'"><Calendar /></el-icon>
            <el-icon v-else-if="selectedNotification.type === 'system'"><Bell /></el-icon>
            <el-icon v-else><Document /></el-icon>
          </div>
          <div class="detail-meta">
            <span class="detail-type" :style="{ color: getNotificationTypeInfo(selectedNotification.type).color }">
              {{ getNotificationTypeInfo(selectedNotification.type).label }}
            </span>
            <span class="detail-time">{{ formatNotificationTime(selectedNotification.time) }}</span>
          </div>
          <button class="detail-close" @click="closeNotificationDetail">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        
        <div class="detail-body">
          <h3 class="detail-title">{{ selectedNotification.title }}</h3>
          <p class="detail-content">{{ selectedNotification.content }}</p>
          <div v-if="selectedNotification.detail" class="detail-extra">
            <el-icon><InfoFilled /></el-icon>
            <span>{{ selectedNotification.detail }}</span>
          </div>
        </div>
        
        <div class="detail-footer">
          <button class="detail-btn primary" @click="closeNotificationDetail">我知道了</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ds-chat {
    width: 100%;
    height: 100vh;
    display: flex;
    transition: background 0.3s ease;
}

.dark-mode { background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%); }
.light-mode { background: linear-gradient(135deg, #e8f4ff 0%, #ffffff 50%, #e8f4ff 100%); }

.sidebar {
    width: 280px;
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
    flex-shrink: 0;
}

.sidebar.collapsed { width: 68px; }

.sidebar-overlay {
    display: none;
}

.dark-mode .sidebar { background: rgba(30, 30, 30, 0.85); border-right: 1px solid rgba(255, 255, 255, 0.08); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); }
.light-mode .sidebar { background: rgba(255, 255, 255, 0.92); border-right: 1px solid rgba(255, 255, 255, 0.5); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px); box-shadow: 4px 0 20px rgba(0, 0, 0, 0.06); }

.sidebar-top {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 4px 0;
    width: 100%;
    justify-content: space-between;
}

.sidebar.collapsed .sidebar-logo {
    justify-content: center;
}

.logo-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    background: linear-gradient(135deg, #4f8cff, #6c5ce7);
    color: #fff;
    flex-shrink: 0;
}

.logo-img {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    object-fit: contain;
    flex-shrink: 0;
}

.logo-text {
    flex: 1;
    font-size: 18px;
    font-weight: 600;
}

.dark-mode .logo-text { color: #ececec; }
.light-mode .logo-text { color: #1a1a1a; }

.sidebar-toggle {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    transition: all 0.2s;
}

.dark-mode .sidebar-toggle {
    background: #fff;
    color: #333;
}
.dark-mode .sidebar-toggle:hover {
    background: #f0f0f0;
    color: #333;
}

.light-mode .sidebar-toggle {
    background: #fff;
    color: #666;
}
.light-mode .sidebar-toggle:hover {
    background: #f0f0f0;
    color: #333;
}

.expand-btn {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    transition: all 0.3s ease;
    background: transparent;
}

.dark-mode .expand-btn {
    color: #fff;
}
.dark-mode .expand-btn:hover {
    background: rgba(255, 255, 255, 0.1);
}

.light-mode .expand-btn {
    color: #333;
}
.light-mode .expand-btn:hover {
    background: rgba(0, 0, 0, 0.05);
}

.new-chat-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 16px;
    border-radius: 25px;
    border: none;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #fff;
    color: #333;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.sidebar.collapsed .new-chat-btn {
    padding: 12px;
    background: transparent;
    box-shadow: none;
}

.dark-mode .sidebar.collapsed .new-chat-btn {
    color: #fff;
}

.light-mode .sidebar.collapsed .new-chat-btn {
    color: #333;
}

.dark-mode .sidebar.collapsed .new-chat-btn:hover {
    background: transparent;
    transform: none;
    box-shadow: none;
}

.light-mode .sidebar.collapsed .new-chat-btn:hover {
    background: transparent;
    transform: none;
    box-shadow: none;
}

.dark-mode .new-chat-btn {
    background: rgba(255,255,255,0.95);
    color: #333;
}
.dark-mode .new-chat-btn:hover {
    background: #fff;
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.light-mode .new-chat-btn {
    background: #fff;
    color: #333;
}
.light-mode .new-chat-btn:hover {
    background: #fff;
    transform: translateY(-5px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.sidebar-history {
    flex: 1;
    overflow-y: auto;
    padding: 0 12px;
}

.dark-mode .sidebar-history { background: rgba(32, 33, 35, 0.15); }
.light-mode .sidebar-history { background: rgba(255, 255, 255, 0.08); }

.history-title {
    font-size: 12px;
    font-weight: 500;
    padding: 8px 4px;
    margin-bottom: 4px;
}

.history-group-title {
    font-size: 12px;
    font-weight: 600;
    padding: 8px 4px 4px;
    color: #999;
}

.history-empty {
    font-size: 13px;
    color: #aaa;
    text-align: center;
    padding: 20px 0;
}

.dark-mode .history-title { color: #666; }
.light-mode .history-title { color: #999; }

.history-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.history-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 25px;
    cursor: pointer;
    transition: all 0.2s;
}

.dark-mode .history-item:hover { background: rgba(255,255,255,0.05); }
.light-mode .history-item:hover { background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

.history-icon {
    font-size: 18px;
}

.dark-mode .history-icon { color: #666; }
.light-mode .history-icon { color: #aaa; }

.history-info { flex: 1; min-width: 0; }

.history-name {
    font-size: 15px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dark-mode .history-name { color: #ccc; }
.light-mode .history-name { color: #333; }

.history-time {
    font-size: 12px;
    margin-top: 2px;
}

.dark-mode .history-time { color: #555; }
.light-mode .history-time { color: #aaa; }

.delete-btn {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    opacity: 0;
    transition: all 0.2s;
    flex-shrink: 0;
}

.history-item:hover .delete-btn {
    opacity: 1;
}

.dark-mode .delete-btn {
    background: transparent;
    color: #666;
}
.dark-mode .delete-btn:hover {
    background: rgba(255,100,100,0.15);
    color: #ff6b6b;
}

.light-mode .delete-btn {
    background: transparent;
    color: #aaa;
}
.light-mode .delete-btn:hover {
    background: rgba(255,100,100,0.1);
    color: #ff4757;
}

.sidebar-bottom {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 15px;
    align-items: center;
}

.dark-mode .sidebar-bottom { background: rgba(32, 33, 35, 0.15); }
.light-mode .sidebar-bottom { background: rgba(255, 255, 255, 0.08); }

.appointment-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    background: transparent;
    width: 100%;
    font-size: inherit;
}

.dark-mode .appointment-btn:hover { background: rgba(255,255,255,0.05); }
.light-mode .appointment-btn:hover { background: #f5f5f5; }

.appointment-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    background: linear-gradient(135deg, #4f8cff, #6c5ce7);
    color: #fff;
    flex-shrink: 0;
}

.appointment-text {
    flex: 1;
    font-size: 15px;
    font-weight: 500;
    text-align: left;
}

.dark-mode .appointment-text { color: #ececec; }
.light-mode .appointment-text { color: #333; }

.user-area-wrapper {
    position: relative;
    width: 100%;
}

.user-mini-wrapper {
    position: relative;
    display: flex;
    justify-content: center;
}

.profile-menu {
    position: absolute;
    bottom: 100%;
    left: 0;
    margin-bottom: 8px;
    min-width: 140px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    padding: 8px 0;
    z-index: 100;
}

.profile-menu-mini {
    left: calc(100% + 18px);
    bottom: -40px;
    transform: none;
    margin-bottom: 0;
    min-width: 160px;
}

.profile-menu-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 14px;
    color: #333;
}

.profile-menu-item:hover {
    background: #f5f5f5;
}

.profile-menu-item .el-icon {
    font-size: 18px;
}

.logout-item {
    color: #ff4757;
}

.logout-item:hover {
    background: #fff5f5;
}

.menu-badge {
    margin-left: auto;
    min-width: 18px;
    height: 18px;
    border-radius: 9px;
    background: #ff4757;
    color: #fff;
    font-size: 11px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 6px;
}

.user-area {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
}

.dark-mode .user-area:hover { background: rgba(255,255,255,0.05); }
.light-mode .user-area:hover { background: #f5f5f5; }

.user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    background: linear-gradient(135deg, #00b894, #00cec9);
    color: #fff;
    flex-shrink: 0;
    overflow: hidden;
}

.user-avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.user-avatar-mini {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    background: linear-gradient(135deg, #00b894, #00cec9);
    color: #fff;
    cursor: pointer;
    flex-shrink: 0;
}

.appointment-avatar-mini {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    background: linear-gradient(135deg, #4f8cff, #6c5ce7);
    color: #fff;
    cursor: pointer;
    flex-shrink: 0;
}

.user-info { flex: 1; min-width: 0; }

.user-name {
    font-size: 14px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dark-mode .user-name { color: #ececec; }
.light-mode .user-name { color: #1a1a1a; }

.user-arrow {
    font-size: 18px;
    transition: transform 0.2s;
}

.dark-mode .user-arrow { color: #666; }
.light-mode .user-arrow { color: #aaa; }

.user-area:hover .user-arrow {
    transform: translateX(2px);
}

.appointment-arrow {
    font-size: 18px;
    transition: transform 0.2s;
}

.dark-mode .appointment-arrow { color: #666; }
.light-mode .appointment-arrow { color: #aaa; }

.appointment-btn:hover .appointment-arrow {
    transform: translateX(2px);
}

.main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.ds-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    border-bottom: 1px solid transparent;
    transition: all 0.3s ease;
}

.dark-mode .ds-header { background: rgba(26, 26, 26, 0.9); border-color: rgba(45, 45, 48, 0.8); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
.light-mode .ds-header { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.2); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); box-shadow: 0 4px 30px rgba(0, 0, 0, 0.08); }

.header-left,
.header-right { display: flex; align-items: center; gap: 8px; }

.header-center { flex: 1; display: flex; justify-content: center; }

.chat-title {
    font-size: 16px;
    font-weight: 600;
}

.dark-mode .chat-title { color: #ececec; }
.light-mode .chat-title { color: #1a1a1a; }

.nav-btn,
.theme-btn {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    transition: all 0.2s;
}

.dark-mode .nav-btn,
.dark-mode .theme-btn {
    background: transparent;
    color: #8e8ea0;
}
.dark-mode .nav-btn:hover,
.dark-mode .theme-btn:hover {
    background: rgba(255,255,255,0.1);
    color: #fff;
}

.light-mode .nav-btn,
.light-mode .theme-btn {
    background: transparent;
    color: #666;
}
.light-mode .nav-btn:hover,
.light-mode .theme-btn:hover {
    background: #f0f0f0;
    color: #333;
}

.mobile-toggle { display: none; }

.ds-main {
    flex: 1;
    overflow-y: auto;
    padding: 0;
}

.ds-main::-webkit-scrollbar { width: 6px; }
.dark-mode .ds-main::-webkit-scrollbar-thumb { background: #3a3a3c; border-radius: 3px; }
.light-mode .ds-main::-webkit-scrollbar-thumb { background: #d9d9d9; border-radius: 3px; }

.empty-state {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
}

.empty-icon {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    margin-bottom: 24px;
}

.dark-mode .empty-icon {
    background: linear-gradient(135deg, rgba(79,140,255,0.15), rgba(108,92,231,0.15));
    color: #4f8cff;
}

.light-mode .empty-icon {
    background: linear-gradient(135deg, rgba(22,119,255,0.1), rgba(114,46,209,0.1));
    color: #1677ff;
}

.empty-state h2 {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 8px;
}

.empty-state p {
    font-size: 15px;
    margin-bottom: 28px;
}

.dark-mode .empty-state h2 { color: #ececec; }
.dark-mode .empty-state p { color: #8e8ea0; }
.light-mode .empty-state h2 { color: #1a1a1a; }
.light-mode .empty-state p { color: #888; }

.quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
    max-width: 500px;
}

.suggestion-chip {
    padding: 10px 18px;
    border-radius: 20px;
    border: none;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.dark-mode .suggestion-chip {
    background: rgba(255,255,255,0.06);
    color: #b4b4b4;
    border: 1px solid rgba(255,255,255,0.1);
}
.dark-mode .suggestion-chip:hover {
    background: rgba(79,140,255,0.12);
    color: #4f8cff;
    border-color: rgba(79,140,255,0.25);
}

.light-mode .suggestion-chip {
    background: #fff;
    color: #555;
    border: 1px solid #e5e5e5;
}
.light-mode .suggestion-chip:hover {
    background: #f0f6ff;
    color: #1677ff;
    border-color: #1677ff;
}

.messages-list {
    padding: 24px 20px;
    max-width: 800px;
    margin: 0 auto;
}

.msg-row {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
}

.msg-row.user-row {
    flex-direction: row-reverse;
}

.msg-avatar {
    flex-shrink: 0;
}

.ai-avatar,
.user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.ai-avatar {
    background: linear-gradient(135deg, #4f8cff, #6c5ce7);
    color: #fff;
}

.user-avatar {
    background: #00b894;
    color: #fff;
}

.ai-message-wrapper {
    flex: 1;
    max-width: 70%;
}

.ai-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.ai-label {
    font-size: 16px;
    font-weight: 600;
}

.dark-mode .ai-label { color: #ececec; }
.light-mode .ai-label { color: #333; }

.ai-content {
    line-height: 1.8;
}

.ai-content p {
    margin: 0;
    font-size: 18px;
}

.message-text {
    margin: 0;
    font-family: inherit;
    font-size: 15px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-wrap: break-word;
}

.dark-mode .ai-content { color: #ececec; }
.light-mode .ai-content { color: #333; }

.msg-body {
    flex: 1;
    max-width: 70%;
}

.msg-bubble {
    padding: 14px 18px;
    border-radius: 16px;
    line-height: 1.6;
}

.dark-mode .msg-bubble {
    background: #2f2f2f;
    color: #ececec;
}

.light-mode .msg-bubble {
    background: #f0f0f0;
    color: #1a1a1a;
}

.msg-bubble.user-bubble {
    background: linear-gradient(135deg, #4f8cff, #6c5ce7);
    color: #fff;
}

.msg-bubble p {
    margin: 0;
    font-size: 15px;
}

.msg-time {
    display: block;
    font-size: 11px;
    margin-top: 6px;
}

.dark-mode .msg-time { color: #555; }
.light-mode .msg-time { color: #aaa; }

.user-row .msg-time {
    text-align: right;
}

.user-msg-body {
    text-align: right;
}

.user-message {
    display: inline-block;
    text-align: left;
    line-height: 1.8;
    max-width: 100%;
}

.user-msg-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.user-msg-avatar .user-avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.user-msg-avatar .user-avatar-icon {
    width: 36px;
    height: 36px;
    background: #00b894;
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
}

.typing-bubble {
    display: flex;
    gap: 4px;
    padding: 8px 0;
    width: fit-content;
}

.dark-mode .typing-bubble { background: transparent; }
.light-mode .typing-bubble { background: transparent; }

.typing-bubble .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
}

.dark-mode .typing-bubble .dot { background: #666; }
.light-mode .typing-bubble .dot { background: #aaa; }

.typing-bubble .dot:nth-child(1) { animation-delay: 0s; }
.typing-bubble .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-bubble .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-4px); }
}

.ds-footer {
    padding: 16px 20px;
}

.input-box {
    display: flex;
    align-items: flex-end;
    gap: 12px;
    max-width: 800px;
    margin: 0 auto;
    padding: 12px 16px;
    border-radius: 25px;
    transition: all 0.2s;
    background: #fff;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.dark-mode .input-box {
    background: #2d2d2d;
}
.dark-mode .input-box:focus-within {
    background: #2d2d2d;
}

.light-mode .input-box {
    background: #fff;
}
.light-mode .input-box:focus-within {
    background: #fff;
}

.input-box textarea {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    font-size: 15px;
    line-height: 1.5;
    min-height: 98px;
    max-height: 200px;
    font-family: inherit;
}

.dark-mode .input-box textarea { color: #ececec; }
.light-mode .input-box textarea { color: #1a1a1a; }

.dark-mode .input-box textarea::placeholder { color: #666; }
.light-mode .input-box textarea::placeholder { color: #888; }

.send-btn {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    transition: all 0.2s;
    flex-shrink: 0;
}

.send-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.image-btn {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    transition: all 0.2s;
    flex-shrink: 0;
}

.image-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}

.dark-mode .image-btn {
    background: rgba(255,255,255,0.08);
    color: #8e8ea0;
}
.dark-mode .image-btn:hover:not(:disabled) {
    background: rgba(79,140,255,0.15);
    color: #4f8cff;
}

.light-mode .image-btn {
    background: #f5f5f5;
    color: #666;
}
.light-mode .image-btn:hover:not(:disabled) {
    background: #e8e8e8;
    color: #1677ff;
}

.loading-icon {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.dark-mode .send-btn {
    background: #4f8cff;
    color: #fff;
}
.dark-mode .send-btn:not(:disabled):hover {
    background: #3d7ae8;
}

.light-mode .send-btn {
    background: #1677ff;
    color: #fff;
}
.light-mode .send-btn:not(:disabled):hover {
    background: #0958d9;
}

@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        z-index: 100;
        transform: translateX(-100%);
    }
    
    .sidebar:not(.collapsed) {
        transform: translateX(0);
    }
    
    .sidebar.collapsed {
        transform: translateX(-100%);
    }
    
    .sidebar-overlay {
        display: block;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 99;
    }
    
    .mobile-toggle {
        display: flex;
    }
    
    .msg-body {
        max-width: 85%;
    }
}

.settings-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.settings-dialog {
    width: 800px;
    max-width: 90vw;
    height: 500px;
    max-height: 80vh;
    background: #fff;
    border-radius: 16px;
    display: flex;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.settings-sidebar {
    width: 200px;
    background: #f7f8fa;
    border-right: 1px solid #e5e6eb;
    padding: 20px 0;
    flex-shrink: 0;
}

.settings-title {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
    padding: 0 20px 20px;
    margin: 0;
    border-bottom: 1px solid #e5e6eb;
}

.settings-menu {
    padding: 10px 0;
}

.settings-menu-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    cursor: pointer;
    transition: all 0.2s;
    color: #666;
    font-size: 14px;
}

.settings-menu-item:hover {
    background: #eef0f3;
    color: #333;
}

.settings-menu-item.active {
    background: #e6f4ff;
    color: #1677ff;
}

.settings-menu-item .el-icon {
    font-size: 18px;
}

.settings-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid #e5e6eb;
}

.settings-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
}

.settings-close {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    border: none;
    background: transparent;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: #999;
    transition: all 0.2s;
}

.settings-close:hover {
    background: #f5f5f5;
    color: #333;
}

.settings-body {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
}

.setting-item {
    margin-bottom: 24px;
}

.setting-label {
    font-size: 14px;
    font-weight: 500;
    color: #333;
    margin-bottom: 12px;
}

.theme-options {
    display: flex;
    gap: 16px;
}

.theme-option {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px;
    border-radius: 12px;
    border: 2px solid #e5e6eb;
    cursor: pointer;
    transition: all 0.2s;
}

.theme-option:hover {
    border-color: #1677ff;
}

.theme-option.active {
    border-color: #1677ff;
    background: #e6f4ff;
}

.theme-preview {
    width: 80px;
    height: 50px;
    border-radius: 8px;
}

.light-preview {
    background: linear-gradient(135deg, #e8f4ff 0%, #ffffff 50%, #e8f4ff 100%);
    border: 1px solid #e5e6eb;
}

.dark-preview {
    background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%);
}

.theme-option span {
    font-size: 13px;
    color: #666;
}

.theme-option.active span {
    color: #1677ff;
}

.avatar-section {
    display: flex;
    justify-content: center;
    margin-bottom: 24px;
}

.avatar-preview {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: linear-gradient(135deg, #e8f4ff 0%, #f0f0f0 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    border: 3px solid #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transition: all 0.2s;
}

.avatar-preview:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.avatar-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.avatar-placeholder {
    font-size: 40px;
    color: #999;
}

.avatar-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(0, 0, 0, 0.6);
    color: #fff;
    font-size: 12px;
    padding: 4px 0;
    text-align: center;
    opacity: 0;
    transition: opacity 0.2s;
}

.avatar-preview:hover .avatar-overlay {
    opacity: 1;
}

.doctor-section, .surgery-section {
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #e5e5e5;
}

.section-label {
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin-bottom: 12px;
}

.readonly-hint {
    font-size: 12px;
    font-weight: 400;
    color: #999;
    margin-left: 4px;
}

.doctor-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: linear-gradient(135deg, #e8f4ff 0%, #f5f9ff 100%);
    border-radius: 12px;
    border: 1px solid rgba(22, 119, 255, 0.1);
}

.doctor-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 24px;
}

.doctor-info {
    flex: 1;
}

.doctor-name {
    font-size: 16px;
    font-weight: 600;
    color: #1a1a1a;
}

.doctor-detail {
    font-size: 13px;
    color: #666;
    margin-top: 2px;
}

.surgery-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.surgery-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e5e5e5;
}

.surgery-info {
    flex: 1;
}

.surgery-name {
    font-size: 14px;
    font-weight: 500;
    color: #333;
}

.surgery-hospital {
    font-size: 12px;
    color: #999;
    margin-top: 2px;
}

.surgery-date {
    font-size: 13px;
    color: #999;
}

.form-item {
    margin-bottom: 20px;
}

.form-item label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    color: #333;
    margin-bottom: 8px;
}

.form-item input {
    width: 100%;
    max-width: 400px;
    padding: 12px 16px;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    font-size: 14px;
    transition: all 0.2s;
    outline: none;
}

.form-item input:focus {
    border-color: #1677ff;
    box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.form-item input:disabled {
    background: #f5f5f5;
    color: #999;
    cursor: not-allowed;
}

.form-select {
    width: 100%;
    max-width: 400px;
    padding: 12px 16px;
    border: 1px solid #d9d9d9;
    border-radius: 8px;
    font-size: 14px;
    transition: all 0.2s;
    outline: none;
    background: #fff;
    cursor: pointer;
}

.form-select:focus {
    border-color: #1677ff;
    box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.1);
}

.save-btn {
    margin-top: 15px;
    padding: 12px 32px;
    background: #1677ff;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.save-btn:hover {
    background: #0958d9;
}

.agreement-content {
    max-width: 600px;
    line-height: 1.8;
    color: #333;
}

.agreement-content h4 {
    font-size: 18px;
    margin: 0 0 16px;
}

.agreement-content h5 {
    font-size: 15px;
    margin: 20px 0 10px;
    color: #1a1a1a;
}

.agreement-content p {
    font-size: 14px;
    color: #666;
    margin: 8px 0;
}

.notifications-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.notifications-dialog {
    width: 560px;
    max-width: 90vw;
    max-height: 80vh;
    background: #fff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
}

.notifications-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid #f0f0f0;
}

.notifications-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
}

.unread-badge {
    font-size: 12px;
    color: #1677ff;
    font-weight: 500;
}

.mark-all-btn {
    padding: 6px 12px;
    border: none;
    border-radius: 14px;
    background: #1677ff;
    color: #fff;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}

.mark-all-btn:hover {
    background: #0958d9;
}

.close-btn {
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 8px;
    background: #f5f5f5;
    color: #666;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.close-btn:hover {
    background: #e8e8e8;
    color: #333;
}

.notifications-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
}

.empty-icon {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f0f5ff 0%, #e6f4ff 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}

.empty-icon .el-icon {
    font-size: 36px;
    color: #1677ff;
    opacity: 0.6;
}

.empty-state p {
    font-size: 14px;
    color: #999;
    margin: 0;
}

.notification-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.notification-item {
    position: relative;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px;
    background: #fff;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    border: 1px solid #f0f0f0;
}

.notification-item:hover {
    background: #fafafa;
    border-color: #e6e6e6;
}

.notification-item.unread {
    background: #f6faff;
    border-color: #d6e4ff;
}

.notification-item.unread::before {
    content: '';
    position: absolute;
    left: 0;
    top: 14px;
    bottom: 14px;
    width: 3px;
    background: #1677ff;
    border-radius: 0 3px 3px 0;
}

.item-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: #fff;
    flex-shrink: 0;
}

.item-content {
    flex: 1;
    min-width: 0;
}

.item-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.item-type {
    font-size: 11px;
    font-weight: 600;
}

.item-time {
    font-size: 11px;
    color: #999;
}

.item-title {
    font-size: 14px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 4px;
    line-height: 1.4;
}

.item-text {
    font-size: 13px;
    color: #666;
    line-height: 1.5;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.item-detail {
    font-size: 11px;
    color: #999;
    margin: 6px 0 0;
    padding: 4px 8px;
    background: #f5f7fa;
    border-radius: 4px;
}

.unread-dot {
    position: absolute;
    top: 14px;
    right: 14px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #1677ff;
}

.notification-detail-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1100;
}

.notification-detail-dialog {
    width: 480px;
    max-width: 90vw;
    background: #fff;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 25px 80px rgba(0, 0, 0, 0.35);
}

.detail-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 24px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
}

.detail-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: #fff;
    flex-shrink: 0;
}

.detail-meta {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.detail-type {
    font-size: 13px;
    font-weight: 600;
}

.detail-time {
    font-size: 12px;
    color: #94a3b8;
}

.detail-close {
    width: 36px;
    height: 36px;
    border: none;
    border-radius: 10px;
    background: #fff;
    color: #64748b;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.detail-close:hover {
    background: #f1f5f9;
    color: #334155;
}

.detail-body {
    padding: 28px 24px;
}

.detail-title {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin: 0 0 16px;
    line-height: 1.4;
}

.detail-content {
    font-size: 15px;
    color: #475569;
    line-height: 1.8;
    margin: 0;
}

.detail-extra {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-top: 20px;
    padding: 16px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 12px;
    border: 1px solid #bae6fd;
}

.detail-extra .el-icon {
    font-size: 18px;
    color: #0284c7;
    margin-top: 2px;
    flex-shrink: 0;
}

.detail-extra span {
    font-size: 14px;
    color: #0369a1;
    line-height: 1.6;
}

.detail-footer {
    padding: 20px 24px;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: center;
}

.detail-btn {
    padding: 12px 48px;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.detail-btn.primary {
    background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
    color: #fff;
}

.detail-btn.primary:hover {
    background: linear-gradient(135deg, #0958d9 0%, #003eb3 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(22, 119, 255, 0.35);
}
</style>
