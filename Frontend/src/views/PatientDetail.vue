<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePatientStore } from '../stores/patient'
import Sidebar from '../components/Sidebar.vue'
import TopBar from '../components/TopBar.vue'
import request from '../api/request'

const route = useRoute()
const router = useRouter()
const patientStore = usePatientStore()

const recordId = route.params.id
const loading = ref(true)
const patientData = ref(null)
const diagnosisText = ref('')
const submitting = ref(false)

const aiSummary = computed(() => patientData.value?.ai_result || {})
const userInfo = computed(() => patientData.value?.user || {})

const fetchDetail = async () => {
    loading.value = true
    try {
        const existing = patientStore.patients.find(p => p.record_id === recordId)
        if (existing) {
            patientData.value = existing
        } else {
            const res = await request.get(`/doctor/summary/${recordId}`)
            patientData.value = res.data?.data || res.data
        }
    } catch (err) {
        console.error(err)
        alert('加载详情失败')
    } finally {
        console.log('patientData loaded:', JSON.stringify(patientData.value, null, 2))
        loading.value = false
    }
}

const handleSubmit = async () => {
    if (!diagnosisText.value.trim()) return
    
    submitting.value = true
    try {
        await patientStore.submitDiagnosis(recordId, diagnosisText.value)
        alert('诊断提交成功')
        router.push({ name: 'dashboard' })
    } catch (err) {
        alert('提交失败')
    } finally {
        submitting.value = false
    }
}



const formatMarkdown = (text) => {
    if (!text) return ''
    let html = text
    html = html.replace(/### (\d+)\. 【(.*)】/g, '<h3 class="text-lg font-bold mt-6 mb-3 text-blue-800 border-b border-blue-200 pb-2">$1. $2</h3>')
    html = html.replace(/### (.*)/g, '<h3 class="text-lg font-bold mt-4 mb-2 text-gray-800">$1</h3>')
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="text-gray-900">$1</strong>')
    html = html.replace(/^\* (.*)/gm, '<li class="ml-6 mb-1 list-disc text-gray-700">$1</li>')
    html = html.replace(/(<li[^>]*>.*?<\/li>\s*)+/gs, '<ul class="my-2">$&</ul>')
    html = html.replace(/\n\n/g, '</p><p class="my-3">')
    html = html.replace(/\n/g, '<br>')
    html = '<p class="my-3">' + html + '</p>'
    return html
}

onMounted(() => {
    fetchDetail()
})
</script>

<template>
  <div class="app-container">
    <Sidebar />
    <div class="main-content">
      <TopBar>
          <template #title>
             <div class="flex items-center">
                 <button @click="router.back()" class="mr-4 hover:bg-gray-100 p-1 rounded">
                     <el-icon><ArrowLeft /></el-icon>
                 </button>
                 <span>病历详情</span>
             </div>
          </template>
      </TopBar>
      
      <div v-if="loading" class="flex justify-center items-center h-full">
          <el-icon class="animate-spin text-4xl text-blue-600"><Loading /></el-icon>
      </div>
      
      <div v-else-if="patientData" class="content-wrap">
          <div class="left-column">
              
              <div class="card">
                  <div class="card-header blue-header flex justify-between items-center">
                      <span><el-icon class="inline mr-2"><Monitor /></el-icon> AI 辅助诊断分析 </span>
                  </div>
                  <div class="p-6">
                      <div v-if="aiSummary?.structured_report" class="prose max-w-none" v-html="formatMarkdown(aiSummary.structured_report)">
                      </div>

                      <div v-else class="text-center text-gray-400 py-6">
                          暂无 AI 分析结果
                      </div>
                  </div>
              </div>
              
          </div>
          
          <div class="right-column">
              <div class="card h-full flex flex-col">
                  <div class="card-header">医生诊断</div>
                  <div class="p-6 flex-1 flex flex-col">
                      <textarea 
                        v-model="diagnosisText"
                        class="w-full flex-1 border border-gray-300 rounded-lg p-4 mb-4 focus:ring-2 focus:ring-blue-500 outline-none resize-none"
                        placeholder="请输入诊断意见和医嘱..."
                      ></textarea>
                      
                      <button 
                        @click="handleSubmit"
                        :disabled="submitting || !diagnosisText.trim()"
                        class="w-full py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition disabled:opacity-50"
                      >
                          <el-icon class="inline mr-2"><CircleCheck /></el-icon>
                          提交诊断结果
                      </button>
                  </div>
              </div>
          </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: #F8FAFC;
}
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.content-wrap {
  padding: 24px;
  flex: 1;
  display: flex;
  gap: 24px;
  overflow: hidden;
  height: 100%;
}
.left-column {
  flex: 2;
  overflow-y: auto;
  padding-right: 8px;
}
.right-column {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
.card-header {
    padding: 16px 24px;
    background: #F8FAFC;
    border-bottom: 1px solid #E2E8F0;
    font-weight: 600;
    color: #475569;
    display: flex;
    align-items: center;
}
.blue-header {
    background: linear-gradient(to right, #eff6ff, white);
    color: #1e3a8a;
    border-left: 4px solid #2563eb;
}
.report-section {
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 16px;
}
.report-section:last-child {
    border-bottom: none;
    padding-bottom: 0;
}
.report-label {
    font-weight: 600;
    color: #475569;
    margin-bottom: 8px;
    font-size: 14px;
}
.report-content {
    color: #334155;
    background: #f8fafc;
    padding: 12px 16px;
    border-radius: 6px;
    line-height: 1.6;
}
</style>
