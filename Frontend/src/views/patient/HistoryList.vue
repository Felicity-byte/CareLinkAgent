<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

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
    },
    {
        id: 4,
        type: 'system',
        title: '系统维护通知',
        content: '系统将于本周六凌晨2:00-4:00进行维护升级，届时部分功能可能无法使用。',
        time: new Date(Date.now() - 1000 * 60 * 60 * 72),
        read: true
    }
])

const activeTab = ref('all')

const unreadCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
})

const filteredNotifications = computed(() => {
    if (activeTab.value === 'unread') {
        return notifications.value.filter(n => !n.read)
    }
    return notifications.value
})

const goBack = () => {
    router.push({ name: 'ai-chat' })
}

const markAsRead = (id) => {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
        notification.read = true
    }
}

const markAllAsRead = () => {
    notifications.value.forEach(n => n.read = true)
}

const formatTime = (date) => {
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

const getTypeInfo = (type) => {
    const types = {
        appointment: { 
            icon: 'Calendar', 
            color: '#1677ff', 
            bg: 'linear-gradient(135deg, #1677ff 0%, #4096ff 100%)',
            label: '预约' 
        },
        system: { 
            icon: 'Bell', 
            color: '#722ed1', 
            bg: 'linear-gradient(135deg, #722ed1 0%, #9254de 100%)',
            label: '系统' 
        }
    }
    return types[type] || { icon: 'Document', color: '#666', bg: '#666', label: '通知' }
}
</script>

<template>
  <div class="notification-page">
    <header class="page-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <div class="header-center">
        <h1 class="page-title">消息通知</h1>
        <span v-if="unreadCount > 0" class="unread-count">{{ unreadCount }}条未读</span>
      </div>
      <button v-if="unreadCount > 0" class="mark-all-btn" @click="markAllAsRead">
        全部已读
      </button>
    </header>

    <div class="tabs-wrapper">
      <div class="tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'all' }"
          @click="activeTab = 'all'"
        >
          全部消息
          <span class="tab-count">{{ notifications.length }}</span>
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'unread' }"
          @click="activeTab = 'unread'"
        >
          未读消息
          <span v-if="unreadCount > 0" class="tab-count highlight">{{ unreadCount }}</span>
        </button>
      </div>
    </div>

    <main class="page-content">
      <div v-if="filteredNotifications.length === 0" class="empty-state">
        <div class="empty-illustration">
          <div class="empty-circle">
            <el-icon class="empty-icon"><Bell /></el-icon>
          </div>
          <div class="empty-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
        <h3 class="empty-title">暂无消息</h3>
        <p class="empty-desc">新的消息会在这里显示</p>
      </div>

      <div v-else class="notification-list">
        <div 
          v-for="notification in filteredNotifications" 
          :key="notification.id" 
          class="notification-item"
          :class="{ unread: !notification.read }"
          @click="markAsRead(notification.id)"
        >
          <div class="item-indicator" v-if="!notification.read"></div>
          
          <div class="item-icon" :style="{ background: getTypeInfo(notification.type).bg }">
            <el-icon v-if="notification.type === 'appointment'"><Calendar /></el-icon>
            <el-icon v-else-if="notification.type === 'system'"><Bell /></el-icon>
            <el-icon v-else><Document /></el-icon>
          </div>
          
          <div class="item-content">
            <div class="item-header">
              <span class="item-type" :style="{ color: getTypeInfo(notification.type).color }">
                {{ getTypeInfo(notification.type).label }}
              </span>
              <span class="item-time">{{ formatTime(notification.time) }}</span>
            </div>
            <h3 class="item-title">{{ notification.title }}</h3>
            <p class="item-text">{{ notification.content }}</p>
            <p v-if="notification.detail" class="item-detail">{{ notification.detail }}</p>
          </div>
          
          <div class="item-action">
            <el-icon><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.notification-page {
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

.unread-count {
    font-size: 11px;
    color: #1677ff;
    font-weight: 500;
}

.mark-all-btn {
    padding: 6px 14px;
    border: none;
    border-radius: 16px;
    background: #1677ff;
    color: #fff;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.mark-all-btn:hover {
    background: #0958d9;
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

.tab-count.highlight {
    background: #ff4d4f;
    color: #fff;
}

.page-content {
    padding: 12px;
    max-width: 600px;
    margin: 0 auto;
}

.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 80px 20px;
}

.empty-illustration {
    position: relative;
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

.empty-dots {
    position: absolute;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 6px;
}

.empty-dots span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #1677ff;
    opacity: 0.3;
}

.empty-dots span:nth-child(2) {
    opacity: 0.5;
}

.empty-dots span:nth-child(3) {
    opacity: 0.7;
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
    padding: 16px;
    background: #fff;
    border-radius: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.notification-item:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
    transform: translateY(-1px);
}

.notification-item.unread {
    background: #fafbff;
}

.notification-item.unread::before {
    content: '';
    position: absolute;
    left: 0;
    top: 16px;
    bottom: 16px;
    width: 3px;
    background: #1677ff;
    border-radius: 0 3px 3px 0;
}

.item-indicator {
    position: absolute;
    top: 18px;
    left: 8px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #1677ff;
}

.item-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
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
    gap: 8px;
    margin-bottom: 6px;
}

.item-type {
    font-size: 12px;
    font-weight: 600;
}

.item-time {
    font-size: 12px;
    color: #999;
}

.item-title {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0 0 4px;
    line-height: 1.4;
}

.item-text {
    font-size: 14px;
    color: #666;
    line-height: 1.5;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.item-detail {
    font-size: 12px;
    color: #999;
    margin: 6px 0 0;
    padding: 6px 10px;
    background: #f5f7fa;
    border-radius: 6px;
}

.item-action {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    color: #ccc;
    font-size: 14px;
    flex-shrink: 0;
    margin-top: 10px;
}

.notification-item:hover .item-action {
    color: #1677ff;
}
</style>
