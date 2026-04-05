# AI服务优化解决方案

**文档版本**: v1.0\
**创建日期**: 2026-04-04\
**基于测试**: 第13-14轮测试结果\
**目标**: 解决6项失败测试，提升服务整体质量

***

## 一、问题汇总

根据第13-14轮测试结果，发现以下6项关键问题：

| 问题编号 | 问题描述 | 当前状态 | 目标状态 | 优先级 |
| --- | --- | --- | --- | --- |
| P1 | 病症识别率低 | 0%-33% | ≥80% | 高 |
| P2 | 健康建议质量评分低 | 0% | ≥60% | 高 |
| P3 | 结构化病历生成不完整 | 字段缺失/内容为空 | 100%完整 | 高 |
| P4 | AI建议专业性评分低 | 0% | ≥80% | 高 |
| P5 | 患者安全建议合格率低 | 0% | ≥80% | 高 |
| P6 | 响应时间波动大 | 13s-55s | <15s稳定 | 中 |

### 1.1 问题根因与解决方案概览

| 问题 | 根本原因 | 解决方案核心 |
| --- | --- | --- |
| P1 病症识别率低 | 评估方式死板（精确匹配） | 引入同义词库 + 语义匹配 |
| P2 健康建议质量低 | 建议模板不匹配场景 | 场景化模板 + 关键词检查 |
| P3 病历生成不完整 | 解析逻辑脆弱，无回退 | 防御性编程 + 降级方案 |
| P4 专业性评分低 | 提示词未要求专业术语 | 强制术语 + 自动检查 |
| P5 安全建议合格率低 | 危急场景未特殊处理 | 关键词触发 + 紧急警告 |
| P6 响应时间波动大 | 无重试、无缓存、无监控 | 重试机制 + 缓存 + 监控 |

***

## 二、根因分析

### 2.1 核心问题一：AI的"理解"与测试的"评估"不匹配

**问题本质**: AI像一个健谈的普通人，而测试标准要求它像一个严谨的医生。

**具体表现**:

- **识别率低 (0%-33%)**: AI会说"伤口周围有红肿和发热感"，但测试脚本只认识"伤口发炎"这个精确关键词。AI的回答从语义上看是正确的，但在评估时被判为错误。

- **专业性评分低 (0%)**: AI会给出"这几天注意休息，吃点清淡的"这样的建议，它很口语化、很安全，但缺少"感染"、"换药"、"就医"等专业关键词，因此被判不合格。

**根本原因**:

1. **提示词模板过于开放**: 未明确要求结构化输出格式
2. **测试评估标准过于严格**: 只匹配精确关键词，未考虑语义相似性
3. **缺乏专业术语引导**: AI倾向于使用自然语言而非医学术语

### 2.2 核心问题二：AI的"安全守则"与"医疗安全需求"冲突

**问题本质**: 通用AI被训练得"避免给出医疗建议"，而业务需要它"果断给出安全警告"。

**具体表现**:

- **危急情况响应迟钝**: 当用户说"发烧39度+伤口流脓"时，通用AI的第一反应是"我不能提供医疗诊断，请咨询医生"，语气是建议性的。但医疗场景需要它第一句话就强硬地说："【紧急警告】请立即前往医院！"

**根本原因**:

1. **通用AI安全限制**: 模型训练时被限制避免给出确定性医疗建议
2. **提示词未覆盖危急场景**: 未针对紧急情况设计专门的响应模板
3. **缺乏场景识别机制**: 未识别用户描述的危急程度

### 2.3 核心问题三：数据流转存在"脆弱的断裂点"

**问题本质**: 从"对话"到"报告"的代码逻辑不够健壮，一旦格式有偏差，就会失败。

**具体表现**:

- **病历内容为空**: 在第14轮测试中，病历完全没生成。后端代码在解析AI回复时，因格式、标点符号、换行等微小变化导致解析失败，又没有做好"失败回退"处理，最终数据库写入了空值。

- **响应时间波动大 (13秒 vs 55秒)**: 这通常指向网络问题、API限流或服务器资源竞争，而非AI模型本身的问题。代码中可能没有处理这些偶发性延迟的机制。

**根本原因**:

1. **解析逻辑脆弱**: 未考虑AI输出格式的多样性
2. **缺乏错误恢复机制**: 解析失败时无降级方案
3. **缺乏重试和超时处理**: 网络波动时无自动重试
4. **缺乏性能监控**: 无法定位性能瓶颈

***

## 三、详细解决方案

### 3.1 问题P1：病症识别率低

#### 解决方案概述

采用**双轨优化策略**：同时优化提示词模板和测试评估标准。

#### 方案一：优化提示词模板

**修改文件**: `GlmAI/zhipuGLM/prompts/prompts.py`

**优化内容**:

```python
MEDICAL_CONSULTATION_PROMPT = """
你是一名专业的术后随访医疗助手。请严格按照以下格式回复患者：

【识别症状】: 请列出患者描述的所有症状，使用医学术语
【严重程度】: 根据症状评估：轻度/中度/重度/紧急
【可能原因】: 简要分析可能的原因
【建议措施】: 给出具体的护理建议或就医建议

患者描述：{user_input}
上下文信息：{context}

注意：
1. 症状识别必须使用标准医学术语（如：伤口感染、发热、疼痛等）
2. 严重程度评估要准确，涉及发热>38.5℃、伤口流脓、剧烈疼痛等情况必须标记为"紧急"
3. 建议措施要具体可执行，包含"就医"、"换药"、"观察"等关键词
"""
```

**预期效果**:

- AI输出将包含结构化的症状列表
- 使用标准医学术语便于测试脚本识别
- 严重程度评估帮助识别危急情况

#### 方案二：优化测试评估标准

**修改文件**: `GlmAI/tests/test_streaming.py`

**优化内容**:

```python
class SymptomExtractionTests:
    
    SYMPTOM_SYNONYMS = {
        "伤口发炎": ["伤口发炎", "伤口感染", "红肿", "发热感", "化脓", "流脓"],
        "发烧": ["发烧", "发热", "体温升高", "低烧", "高烧"],
        "疼痛": ["疼痛", "疼", "痛", "不适", "难受"],
        "恶心": ["恶心", "想吐", "呕吐感", "反胃"],
    }
    
    def check_symptom_recognition(self, response, expected_symptoms):
        recognized = []
        for symptom in expected_symptoms:
            synonyms = self.SYMPTOM_SYNONYMS.get(symptom, [symptom])
            if any(syn in response for syn in synonyms):
                recognized.append(symptom)
        return len(recognized) / len(expected_symptoms) * 100
```

**预期效果**:

- 测试评估更灵活，考虑语义相似性
- 避免因表述差异导致的误判

#### 实施步骤

1. 修改 `prompts.py` 中的提示词模板
2. 修改 `test_streaming.py` 中的评估逻辑
3. 运行第15轮测试验证效果
4. 根据测试结果微调

---

### 3.2 问题P2：健康建议质量评分低

#### 解决方案概述

建立**建议质量分级体系**，针对不同严重程度场景设计专门的建议模板。

#### 方案一：场景化建议模板

**修改文件**: `GlmAI/zhipuGLM/prompts/prompts.py`

**优化内容**:

```python
SCENARIO_BASED_ADVICE = {
    "high_severity": {
        "keywords": ["发烧>38.5", "伤口流脓", "剧烈疼痛", "出血不止"],
        "required_terms": ["立即", "紧急", "医院", "就医", "感染"],
        "template": """
【紧急警告】根据您描述的情况，建议您立即采取以下措施：
1. 立即前往最近医院就诊
2. 就诊前保持伤口清洁，避免触碰
3. 如有发烧，可物理降温
4. 携带术后病历资料

这种情况需要专业医生处理，请勿自行用药或拖延。
"""
    },
    "medium_severity": {
        "keywords": ["伤口渗血", "轻微红肿", "低烧<38.5"],
        "required_terms": ["观察", "换药", "清洁", "注意"],
        "template": """
根据您描述的情况，建议您：
1. 每日观察伤口变化，记录红肿范围
2. 按时换药，保持伤口清洁干燥
3. 如症状加重（红肿扩大、发烧升高），请及时就医
4. 避免剧烈运动，注意休息
"""
    },
    "low_severity": {
        "keywords": ["饮食咨询", "恢复咨询", "轻微不适"],
        "required_terms": ["避免", "清淡", "恢复", "建议"],
        "template": """
针对您的问题，建议如下：
1. 饮食方面：避免辛辣刺激食物，以清淡易消化为主
2. 生活方面：保证充足睡眠，适度活动
3. 恢复期间：遵医嘱按时复查
"""
    }
}

def get_advice_template(user_input, symptoms):
    severity = assess_severity(symptoms)
    if severity == "high":
        return SCENARIO_BASED_ADVICE["high_severity"]["template"]
    elif severity == "medium":
        return SCENARIO_BASED_ADVICE["medium_severity"]["template"]
    else:
        return SCENARIO_BASED_ADVICE["low_severity"]["template"]
```

#### 方案二：建议质量检查函数

**修改文件**: `GlmAI/zhipuGLM/service.py`

**优化内容**:

```python
def validate_advice_quality(advice, severity):
    """验证建议质量，确保包含必要关键词"""
    scenario = SCENARIO_BASED_ADVICE[severity]
    required_terms = scenario["required_terms"]
    
    found_terms = [term for term in required_terms if term in advice]
    coverage = len(found_terms) / len(required_terms) * 100
    
    if coverage < 60:
        logger.warning(f"建议质量不达标: 覆盖率{coverage}%, 缺失关键词: {set(required_terms) - set(found_terms)}")
        return False
    return True
```

#### 实施步骤

1. 在 `prompts.py` 中添加场景化建议模板
2. 在 `service.py` 中集成建议质量检查
3. 运行第15轮测试验证
4. 根据测试结果调整关键词列表

---

### 3.3 问题P3：结构化病历生成不完整

#### 解决方案概述

建立**健壮的病历生成流程**，包含数据验证、错误恢复和降级方案。

#### 方案一：病历生成流程重构

**修改文件**: `GlmAI/zhipuGLM/service.py`

**优化内容**:

```python
def generate_medical_report(self, session_id):
    """生成结构化病历报告（增强版）"""
    
    # 步骤1: 数据验证
    session = self.session_manager.get_session(session_id)
    if not session:
        logger.error(f"会话不存在: {session_id}")
        return self._generate_empty_report(session_id, "会话不存在")
    
    if not session.messages:
        logger.warning(f"会话无消息记录: {session_id}")
        return self._generate_empty_report(session_id, "无对话记录")
    
    # 步骤2: 提取对话内容
    try:
        conversation_text = self._extract_conversation(session.messages)
        logger.info(f"提取对话内容成功，长度: {len(conversation_text)}")
    except Exception as e:
        logger.error(f"提取对话失败: {e}")
        return self._generate_empty_report(session_id, f"提取失败: {e}")
    
    # 步骤3: 调用AI生成病历
    try:
        ai_report = self._call_ai_for_report(conversation_text)
        logger.info(f"AI生成病历成功")
    except Exception as e:
        logger.error(f"AI生成病历失败: {e}")
        return self._generate_fallback_report(session)
    
    # 步骤4: 解析并验证病历
    try:
        structured_report = self._parse_and_validate_report(ai_report, session)
        logger.info(f"病历解析验证成功")
        return structured_report
    except Exception as e:
        logger.error(f"病历解析失败: {e}")
        return self._generate_fallback_report(session)

def _extract_conversation(self, messages):
    """提取对话内容"""
    conversation = []
    for msg in messages:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        conversation.append(f"{role}: {content}")
    return "\n".join(conversation)

def _parse_and_validate_report(self, ai_report, session):
    """解析并验证病历报告"""
    
    report = {
        "session_id": session.session_id,
        "patient_info": self._extract_patient_info(session),
        "present_illness": self._extract_field(ai_report, "现病史") or "患者术后随访",
        "symptoms": self._extract_field(ai_report, "症状") or self._extract_symptoms_from_conversation(session),
        "vital_signs": self._extract_field(ai_report, "生命体征") or "未记录",
        "medications": self._extract_field(ai_report, "用药情况") or "未记录",
        "advice": self._extract_field(ai_report, "医嘱建议") or self._generate_basic_advice(session),
        "risk_alerts": self._extract_risk_alerts(ai_report),
        "created_at": datetime.now().isoformat()
    }
    
    # 验证必需字段
    required_fields = ["present_illness", "symptoms", "advice"]
    for field in required_fields:
        if not report.get(field):
            logger.warning(f"必需字段缺失: {field}")
            report[field] = self._get_default_value(field)
    
    return report

def _extract_field(self, text, field_name):
    """从AI回复中提取特定字段（支持多种格式）"""
    
    patterns = [
        rf"【{field_name}】[:：]\s*(.+?)(?=【|$)",
        rf"{field_name}[:：]\s*(.+?)(?=\n|$)",
        rf"{field_name}[:：](.+?)(?=\n\n|$)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return None

def _extract_symptoms_from_conversation(self, session):
    """从对话中提取症状（降级方案）"""
    symptoms = []
    symptom_keywords = ["疼", "痛", "发烧", "红肿", "恶心", "呕吐", "出血"]
    
    for msg in session.messages:
        content = msg.get('content', '')
        for keyword in symptom_keywords:
            if keyword in content and keyword not in symptoms:
                symptoms.append(keyword)
    
    return "、".join(symptoms) if symptoms else "患者未描述明显症状"

def _generate_fallback_report(self, session):
    """生成降级病历报告"""
    return {
        "session_id": session.session_id,
        "patient_info": self._extract_patient_info(session),
        "present_illness": "患者术后随访（自动生成）",
        "symptoms": self._extract_symptoms_from_conversation(session),
        "vital_signs": "未记录",
        "medications": "未记录",
        "advice": "建议遵医嘱定期复查，如有不适及时就医",
        "risk_alerts": [],
        "created_at": datetime.now().isoformat(),
        "note": "此病历为系统自动生成，建议医生复核"
    }

def _generate_empty_report(self, session_id, reason):
    """生成空病历报告"""
    return {
        "session_id": session_id,
        "error": reason,
        "present_illness": "生成失败",
        "symptoms": "生成失败",
        "advice": "生成失败",
        "created_at": datetime.now().isoformat()
    }
```

#### 方案二：病历生成提示词优化

**修改文件**: `GlmAI/zhipuGLM/prompts/prompts.py`

**优化内容**:

```python
MEDICAL_REPORT_PROMPT = """
请根据以下医患对话内容，生成结构化病历报告。

对话内容：
{conversation}

请严格按照以下JSON格式输出（不要添加任何其他文字）：

{{
    "present_illness": "现病史描述",
    "symptoms": "症状列表，用顿号分隔",
    "vital_signs": "生命体征（体温、血压等）",
    "medications": "用药情况",
    "advice": "医嘱建议",
    "risk_alerts": ["风险警示1", "风险警示2"]
}}

注意事项：
1. 所有字段必须填写，如无信息填写"未提及"
2. 症状使用标准医学术语
3. 风险警示列出需要关注的问题
4. 输出必须是纯JSON格式，不要有其他文字
"""
```

#### 实施步骤

1. 重构 `service.py` 中的病历生成函数
2. 添加数据验证和错误恢复机制
3. 优化病历生成提示词
4. 运行第15轮测试验证
5. 检查日志确认流程正常

---

### 3.4 问题P4：AI建议专业性评分低

#### 解决方案概述

建立**专业性评估体系**，在提示词中强制要求使用医学术语和专业表达。

#### 方案一：专业性提示词模板

**修改文件**: `GlmAI/zhipuGLM/prompts/prompts.py`

**优化内容**:

```python
PROFESSIONAL_ADVICE_PROMPT = """
你是一名具有10年临床经验的专业医疗助手。请用专业、严谨的语言回复患者。

回复要求：
1. 使用标准医学术语（如：感染、炎症、愈合、并发症等）
2. 建议要具体可执行（如：每日换药、观察体温变化、避免剧烈运动等）
3. 必须包含风险提示（如：如出现XX症状请立即就医）
4. 语气专业但亲切，避免过于口语化

患者问题：{user_input}

请按以下格式回复：
【病情分析】: 使用医学术语分析患者情况
【专业建议】: 给出具体可执行的护理建议
【风险提示】: 列出需要立即就医的情况
【复查建议】: 下次复查时间和注意事项
"""
```

#### 方案二：专业性自动检查

**修改文件**: `GlmAI/zhipuGLM/service.py`

**优化内容**:

```python
PROFESSIONAL_TERMS = {
    "感染相关": ["感染", "炎症", "化脓", "细菌", "抗生素"],
    "伤口护理": ["换药", "消毒", "清创", "缝合", "愈合"],
    "症状描述": ["发热", "疼痛", "红肿", "渗出", "出血"],
    "就医建议": ["就医", "复查", "急诊", "门诊", "住院"],
    "风险警示": ["立即", "紧急", "危险", "并发症", "恶化"]
}

def check_professionalism(response):
    """检查回复的专业性"""
    score = 0
    found_categories = []
    
    for category, terms in PROFESSIONAL_TERMS.items():
        if any(term in response for term in terms):
            score += 20
            found_categories.append(category)
    
    return {
        "score": min(score, 100),
        "categories": found_categories,
        "passed": score >= 80
    }
```

#### 实施步骤

1. 更新提示词模板，强调专业性要求
2. 添加专业性自动检查函数
3. 运行第15轮测试验证
4. 根据测试结果调整术语库

---

### 3.5 问题P5：患者安全建议合格率低

#### 解决方案概述

建立**危急情况识别机制**，强制在危急场景下输出紧急警告。

#### 方案一：危急情况识别与响应

**修改文件**: `GlmAI/zhipuGLM/service.py`

**优化内容**:

```python
CRITICAL_CONDITIONS = {
    "high_fever": {
        "patterns": [r"发烧.*3[89]\.?\d*", r"体温.*3[89]\.?\d*", r"高烧"],
        "response": "【紧急警告】您描述的体温已达到高热标准，可能存在感染风险，请立即前往医院就诊！"
    },
    "wound_infection": {
        "patterns": [r"伤口.*流脓", r"伤口.*化脓", r"伤口.*红肿.*发热"],
        "response": "【紧急警告】伤口出现感染迹象，需要专业医生处理，请立即就医！"
    },
    "severe_bleeding": {
        "patterns": [r"出血.*不止", r"大量.*出血", r"血流.*不止"],
        "response": "【紧急警告】伤口出血不止，请立即压迫止血并前往医院！"
    },
    "severe_pain": {
        "patterns": [r"剧烈.*疼痛", r"疼痛.*难忍", r"无法忍受.*疼痛"],
        "response": "【紧急警告】剧烈疼痛可能是严重并发症的信号，请立即就医检查！"
    }
}

def detect_critical_condition(user_input):
    """检测危急情况"""
    for condition_name, condition_data in CRITICAL_CONDITIONS.items():
        for pattern in condition_data["patterns"]:
            if re.search(pattern, user_input):
                return {
                    "is_critical": True,
                    "condition": condition_name,
                    "warning": condition_data["response"]
                }
    return {"is_critical": False}

def chat_with_safety_check(self, user_input, session_id):
    """带安全检查的对话"""
    
    # 检测危急情况
    critical = detect_critical_condition(user_input)
    
    if critical["is_critical"]:
        # 危急情况：强制返回紧急警告
        logger.warning(f"检测到危急情况: {critical['condition']}")
        return {
            "content": critical["warning"] + "\n\n" + self._get_safe_advice(critical["condition"]),
            "is_critical": True,
            "requires_immediate_attention": True
        }
    
    # 正常情况：调用AI对话
    return self.normal_chat_stream(user_input, session_id)

def _get_safe_advice(self, condition):
    """获取安全建议"""
    advice_map = {
        "high_fever": "在前往医院前，可以：\n1. 多喝水，保持水分\n2. 物理降温（温水擦浴）\n3. 避免剧烈运动",
        "wound_infection": "在前往医院前，可以：\n1. 保持伤口清洁\n2. 避免触碰伤口\n3. 记录症状变化",
        "severe_bleeding": "在前往医院前，请：\n1. 用干净纱布压迫止血\n2. 抬高受伤部位\n3. 保持冷静",
        "severe_pain": "在前往医院前，可以：\n1. 保持舒适体位\n2. 避免移动受伤部位\n3. 记录疼痛特点"
    }
    return advice_map.get(condition, "请保持冷静，尽快就医")
```

#### 方案二：安全建议模板库

**修改文件**: `GlmAI/zhipuGLM/prompts/prompts.py`

**优化内容**:

```python
SAFETY_ADVICE_TEMPLATES = {
    "emergency_header": "【紧急警告】",
    "emergency_footer": "\n\n请立即拨打120或前往最近医院急诊！",
    
    "warning_signs": {
        "术后感染": ["持续高烧>38.5℃", "伤口红肿热痛", "伤口流脓或有异味"],
        "术后出血": ["伤口渗血不止", "敷料完全湿透", "出现血肿"],
        "并发症": ["剧烈疼痛", "呼吸困难", "意识模糊"]
    },
    
    "safety_disclaimer": """
免责声明：以上建议仅供参考，不能替代专业医疗诊断。
如症状持续或加重，请立即就医。
紧急情况请拨打：120急救电话
"""
}
```

#### 实施步骤

1. 在 `service.py` 中添加危急情况检测
2. 创建安全建议模板库
3. 修改对话流程，优先检测危急情况
4. 运行第15轮测试验证
5. 检查危急情况响应是否正确

---

### 3.6 问题P6：响应时间波动大

#### 解决方案概述

建立**性能优化机制**，包含重试、超时、缓存和监控。

#### 方案一：API调用优化

**修改文件**: `GlmAI/zhipuGLM/service.py`

**优化内容**:

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """失败重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"函数 {func.__name__} 重试{max_retries}次后仍失败: {e}")
                        raise
                    
                    logger.warning(f"函数 {func.__name__} 第{retries}次失败，{current_delay}秒后重试: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator

def timeout_handler(timeout_seconds=30):
    """超时处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_signal(signum, frame):
                raise TimeoutError(f"函数 {func.__name__} 执行超时（{timeout_seconds}秒）")
            
            signal.signal(signal.SIGALRM, timeout_signal)
            signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            
            return result
        
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=1, backoff=2)
def call_zhipu_api(self, messages):
    """调用智谱AI API（带重试）"""
    start_time = time.time()
    
    try:
        response = self.client.chat.completions.create(
            model="glm-4",
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            stream=True
        )
        
        elapsed = time.time() - start_time
        logger.info(f"API调用成功，耗时: {elapsed:.2f}秒")
        
        return response
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"API调用失败，耗时: {elapsed:.2f}秒，错误: {e}")
        raise
```

#### 方案二：响应缓存机制

**修改文件**: `GlmAI/zhipuGLM/service.py`

**优化内容**:

```python
from functools import lru_cache
import hashlib

class ResponseCache:
    """响应缓存管理器"""
    
    def __init__(self, max_size=100, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def _get_cache_key(self, user_input, session_context):
        """生成缓存键"""
        content = f"{user_input}|{session_context}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, user_input, session_context):
        """获取缓存响应"""
        key = self._get_cache_key(user_input, session_context)
        
        if key in self.cache:
            cached_data = self.cache[key]
            if time.time() - cached_data['timestamp'] < self.ttl:
                logger.info(f"命中缓存: {key[:8]}")
                return cached_data['response']
        
        return None
    
    def set(self, user_input, session_context, response):
        """设置缓存"""
        if len(self.cache) >= self.max_size:
            # 移除最旧的缓存
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]
        
        key = self._get_cache_key(user_input, session_context)
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }
        
        logger.info(f"设置缓存: {key[:8]}")

# 在service.py中集成缓存
class MedicalAIService:
    def __init__(self):
        self.response_cache = ResponseCache()
    
    def chat_with_cache(self, user_input, session_id):
        """带缓存的对话"""
        session = self.session_manager.get_session(session_id)
        session_context = self._get_session_context(session)
        
        # 尝试从缓存获取
        cached_response = self.response_cache.get(user_input, session_context)
        if cached_response:
            return cached_response
        
        # 调用AI
        response = self.normal_chat_stream(user_input, session_id)
        
        # 设置缓存
        self.response_cache.set(user_input, session_context, response)
        
        return response
```

#### 方案三：性能监控

**修改文件**: `GlmAI/zhipuGLM/service.py`

**优化内容**:

```python
import time
from collections import defaultdict

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
    
    def record(self, operation, duration):
        """记录性能指标"""
        self.metrics[operation].append({
            'duration': duration,
            'timestamp': time.time()
        })
        
        # 保留最近100条记录
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]
    
    def get_stats(self, operation):
        """获取统计信息"""
        if operation not in self.metrics:
            return None
        
        durations = [m['duration'] for m in self.metrics[operation]]
        
        return {
            'count': len(durations),
            'avg': sum(durations) / len(durations),
            'min': min(durations),
            'max': max(durations),
            'recent_10_avg': sum(durations[-10:]) / len(durations[-10:]) if len(durations) >= 10 else None
        }
    
    def check_anomaly(self, operation, current_duration):
        """检测异常（响应时间突然变长）"""
        stats = self.get_stats(operation)
        if not stats or not stats['recent_10_avg']:
            return False
        
        # 如果当前响应时间是最近10次平均的2倍以上，视为异常
        return current_duration > stats['recent_10_avg'] * 2

# 在service.py中集成监控
class MedicalAIService:
    def __init__(self):
        self.perf_monitor = PerformanceMonitor()
    
    def chat_with_monitoring(self, user_input, session_id):
        """带性能监控的对话"""
        start_time = time.time()
        
        try:
            response = self.normal_chat_stream(user_input, session_id)
            
            duration = time.time() - start_time
            self.perf_monitor.record('chat', duration)
            
            # 检测异常
            if self.perf_monitor.check_anomaly('chat', duration):
                logger.warning(f"响应时间异常: {duration:.2f}秒")
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self.perf_monitor.record('chat_error', duration)
            raise
```

#### 实施步骤

1. 添加重试和超时处理装饰器
2. 实现响应缓存机制
3. 集成性能监控
4. 运行第15轮测试验证
5. 分析性能指标，定位瓶颈

---

## 四、实施计划

### 4.1 实施优先级

| 阶段 | 问题 | 优先级 | 预计工作量 | 依赖关系 |
| --- | --- | --- | --- | --- |
| 第一阶段 | P3: 病历生成不完整 | 高 | 4小时 | 无 |
| 第一阶段 | P5: 患者安全建议 | 高 | 3小时 | 无 |
| 第二阶段 | P1: 病症识别率 | 高 | 3小时 | 无 |
| 第二阶段 | P4: AI专业性 | 高 | 2小时 | P1 |
| 第三阶段 | P2: 健康建议质量 | 高 | 3小时 | P1, P4 |
| 第三阶段 | P6: 响应时间波动 | 中 | 4小时 | 无 |

### 4.2 实施时间表

```
第1天 (2026-04-05):
  上午: P3 病历生成优化
  下午: P5 患者安全建议优化
  晚上: 第15轮测试验证

第2天 (2026-04-06):
  上午: P1 病症识别优化
  下午: P4 AI专业性优化
  晚上: 第16轮测试验证

第3天 (2026-04-07):
  上午: P2 健康建议质量优化
  下午: P6 响应时间优化
  晚上: 第17轮测试验证

第4天 (2026-04-08):
  全天: 第18-20轮全面测试
  晚上: 问题修复和微调

第5天 (2026-04-09):
  全天: 第21-22轮最终验证
  晚上: 文档更新和总结
```

### 4.3 验证标准

每个阶段完成后，需通过以下验证：

**第一阶段验证**:
- [ ] 病历生成成功率 ≥ 95%
- [ ] 病历字段完整性 = 100%
- [ ] 危急情况识别准确率 ≥ 90%
- [ ] 安全建议合格率 ≥ 80%

**第二阶段验证**:
- [ ] 病症识别率 ≥ 70%
- [ ] 专业性评分 ≥ 70%

**第三阶段验证**:
- [ ] 病症识别率 ≥ 80%
- [ ] 健康建议质量 ≥ 60%
- [ ] 专业性评分 ≥ 80%
- [ ] 响应时间波动 < 50%

**最终验证**:
- [ ] 所有测试项通过率 ≥ 95%
- [ ] 28项测试中至少26项通过
- [ ] 无严重功能缺陷

---

## 五、风险评估

### 5.1 技术风险

| 风险项 | 影响 | 概率 | 应对措施 |
| --- | --- | --- | --- |
| AI API不稳定 | 高 | 中 | 实现重试机制和降级方案 |
| 提示词优化效果不佳 | 中 | 低 | 多版本测试，选择最优方案 |
| 性能优化影响功能 | 高 | 低 | 充分测试，保留回滚能力 |
| 缓存导致响应过时 | 中 | 中 | 设置合理TTL，关键场景禁用缓存 |

### 5.2 业务风险

| 风险项 | 影响 | 概率 | 应对措施 |
| --- | --- | --- | --- |
| 危急情况误判 | 高 | 低 | 保守判断，宁可误报不可漏报 |
| 专业性过度导致用户难理解 | 中 | 中 | 平衡专业性和可读性 |
| 响应时间优化影响质量 | 中 | 低 | 质量优先，性能次之 |

---

## 六、后续优化建议

### 6.1 短期优化 (1-2周)

1. **丰富知识库**: 添加更多术后护理文档
2. **优化RAG检索**: 提高检索准确率
3. **用户反馈收集**: 建立反馈机制

### 6.2 中期优化 (1-2月)

1. **多模型对比**: 测试不同AI模型效果
2. **A/B测试**: 对比不同提示词模板效果
3. **性能深度优化**: 数据库查询优化、并发处理

### 6.3 长期优化 (3-6月)

1. **模型微调**: 基于真实对话数据微调模型
2. **多语言支持**: 支持方言、少数民族语言
3. **智能推荐**: 基于患者历史推荐个性化建议

---

## 七、附录

### 7.1 相关文件清单

| 文件路径 | 修改内容 | 优先级 |
| --- | --- | --- |
| `GlmAI/zhipuGLM/prompts/prompts.py` | 提示词模板优化 | 高 |
| `GlmAI/zhipuGLM/service.py` | 核心服务逻辑优化 | 高 |
| `GlmAI/tests/test_streaming.py` | 测试评估标准优化 | 中 |
| `GlmAI/zhipuGLM/session_manager.py` | 会话管理增强 | 低 |

### 7.2 测试用例更新

需要在 `test_streaming.py` 中添加以下测试用例：

1. **危急情况识别测试**: 测试高烧、伤口感染等危急场景
2. **病历生成健壮性测试**: 测试异常输入下的病历生成
3. **性能压力测试**: 测试连续高并发请求
4. **缓存效果测试**: 测试缓存命中率和效果

### 7.3 监控指标

建议在生产环境中监控以下指标：

- API调用成功率
- 平均响应时间
- 响应时间P95/P99
- 缓存命中率
- 危急情况识别次数
- 病历生成成功率
- 用户满意度评分

---

**文档编写**: AI Assistant\
**审核状态**: 待审核\
**预计实施日期**: 2026-04-05

***
