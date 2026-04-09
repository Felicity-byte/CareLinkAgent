<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const sidebarCollapsed = ref(true)
const showMobileMenu = ref(false)
const isMobile = ref(window.innerWidth < 768)

const welcomeText = ref('欢迎回来，' + (authStore.doctor?.username || '医生'))

const notificationCount = ref(3)

const menuItems = ref([
    { label: '工作台', icon: 'HomeFilled', active: true, route: '/doctor/workspace' },
    { label: '患者管理', icon: 'User', active: false, route: '/doctor/patients' },
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

const statsCards = ref([
    { title: '今日问诊', value: 28, icon: 'ChatDotRound', color: '#4f8cff' },
    { title: '待处理', value: 12, icon: 'Bell', color: '#ff9f43' },
    { title: '已完成', value: 156, icon: 'CircleCheck', color: '#00b894' }
])

const recentPatients = ref([
    { id: 1, name: '张三', time: '10:30', status: '待回复' },
    { id: 2, name: '李四', time: '09:15', status: '进行中' },
    { id: 3, name: '王五', time: '昨天', status: '已完成' }
])

const quickActions = ref([
    { label: '新建问诊', icon: 'Plus' },
    { label: '查看报告', icon: 'Document' },
    { label: '患者管理', icon: 'User' },
    { label: '数据统计', icon: 'DataAnalysis' }
])
</script>

<template>
  <div class="workspace">
    <!-- 左侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed, 'mobile-open': !sidebarCollapsed && isMobile }">
      <!-- 顶部Logo卡片 -->
      <div class="card logo-card">
        <div class="logo-icon">
          <el-icon><FirstAidKit /></el-icon>
        </div>
        <span v-if="!sidebarCollapsed" class="logo-text">医生工作站</span>
        <button v-if="isMobile && !sidebarCollapsed" class="close-sidebar-btn" @click="toggleSidebar">
          <el-icon><Close /></el-icon>
        </button>
      </div>

      <!-- 导航菜单卡片 -->
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

      <!-- 底部用户卡片 -->
      <div class="card user-card" @click="handleMenuClick(4)">
        <div class="user-avatar">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div v-if="!sidebarCollapsed" class="user-info">
          <div class="user-name">{{ authStore.doctor?.username || '医生姓名' }}</div>
          <div class="user-role">主治医师</div>
        </div>
      </div>
    </aside>

    <!-- 遮罩层 -->
    <div v-if="isMobile && !sidebarCollapsed" class="sidebar-overlay" @click="toggleSidebar"></div>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部欢迎语卡片 -->
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

      <!-- 内容网格 -->
      <div class="content-grid">
        <!-- 第一行：两个卡片 -->
        <div class="row row-1">
          <!-- 左侧卡片：统计+列表 -->
          <div class="card content-card card-left-top">
            <div class="card-header">
              <h3>今日概览</h3>
              <span class="badge">实时</span>
            </div>
            <div class="stats-row">
              <div 
                v-for="stat in statsCards" 
                :key="stat.title"
                class="stat-item"
              >
                <div class="stat-icon" :style="{ background: stat.color + '20', color: stat.color }">
                  <el-icon><component :is="stat.icon" /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ stat.value }}</div>
                  <div class="stat-label">{{ stat.title }}</div>
                </div>
              </div>
            </div>
            <div class="recent-list">
              <div class="list-title">最近患者</div>
              <div 
                v-for="patient in recentPatients" 
                :key="patient.id"
                class="list-item"
              >
                <div class="item-avatar">
                  <el-icon><User /></el-icon>
                </div>
                <div class="item-info">
                  <span class="item-name">{{ patient.name }}</span>
                  <span class="item-time">{{ patient.time }}</span>
                </div>
                <span 
                  class="item-status"
                  :class="{ 
                    'status-pending': patient.status === '待回复',
                    'status-active': patient.status === '进行中',
                    'status-done': patient.status === '已完成'
                  }"
                >{{ patient.status }}</span>
              </div>
            </div>
          </div>

          <!-- 右侧卡片：快捷操作+通知 -->
          <div class="card content-card card-right-top">
            <div class="card-header">
              <h3>快捷操作</h3>
            </div>
            <div class="quick-grid">
              <div 
                v-for="action in quickActions" 
                :key="action.label"
                class="quick-item"
              >
                <el-icon><component :is="action.icon" /></el-icon>
                <span>{{ action.label }}</span>
              </div>
            </div>
            <div class="notice-section">
              <div class="card-header">
                <h3>系统通知</h3>
                <a href="#" class="more-link">查看全部</a>
              </div>
              <div class="notice-list">
                <div class="notice-item">
                  <div class="notice-dot"></div>
                  <div class="notice-content">
                    <p>您有 3 条新的患者消息待处理</p>
                    <span class="notice-time">5分钟前</span>
                  </div>
                </div>
                <div class="notice-item">
                  <div class="notice-dot read"></div>
                  <div class="notice-content">
                    <p>系统已自动生成本周统计报告</p>
                    <span class="notice-time">1小时前</span>
                  </div>
                </div>
                <div class="notice-item">
                  <div class="notice-dot read"></div>
                  <div class="notice-content">
                    <p>患者张三已完成术后第7天随访</p>
                    <span class="notice-time">2小时前</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 第二行：两个卡片 -->
        <div class="row row-2">
          <!-- 左下卡片：日程安排 -->
          <div class="card content-card card-bottom-left">
            <div class="card-header">
              <h3>今日日程</h3>
              <span class="date-badge">2026-04-07 周二</span>
            </div>
            <div class="schedule-list">
              <div class="schedule-item">
                <div class="schedule-time">
                  <span class="time">09:00</span>
                  <span class="time-end">10:00</span>
                </div>
                <div class="schedule-content">
                  <div class="schedule-title">门诊接诊</div>
                  <div class="schedule-desc">内科门诊 3号诊室</div>
                </div>
                <span class="schedule-status done">已完成</span>
              </div>
              <div class="schedule-item">
                <div class="schedule-time">
                  <span class="time">14:00</span>
                  <span class="time-end">15:30</span>
                </div>
                <div class="schedule-content">
                  <div class="schedule-title">AI随访复查</div>
                  <div class="schedule-desc">5位患者术后随访</div>
                </div>
                <span class="schedule-status current">进行中</span>
              </div>
              <div class="schedule-item">
                <div class="schedule-time">
                  <span class="time">16:00</span>
                  <span class="time-end">17:00</span>
                </div>
                <div class="schedule-content">
                  <div class="schedule-title">病例讨论会</div>
                  <div class="schedule-desc">三楼会议室</div>
                </div>
                <span class="schedule-status pending">待开始</span>
              </div>
            </div>
          </div>

          <!-- 右下卡片：数据图表区 -->
          <div class="card content-card card-bottom-right">
            <div class="card-header">
              <h3>数据分析</h3>
            </div>
            <div class="chart-placeholder">
              <div class="chart-bars">
                <div class="bar" style="--h: 60%; --c: #4f8cff;">
                  <span class="bar-label">周一</span>
                  <div class="bar-fill"></div>
                </div>
                <div class="bar" style="--h: 80%; --c: #4f8cff;">
                  <span class="bar-label">周二</span>
                  <div class="bar-fill"></div>
                </div>
                <div class="bar" style="--h: 45%; --c: #4f8cff;">
                  <span class="bar-label">周三</span>
                  <div class="bar-fill"></div>
                </div>
                <div class="bar" style="--h: 90%; --c: #4f8cff;">
                  <span class="bar-label">周四</span>
                  <div class="bar-fill"></div>
                </div>
                <div class="bar" style="--h: 70%; --c: #4f8cff;">
                  <span class="bar-label">周五</span>
                  <div class="bar-fill"></div>
                </div>
                <div class="bar" style="--h: 30%; --c: #e0e0e0;">
                  <span class="bar-label">周六</span>
                  <div class="bar-fill"></div>
                </div>
                <div class="bar" style="--h: 25%; --c: #e0e0e0;">
                  <span class="bar-label">周日</span>
                  <div class="bar-fill"></div>
                </div>
              </div>
              <div class="chart-summary">
                <div class="summary-item">
                  <span class="summary-label">本周总问诊</span>
                  <span class="summary-value">186次</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">较上周</span>
                  <span class="summary-value up">+12.5%</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">平均响应</span>
                  <span class="summary-value">3.2分钟</span>
                </div>
              </div>
            </div>
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

/* 卡片基础样式 */
.card {
  background: linear-gradient(135deg, #f0f7ff, #cce5ff);
  border-radius: 25px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* 侧边栏 */
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

/* 移动端侧边栏 */
.sidebar-overlay {
  display: none;
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

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px 20px;
  overflow: hidden;
}

.main-content::-webkit-scrollbar {
  width: 6px;
}

.main-content::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}

/* 顶部欢迎语 */
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

/* 内容网格 */
.content-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.row {
  display: flex;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

.row-1 {
  flex: 1;
}

.row-2 {
  flex: 1;
}

.content-card {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.card-left-top,
.card-bottom-left {
  flex: 1;
  min-width: 0;
}

.card-right-top {
  flex: 1;
  min-width: 0;
}

.card-bottom-right {
  flex: 1;
  min-width: 0;
}

/* 小屏幕响应式布局 */
@media (max-width: 768px) {
  .main-content {
    overflow-y: auto;
    min-height: 0;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .main-content::-webkit-scrollbar {
    display: none;
  }

  .content-grid {
    overflow-y: auto;
    min-height: 0;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }

  .content-grid::-webkit-scrollbar {
    display: none;
  }

  .row {
    flex-direction: column;
    overflow: visible;
  }

  .row-1,
  .row-2 {
    flex: none;
    overflow: visible;
  }

  .content-card {
    flex: none;
    min-height: 200px;
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

  .stats-row {
    flex-wrap: wrap;
  }

  .stat-item {
    flex: 1 1 calc(50% - 6px);
    min-width: 100px;
  }

  .quick-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.card-header h3 {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.badge {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  background: #52c41a15;
  color: #52c41a;
  font-weight: 500;
}

.date-badge {
  font-size: 12px;
  color: #888;
}

.more-link {
  font-size: 12px;
  color: #4f8cff;
  text-decoration: none;
}

/* 统计卡片 */
.stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #fafbfc;
  border-radius: 10px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #333;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #888;
  margin-top: 2px;
}

/* 列表样式 */
.list-title {
  font-size: 13px;
  font-weight: 600;
  color: #555;
  margin-bottom: 10px;
}

.recent-list {
  flex: 1;
  overflow-y: auto;
}

.recent-list::-webkit-scrollbar {
  width: 4px;
}

.recent-list::-webkit-scrollbar-thumb {
  background: #e0e0e0;
  border-radius: 2px;
}

.list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.2s;
  cursor: pointer;
}

.list-item:hover {
  background: #f8f9fa;
}

.item-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  background: #e8f4fd;
  color: #4f8cff;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.item-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
}

.item-time {
  font-size: 11px;
  color: #aaa;
}

.item-status {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}

.status-pending {
  background: #ff9f4320;
  color: #ff9f43;
}

.status-active {
  background: #4f8cff20;
  color: #4f8cff;
}

.status-done {
  background: #00b89420;
  color: #00b894;
}

/* 快捷操作 */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 16px 10px;
  background: #fafbfc;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  color: #555;
}

.quick-item .el-icon {
  font-size: 24px;
  color: #4f8cff;
}

.quick-item:hover {
  background: #4f8cff10;
  transform: translateY(-2px);
}

/* 通知区域 */
.notice-section {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.notice-section .card-header {
  margin-bottom: 10px;
}

.notice-list {
  flex: 1;
  overflow-y: auto;
}

.notice-list::-webkit-scrollbar {
  width: 4px;
}

.notice-list::-webkit-scrollbar-thumb {
  background: #e0e0e0;
  border-radius: 2px;
}

.notice-item {
  display: flex;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.notice-item:last-child {
  border-bottom: none;
}

.notice-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4757;
  margin-top: 5px;
  flex-shrink: 0;
}

.notice-dot.read {
  background: #ddd;
}

.notice-content {
  flex: 1;
  min-width: 0;
}

.notice-content p {
  font-size: 13px;
  color: #444;
  margin: 0 0 4px 0;
  line-height: 1.4;
}

.notice-time {
  font-size: 11px;
  color: #bbb;
}

/* 日程安排 */
.schedule-list {
  flex: 1;
  overflow-y: auto;
}

.schedule-list::-webkit-scrollbar {
  width: 4px;
}

.schedule-list::-webkit-scrollbar-thumb {
  background: #e0e0e0;
  border-radius: 2px;
}

.schedule-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 0;
  border-bottom: 1px solid #f5f5f5;
}

.schedule-item:last-child {
  border-bottom: none;
}

.schedule-time {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}

.time {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.time-end {
  font-size: 11px;
  color: #bbb;
}

.schedule-content {
  flex: 1;
  min-width: 0;
}

.schedule-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.schedule-desc {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.schedule-status {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 4px;
  font-weight: 500;
  white-space: nowrap;
}

.schedule-status.done {
  background: #f0fdf4;
  color: #22c55e;
}

.schedule-status.current {
  background: #eff6ff;
  color: #3b82f6;
}

.schedule-status.pending {
  background: #fefce8;
  color: #eab308;
}

/* 图表区域 */
.chart-tabs {
  display: flex;
  gap: 4px;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 3px;
}

.tab {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  color: #888;
  transition: all 0.2s;
}

.tab.active {
  background: #fff;
  color: #4f8cff;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.chart-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-top: 20px;
}

.chart-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 160px;
  padding: 0 10px;
  gap: 8px;
}

.bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  height: 100%;
  justify-content: flex-end;
}

.bar-label {
  font-size: 11px;
  color: #888;
}

.bar-fill {
  width: 100%;
  max-width: 40px;
  height: var(--h);
  background: var(--c);
  border-radius: 6px 6px 0 0;
  transition: height 0.3s ease;
}

.chart-summary {
  display: flex;
  gap: 24px;
  padding: 14px 16px;
  background: #fafbfc;
  border-radius: 10px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-label {
  font-size: 12px;
  color: #888;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}

.summary-value.up {
  color: #22c55e;
}
</style>
