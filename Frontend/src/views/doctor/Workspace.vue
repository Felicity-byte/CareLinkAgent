<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import * as echarts from 'echarts'

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
    if (chart) {
        chart.resize()
    }
}

const statsCards = ref([
    { title: '本周新增患者', value: 28, icon: 'User', color: '#4f8cff', trend: '+12%' },
    { title: '本周新增病历', value: 45, icon: 'Document', color: '#00b894', trend: '+8%' },
    { title: '待查看病历', value: 12, icon: 'View', color: '#ff9f43', trend: '' },
    { title: '高风险预警', value: 5, icon: 'Warning', color: '#ff4757', trend: '' }
])

const chartData = ref({
    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    patients: [5, 8, 6, 10, 7, 3, 4],
    records: [8, 12, 9, 15, 11, 5, 6]
})

const quickActions = ref([
    { label: '新增患者', icon: 'UserFilled', color: '#4f8cff' },
    { label: '病历管理', icon: 'Document', color: '#00b894' },
    { label: '快速预约', icon: 'Calendar', color: '#ff9f43' },
    { label: '通知', icon: 'Bell', color: '#764ba2' }
])

const pendingTasks = ref([
    { id: 1, title: '查看张三的复查报告', time: '10分钟前', type: 'urgent' },
    { id: 2, title: '确认李四的预约申请', time: '30分钟前', type: 'normal' },
    { id: 3, title: '处理王五的病历审核', time: '1小时前', type: 'normal' }
])

let chart = null
const chartRef = ref(null)

const initChart = () => {
    if (!chartRef.value) return
    
    chart = echarts.init(chartRef.value)
    
    const option = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#e0e0e0',
            borderWidth: 1,
            textStyle: {
                color: '#333'
            }
        },
        legend: {
            data: ['新增患者', '新增病历'],
            top: 0,
            right: 0,
            textStyle: {
                color: '#888',
                fontSize: 12
            }
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '15%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: chartData.value.labels,
            axisLine: {
                lineStyle: {
                    color: '#e0e0e0'
                }
            },
            axisLabel: {
                color: '#888'
            }
        },
        yAxis: {
            type: 'value',
            min: 0,
            max: 20,
            interval: 5,
            axisLine: {
                show: false
            },
            axisLabel: {
                color: '#888'
            },
            splitLine: {
                lineStyle: {
                    color: '#f0f0f0'
                }
            }
        },
        series: [
            {
                name: '新增患者',
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 8,
                lineStyle: {
                    color: '#4f8cff',
                    width: 2
                },
                itemStyle: {
                    color: '#4f8cff',
                    borderColor: '#fff',
                    borderWidth: 2
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(79, 140, 255, 0.3)' },
                        { offset: 1, color: 'rgba(79, 140, 255, 0)' }
                    ])
                },
                data: chartData.value.patients
            },
            {
                name: '新增病历',
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 8,
                lineStyle: {
                    color: '#00b894',
                    width: 2
                },
                itemStyle: {
                    color: '#00b894',
                    borderColor: '#fff',
                    borderWidth: 2
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(0, 184, 148, 0.3)' },
                        { offset: 1, color: 'rgba(0, 184, 148, 0)' }
                    ])
                },
                data: chartData.value.records
            }
        ]
    }
    
    chart.setOption(option)
}

onMounted(() => {
    window.addEventListener('resize', handleResize)
    handleResize()
    nextTick(() => {
        initChart()
    })
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    if (chart) {
        chart.dispose()
    }
})
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
        <!-- 第一行：四个功能区块 -->
        <div class="row row-1">
          <div 
            v-for="stat in statsCards" 
            :key="stat.title"
            class="card stat-card"
          >
            <div class="stat-icon" :style="{ background: stat.color + '20', color: stat.color }">
              <el-icon><component :is="stat.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.title }}</div>
              <div v-if="stat.trend" class="stat-trend" :style="{ color: stat.color }">{{ stat.trend }}</div>
            </div>
          </div>
        </div>

        <!-- 第二行：折线图 + 快捷功能 -->
        <div class="row row-2">
          <!-- 左侧：折线图 -->
          <div class="card content-card chart-card">
            <div class="card-header">
              <h3>数据趋势</h3>
            </div>
            <div ref="chartRef" class="chart-container"></div>
          </div>

          <!-- 右侧：快捷功能 -->
          <div class="card content-card quick-card">
            <div class="card-header">
              <h3>快捷功能</h3>
            </div>
            <div class="quick-grid-vertical">
              <div 
                v-for="action in quickActions" 
                :key="action.label"
                class="quick-item-vertical"
                :style="{ '--accent-color': action.color }"
              >
                <div class="quick-icon-wrapper">
                  <div class="quick-icon" :style="{ background: action.color + '15', color: action.color }">
                    <el-icon><component :is="action.icon" /></el-icon>
                  </div>
                </div>
                <span class="quick-label">{{ action.label }}</span>
                <div class="quick-arrow">
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>
            </div>
            <div class="pending-section">
              <div class="section-header">
                <span class="section-title">待办事项</span>
                <span class="section-badge">{{ pendingTasks.length }}</span>
              </div>
              <div class="pending-list">
                <div 
                  v-for="task in pendingTasks" 
                  :key="task.id"
                  class="pending-item"
                  :class="{ urgent: task.type === 'urgent' }"
                >
                  <div class="pending-dot"></div>
                  <div class="pending-content">
                    <span class="pending-title">{{ task.title }}</span>
                    <span class="pending-time">{{ task.time }}</span>
                  </div>
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
  flex: none;
  height: auto;
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

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px 24px;
  min-width: 0;
  cursor: pointer;
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card .stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.stat-card .stat-info {
  flex: 1;
  min-width: 0;
}

.stat-card .stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  line-height: 1.2;
}

.stat-card .stat-label {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
}

.stat-trend {
  font-size: 12px;
  font-weight: 600;
  margin-top: 2px;
}

.chart-card {
  flex: 1;
  min-width: 0;
}

.quick-card {
  flex: 1;
  min-width: 0;
  max-width: none;
}

.chart-container {
  flex: 1;
  min-height: 200px;
}

.quick-grid-vertical {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.quick-item-vertical {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: #fff;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.quick-item-vertical::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, var(--accent-color)08, var(--accent-color)03);
  opacity: 0;
  transition: opacity 0.3s;
}

.quick-item-vertical:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: var(--accent-color)30;
}

.quick-item-vertical:hover::before {
  opacity: 1;
}

.quick-item-vertical:active {
  transform: translateY(-1px);
}

.quick-icon-wrapper {
  position: relative;
  z-index: 1;
}

.quick-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.3s;
}

.quick-item-vertical:hover .quick-icon {
  transform: scale(1.1);
  box-shadow: 0 4px 12px var(--accent-color)30;
}

.quick-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  position: relative;
  z-index: 1;
  flex: 1;
}

.quick-arrow {
  position: relative;
  z-index: 1;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  font-size: 10px;
  transition: all 0.3s;
  opacity: 0;
  transform: translateX(-8px);
}

.quick-item-vertical:hover .quick-arrow {
  opacity: 1;
  transform: translateX(0);
  background: var(--accent-color)15;
  color: var(--accent-color);
}

.pending-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.section-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #ff475715;
  color: #ff4757;
  font-weight: 600;
}

.pending-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pending-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: #fafbfc;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.pending-item:hover {
  background: #f0f4f8;
}

.pending-item.urgent {
  background: #fff5f5;
}

.pending-item.urgent:hover {
  background: #ffebeb;
}

.pending-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00b894;
  margin-top: 5px;
  flex-shrink: 0;
}

.pending-item.urgent .pending-dot {
  background: #ff4757;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.pending-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pending-title {
  font-size: 13px;
  color: #333;
  line-height: 1.4;
}

.pending-time {
  font-size: 11px;
  color: #999;
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

  .row-1 {
    flex: none;
    overflow: visible;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .row-2 {
    flex: none;
    overflow: visible;
  }

  .content-card {
    flex: none;
    min-height: 200px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-card .stat-value {
    font-size: 24px;
  }

  .quick-card {
    max-width: none;
    min-width: 0;
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
</style>
