<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import request from '../../api/request'
import { PictureFilled, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const chatContainer = ref(null)
const textareaRef = ref(null)
const isDarkMode = ref(false)
const sidebarCollapsed = ref(false)

// 图片分析相关状态
const fileInputRef = ref(null)
const analyzingImage = ref(false)
const pendingQuestions = ref([])
const waitingForAnswers = ref(false)
const currentSessionId = ref(`sess_${Date.now()}`)

const historyList = ref([
    { id: 1, title: '头痛症状咨询', time: '今天 14:30' },
    { id: 2, title: '发烧处理建议', time: '昨天 09:15' },
    { id: 3, title: '胃痛科室推荐', time: '3天前' },
])

const userInfo = ref(authStore.user || { name: '用户', phone: '' })

const scrollToBottom = async () => {
    await nextTick()
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
}

const addMessage = (content, isUser = false) => {
    messages.value.push({
        id: Date.now(),
        content,
        isUser,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
    scrollToBottom()
}

const handleSend = async () => {
    const text = inputText.value.trim()
    if (!text || loading.value) return
    
    // 如果正在等待回答，处理患者回答
    if (waitingForAnswers.value) {
        await handlePatientAnswer(text)
        return
    }
    
    inputText.value = ''
    addMessage(text, true)
    loading.value = true
    
    setTimeout(async () => {
        const responses = [
            '根据您的描述，建议您前往内科就诊。请问还有其他症状吗？',
            '感谢您的详细描述。为了更准确地判断，请问您是否有发热的情况？',
            '我理解您的困扰。这种情况持续多久了？是否有过类似经历？',
            '根据症状分析，您可能需要做一些检查。请问您的年龄大概是多少？',
            '好的，我已经记录下来。请问这些症状是突然出现的还是逐渐加重的？',
            '了解。请问您最近有没有服用什么药物？',
            '收到，我会继续为您分析。还有其他需要补充的信息吗？'
        ]
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)]
        addMessage(randomResponse, false)
        loading.value = false
        
        await nextTick()
        if (textareaRef.value) {
            textareaRef.value.focus()
        }
    }, 800 + Math.random() * 1200)
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

const startNewChat = () => {
    if (messages.value.length > 1) {
        const firstUserMsg = messages.value.find(m => m.isUser)
        const title = firstUserMsg ? firstUserMsg.content.slice(0, 15) + (firstUserMsg.content.length > 15 ? '...' : '') : '新对话'
        historyList.value.unshift({
            id: Date.now(),
            title,
            time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
        })
    }
    messages.value = []
    setTimeout(() => {
        addMessage('您好！我是 AI 智能导诊助手。请告诉我您的症状或健康问题，我会为您提供专业的医疗建议和分诊指导。', false)
    }, 300)
}

const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value
}

const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
}

const deleteHistory = (id) => {
    historyList.value = historyList.value.filter(item => item.id !== id)
}

const goToProfile = () => {
    router.push({ name: 'patient-home' })
}

const logout = () => {
    authStore.logout()
    router.push({ name: 'login' })
}

onMounted(() => {
    setTimeout(() => {
        addMessage('您好！我是 AI 智能导诊助手。请告诉我您的症状或健康问题，我会为您提供专业的医疗建议和分诊指导。', false)
    }, 300)
})
</script>

<template>
  <div class="ds-chat" :class="{ 'dark-mode': isDarkMode, 'light-mode': !isDarkMode }">
    <aside class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
      <div class="sidebar-top">
        <div class="sidebar-logo">
          <div class="logo-icon">
            <el-icon><FirstAidKit /></el-icon>
          </div>
          <span v-if="!sidebarCollapsed" class="logo-text">智能导诊</span>
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
        <div class="history-title">历史对话</div>
        <div class="history-list">
          <div 
            v-for="item in historyList" 
            :key="item.id" 
            class="history-item"
          >
            <el-icon class="history-icon"><ChatDotRound /></el-icon>
            <div class="history-info">
              <div class="history-name">{{ item.title }}</div>
              <div class="history-time">{{ item.time }}</div>
            </div>
            <button class="delete-btn" @click.stop="deleteHistory(item.id)">
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </div>
      </div>
      
      <div class="sidebar-bottom">
        <div class="user-area" v-if="!sidebarCollapsed" @click="goToProfile">
          <div class="user-avatar">
            <el-icon><User /></el-icon>
          </div>
          <div class="user-info">
            <div class="user-name">个人中心</div>
          </div>
          <el-icon class="user-arrow"><ArrowRight /></el-icon>
        </div>
        
        <button v-if="sidebarCollapsed" class="user-avatar-mini" @click="goToProfile" title="个人中心">
          <el-icon><User /></el-icon>
        </button>
      </div>
    </aside>

    <div class="main-area">
      <header class="ds-header">
        <div class="header-left">
          <button @click="toggleSidebar" class="nav-btn mobile-toggle">
            <el-icon><Expand /></el-icon>
          </button>
        </div>
        
        <div class="header-center">
          <span class="chat-title">AI 智能导诊</span>
        </div>
        
        <div class="header-right">
          <button @click="toggleTheme" class="theme-btn">
            <el-icon v-if="isDarkMode"><Sunny /></el-icon>
            <el-icon v-else><Moon /></el-icon>
          </button>
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
            <div class="msg-avatar">
              <el-icon v-if="!msg.isUser" class="ai-avatar"><Service /></el-icon>
              <el-icon v-else class="user-avatar"><UserFilled /></el-icon>
            </div>
            
            <div class="msg-body">
              <div class="msg-bubble" :class="{ 'user-bubble': msg.isUser }">
                <p>{{ msg.content }}</p>
              </div>
              <span class="msg-time">{{ msg.time }}</span>
            </div>
          </div>
          
          <div v-if="loading" class="msg-row ai-row">
            <div class="msg-avatar">
              <el-icon class="ai-avatar"><Service /></el-icon>
            </div>
            <div class="msg-body">
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
          
          <button 
            class="image-btn" 
            @click="triggerFileInput"
            :disabled="loading || analyzingImage"
            title="上传伤口图片"
          >
            <el-icon v-if="!analyzingImage"><PictureFilled /></el-icon>
            <el-icon v-else class="loading-icon"><Loading /></el-icon>
          </button>
          
          <textarea 
            ref="textareaRef"
            v-model="inputText"
            @keydown="handleKeyDown"
            :placeholder="waitingForAnswers ? '请回答上述问题...' : '输入您的症状或问题...'"
            rows="2"
            :disabled="loading"
          ></textarea>
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
  </div>
</template>

<style scoped>
.ds-chat {
    width: 100%;
    height: 100vh;
    display: flex;
    transition: background 0.3s ease;
}

.dark-mode { background: #1a1a1a; }
.light-mode { background: #fff; }

.sidebar {
    width: 260px;
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: all 0.3s ease;
    flex-shrink: 0;
}

.sidebar.collapsed { width: 64px; }

.dark-mode .sidebar { background: #202123; border-right: 1px solid #2d2d30; }
.light-mode .sidebar { background: #fff; border-right: 1px solid #e5e5e5; }

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
}

.sidebar.collapsed .sidebar-logo {
    justify-content: center;
}

.logo-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    background: linear-gradient(135deg, #4f8cff, #6c5ce7);
    color: #fff;
    flex-shrink: 0;
}

.logo-text {
    flex: 1;
    font-size: 16px;
    font-weight: 600;
}

.dark-mode .logo-text { color: #ececec; }
.light-mode .logo-text { color: #1a1a1a; }

.expand-btn {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    transition: all 0.2s;
}

.dark-mode .expand-btn {
    background: rgba(255,255,255,0.08);
    color: #ccc;
}
.dark-mode .expand-btn:hover {
    background: rgba(255,255,255,0.12);
}

.light-mode .expand-btn {
    background: #f5f5f5;
    color: #333;
}
.light-mode .expand-btn:hover {
    background: #e0e0e0;
}

.new-chat-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 16px;
    border-radius: 12px;
    border: none;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.sidebar.collapsed .new-chat-btn {
    padding: 12px;
}

.dark-mode .new-chat-btn {
    background: rgba(255,255,255,0.08);
    color: #ececec;
}
.dark-mode .new-chat-btn:hover {
    background: rgba(255,255,255,0.15);
}

.light-mode .new-chat-btn {
    background: #f0f0f0;
    color: #333;
}
.light-mode .new-chat-btn:hover {
    background: #e0e0e0;
}

.sidebar-history {
    flex: 1;
    overflow-y: auto;
    padding: 0 12px;
}

.dark-mode .sidebar-history { background: #202123; }
.light-mode .sidebar-history { background: #fff; }

.history-title {
    font-size: 12px;
    font-weight: 500;
    padding: 8px 4px;
    margin-bottom: 4px;
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
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
}

.dark-mode .history-item:hover { background: rgba(255,255,255,0.05); }
.light-mode .history-item:hover { background: #f5f5f5; }

.history-icon {
    font-size: 18px;
}

.dark-mode .history-icon { color: #666; }
.light-mode .history-icon { color: #aaa; }

.history-info { flex: 1; min-width: 0; }

.history-name {
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dark-mode .history-name { color: #ccc; }
.light-mode .history-name { color: #333; }

.history-time {
    font-size: 11px;
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
    gap: 8px;
}

.dark-mode .sidebar-bottom { background: #202123; }
.light-mode .sidebar-bottom { background: #fff; }

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

.dark-mode .ds-header { background: #1a1a1a; border-color: #2d2d30; }
.light-mode .ds-header { background: #f7f7f8; border-color: #e5e5e5; }

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

.typing-bubble {
    display: flex;
    gap: 4px;
    padding: 14px 18px;
    border-radius: 16px;
    width: fit-content;
}

.dark-mode .typing-bubble { background: #2f2f2f; }
.light-mode .typing-bubble { background: #f0f0f0; }

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
    border-radius: 16px;
    transition: all 0.2s;
}

.dark-mode .input-box {
    background: #2f2f2f;
}
.dark-mode .input-box:focus-within {
    background: #3a3a3a;
}

.light-mode .input-box {
    background: #f0f0f0;
}
.light-mode .input-box:focus-within {
    background: #e8e8e8;
}

.input-box textarea {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    font-size: 15px;
    line-height: 1.5;
    min-height: 48px;
    max-height: 150px;
    font-family: inherit;
}

.dark-mode .input-box textarea { color: #ececec; }
.light-mode .input-box textarea { color: #1a1a1a; }

.input-box textarea::placeholder {
    color: #888;
}

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
    
    .mobile-toggle {
        display: flex;
    }
    
    .msg-body {
        max-width: 85%;
    }
}
</style>
