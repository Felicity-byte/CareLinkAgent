<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../../api/request'

const router = useRouter()

const sessions = ref([])
const loading = ref(false)
const activeTab = ref('all')

const filteredSessions = computed(() => {
    if (activeTab.value === 'recent') {
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000
        return sessions.value.filter(s => new Date(s.updated_at).getTime() > weekAgo)
    }
    return sessions.value
})

const goBack = () => {
    router.push({ name: 'ai-chat' })
}

const openSession = (sessionId) => {
    router.push({ name: 'ai-chat', query: { session_id: sessionId } })
}

const deleteSession = async (sessionId) => {
    if (!confirm('确定要删除这条问诊记录吗？')) return
    
    try {
        await request.delete(`/ai/sessions/${sessionId}`)
        sessions.value = sessions.value.filter(s => s.id !== sessionId)
    } catch (err) {
        console.error('删除失败', err)
        alert('删除失败')
    }
}

const formatTime = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
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

const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const fetchSessions = async () => {
    loading.value = true
    try {
        const res = await request.get('/ai/sessions')
        sessions.value = res.data.sessions || []
    } catch (err) {
        console.error('获取会话列表失败', err)
    } finally {
        loading.value = false
    }
}

onMounted(() => {
    fetchSessions()
})
</script>

<template>
  <div class="history-page">
    <header class="page-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <div class="header-center">
        <h1 class="page-title">问诊记录</h1>
        <span class="session-count">{{ sessions.length }}条记录</span>
      </div>
    </header>

    <div class="tabs-wrapper">
      <div class="tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'all' }"
          @click="activeTab = 'all'"
        >
          全部记录
          <span class="tab-count">{{ sessions.length }}</span>
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'recent' }"
          @click="activeTab = 'recent'"
        >
          最近一周
        </button>
      </div>
    </div>

    <main class="page-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="filteredSessions.length === 0" class="empty-state">
        <div class="empty-illustration">
          <div class="empty-circle">
            <el-icon class="empty-icon"><ChatDotRound /></el-icon>
          </div>
        </div>
        <h3 class="empty-title">暂无问诊记录</h3>
        <p class="empty-desc">开始AI问诊后，记录会在这里显示</p>
      </div>

      <div v-else class="session-list">
        <div 
          v-for="session in filteredSessions" 
          :key="session.id" 
          class="session-item"
          @click="openSession(session.id)"
        >
          <div class="item-icon">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          
          <div class="item-content">
            <div class="item-header">
              <span class="item-title">{{ session.title || 'AI问诊' }}</span>
              <span class="item-time">{{ formatTime(session.updated_at) }}</span>
            </div>
            <div class="item-meta">
              <span v-if="session.surgery_type" class="item-tag">{{ session.surgery_type }}</span>
              <span class="item-count">{{ session.message_count }}条对话</span>
            </div>
            <div class="item-date">{{ formatDate(session.created_at) }}</div>
          </div>
          
          <button class="delete-btn" @click.stop="deleteSession(session.id)">
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.history-page {
    min-height: 100vh;
    background: #f5f7fa;
}

.page-header {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background: #fff;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06);
}

.back-btn {
    width: 36px;
    height: 36px;
    border: none;
    border-radius: 10px;
    background: #f5f5f5;
    color: #333;
    font-size: 18px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.back-btn:hover {
    background: #e8e8e8;
}

.header-center {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}

.page-title {
    font-size: 17px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0;
}

.session-count {
    font-size: 11px;
    color: #999;
}

.tabs-wrapper {
    background: #fff;
    padding: 0 16px 12px;
}

.tabs {
    display: flex;
    background: #f5f5f5;
    border-radius: 10px;
    padding: 3px;
}

.tab-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #666;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.tab-btn.active {
    background: #fff;
    color: #1a1a1a;
    font-weight: 500;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.tab-count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
    border-radius: 9px;
    background: #e0e0e0;
    color: #666;
    font-size: 11px;
    font-weight: 600;
}

.page-content {
    padding: 12px;
    max-width: 600px;
    margin: 0 auto;
}

.loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    color: #999;
    gap: 12px;
}

.loading-icon {
    font-size: 32px;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 20px;
}

.empty-illustration {
    margin-bottom: 24px;
}

.empty-circle {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background: linear-gradient(135deg, #f0f5ff 0%, #e6f4ff 100%);
    display: flex;
    align-items: center;
    justify-content: center;
}

.empty-icon {
    font-size: 48px;
    color: #1677ff;
    opacity: 0.6;
}

.empty-title {
    font-size: 17px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 8px;
}

.empty-desc {
    font-size: 14px;
    color: #999;
    margin: 0;
}

.session-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.session-item {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 16px;
    background: #fff;
    border-radius: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.session-item:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    transform: translateY(-1px);
}

.item-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
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
    justify-content: space-between;
    margin-bottom: 6px;
}

.item-title {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.item-time {
    font-size: 12px;
    color: #999;
    flex-shrink: 0;
}

.item-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}

.item-tag {
    font-size: 12px;
    color: #1677ff;
    background: #e6f4ff;
    padding: 2px 8px;
    border-radius: 4px;
}

.item-count {
    font-size: 12px;
    color: #666;
}

.item-date {
    font-size: 12px;
    color: #999;
}

.delete-btn {
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #999;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    flex-shrink: 0;
}

.delete-btn:hover {
    background: #fff1f0;
    color: #ff4d4f;
}
</style>
