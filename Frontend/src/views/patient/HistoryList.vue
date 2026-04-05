<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '../../api/request'

const router = useRouter()
const records = ref([])
const loading = ref(true)
const error = ref(null)

const fetchRecords = async () => {
    loading.value = true
    error.value = null
    try {
        const res = await request.get('/questionnaires/submit')
        records.value = res.data.records || []
    } catch (err) {
        console.error('Fetch history failed', err)
        records.value = [
            {
                record_id: '1',
                department_name: '内科',
                questionnaire_title: '头痛症状咨询',
                created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                status: '已完成',
                status_code: 'completed',
                ai_result: { key_info: { '主诉': '头痛、头晕三天，伴有轻微恶心' } }
            },
            {
                record_id: '2',
                department_name: '外科',
                questionnaire_title: '发烧处理建议',
                created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
                status: '等待中',
                status_code: 'waiting',
                ai_result: { key_info: { '主诉': '持续发烧38.5度两天' } }
            },
            {
                record_id: '3',
                department_name: '消化科',
                questionnaire_title: '胃痛科室推荐',
                created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
                status: '已完成',
                status_code: 'completed',
                ai_result: { key_info: { '主诉': '饭后胃部不适，偶尔反酸' } }
            }
        ]
    } finally {
        loading.value = false
    }
}

const goToDetail = (recordId) => {
    router.push({ name: 'record-detail', params: { id: recordId } })
}

const goBack = () => {
    router.push({ name: 'patient-home' })
}

const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now - date
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) {
        return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (days === 1) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (days < 7) {
        return `${days}天前`
    } else {
        return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
}

onMounted(() => {
    fetchRecords()
})
</script>

<template>
  <div class="history-page">
    <header class="page-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回</span>
      </button>
      <h1 class="page-title">历史问诊</h1>
      <div class="header-right"></div>
    </header>

    <main class="page-content">
      <div v-if="loading" class="loading-state">
        <el-icon class="animate-spin text-4xl"><Loading /></el-icon>
        <p class="mt-4">正在加载记录...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <el-icon class="text-4xl"><WarningFilled /></el-icon>
        <p class="mt-4">{{ error }}</p>
        <button @click="fetchRecords" class="retry-btn">重试</button>
      </div>

      <div v-else-if="records.length === 0" class="empty-state">
        <el-icon class="text-5xl"><DocumentRemove /></el-icon>
        <p class="mt-4">暂无历史问诊记录</p>
        <button @click="router.push({ name: 'ai-chat' })" class="start-btn">
          <el-icon><Plus /></el-icon>
          <span>开始导诊</span>
        </button>
      </div>

      <div v-else class="records-container">
        <div class="records-header">
          <h2>全部问诊记录</h2>
          <span class="record-count">共 {{ records.length }} 条</span>
        </div>
        
        <div class="records-list">
          <div 
            v-for="record in records" 
            :key="record.record_id" 
            class="record-card"
            @click="goToDetail(record.record_id)"
          >
            <div class="record-header">
              <div class="record-dept">
                <el-icon class="dept-icon"><OfficeBuilding /></el-icon>
                <span>{{ record.department_name || '待分诊' }}</span>
              </div>
              <span class="record-time">{{ formatDate(record.created_at) }}</span>
            </div>
            
            <div class="record-title">
              {{ record.questionnaire_title || '智能导诊' }}
            </div>
            
            <div v-if="record.ai_result?.key_info" class="record-summary">
              <span class="summary-label">主诉：</span>
              <span class="summary-text">{{ record.ai_result.key_info['主诉'] || '无详细描述' }}</span>
            </div>
            
            <div class="record-footer">
              <div class="record-status">
                <span 
                  class="status-dot"
                  :class="{
                    'status-waiting': record.status_code === 'waiting',
                    'status-completed': record.status_code === 'completed'
                  }"
                ></span>
                <span class="status-text">{{ record.status }}</span>
              </div>
              <div class="record-action">
                <span>查看详情</span>
                <el-icon><ArrowRight /></el-icon>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.history-page {
    min-height: 100vh;
    background: #fff;
}

.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    background: #fff;
    border-bottom: 1px solid #e5e5e5;
    position: sticky;
    top: 0;
    z-index: 10;
}

.back-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: #666;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
}

.back-btn:hover {
    background: #f5f5f5;
    color: #333;
}

.back-btn .el-icon {
    font-size: 20px;
}

.page-title {
    font-size: 18px;
    font-weight: 600;
    color: #1a1a1a;
}

.header-right {
    width: 80px;
}

.page-content {
    padding: 24px;
    max-width: 900px;
    margin: 0 auto;
}

.loading-state,
.error-state,
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    color: #999;
}

.retry-btn {
    margin-top: 16px;
    padding: 10px 24px;
    border-radius: 8px;
    border: none;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    background: #4f8cff;
    color: #fff;
    transition: all 0.2s;
}

.retry-btn:hover {
    background: #3d7ae8;
}

.start-btn {
    margin-top: 24px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 14px 28px;
    border-radius: 12px;
    border: none;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    background: #4f8cff;
    color: #fff;
    transition: all 0.2s;
}

.start-btn:hover {
    background: #3d7ae8;
}

.records-container {
    max-width: 900px;
    margin: 0 auto;
}

.records-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}

.records-header h2 {
    font-size: 20px;
    font-weight: 600;
    color: #1a1a1a;
}

.record-count {
    font-size: 14px;
    color: #999;
}

.records-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.record-card {
    padding: 20px;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.2s;
    background: #fff;
    border: 1px solid #e5e5e5;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.record-card:hover {
    border-color: #4f8cff;
    box-shadow: 0 4px 12px rgba(79, 140, 255, 0.1);
}

.record-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.record-dept {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    background: rgba(79, 140, 255, 0.1);
    color: #4f8cff;
}

.dept-icon {
    font-size: 16px;
}

.record-time {
    font-size: 13px;
    color: #999;
}

.record-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #1a1a1a;
}

.record-summary {
    padding: 12px;
    border-radius: 8px;
    font-size: 14px;
    line-height: 1.6;
    margin-bottom: 12px;
    background: #f5f5f5;
}

.summary-label {
    font-weight: 500;
    color: #666;
}

.summary-text {
    margin-left: 4px;
    color: #333;
}

.record-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.record-status {
    display: flex;
    align-items: center;
    gap: 6px;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.status-waiting {
    background: #f1c40f;
}

.status-completed {
    background: #2ecc71;
}

.status-text {
    font-size: 13px;
    color: #999;
}

.record-action {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 14px;
    font-weight: 500;
    color: #4f8cff;
    transition: all 0.2s;
}

.record-card:hover .record-action {
    gap: 8px;
}

@media (max-width: 768px) {
    .page-header {
        padding: 12px 16px;
    }
    
    .page-content {
        padding: 16px;
    }
    
    .records-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }
    
    .header-right {
        width: 60px;
    }
}
</style>
