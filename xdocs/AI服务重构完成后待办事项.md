# AI 服务重构完成后待办事项

## 一、文件修改清单

### 1.1 需要修改的现有文件

| 文件路径 | 修改内容 | 优先级 |
|----------|----------|--------|
| `GlmAI/ai.py` | 启动配置、导入新模块 | 高 |
| `GlmAI/connect/server.py` | gRPC 接口重构（新增 CreateSession/Chat/EndSession 等） | 高 |
| `GlmAI/connect/medical_ai.proto` | Proto 定义更新 | 高 |
| `GlmAI/zhipuGLM/service.py` | 混合检索逻辑、流式对话、病历生成 | 高 |
| `GlmAI/zhipuGLM/prompts/prompts.py` | 对话提示词更新 | 高 |
| `GlmAI/zhipuGLM/config/config.py` | 智谱知识库配置 | 中 |
| `GlmAI/zhipuGLM/rag/rag_core.py` | 支持手术类型定向检索 | 中 |

### 1.2 需要新增的文件

| 文件路径 | 说明 |
|----------|------|
| `GlmAI/zhipuGLM/knowledge/__init__.py` | 知识库模块初始化 |
| `GlmAI/zhipuGLM/knowledge/zhipu_knowledge.py` | 智谱知识库调用 |
| `GlmAI/zhipuGLM/post_surgery_care/*.txt` | 术后护理文档（16篇） |

---

## 二、智谱知识库配置

### 2.1 创建知识库
1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 进入「知识库」模块 → 创建知识库（如「通用疾病知识库」）
3. 获取知识库 ID（`knowledge_id`）

### 2.2 上传文档
1. 将 `medical_docs/` 下的 100 篇普通疾病文档上传
2. 等待向量化完成

### 2.3 获取 API Key
在智谱平台获取 API Key

---

## 三、本地术后护理文档

### 3.1 文档目录
```
GlmAI\zhipuGLM\post_surgery_care\
```

### 3.2 文档清单

**基础通用类（必选）**
| 序号 | 文档名称 | 说明 |
|------|----------|------|
| 101 | 术后伤口疼痛 | 伤口疼痛定义、表现、缓解方法 |
| 102 | 术后伤口护理 | 伤口清洁、换药、防护 |
| 103 | 术后发热 | 发热原因、处理方法 |
| 104 | 术后乏力 | 乏力原因、恢复建议 |
| 105 | 术后恶心呕吐 | 恶心呕吐原因、缓解方法 |
| 106 | 术后腹胀 | 腹胀原因、排气排便 |
| 107 | 术后便秘 | 便秘预防、饮食调整 |
| 108 | 术后饮食指南 | 饮食阶段、营养建议 |
| 109 | 术后活动指导 | 活动时机、注意事项 |
| 110 | 术后失眠 | 失眠原因、改善方法 |

**特殊情况类**
| 序号 | 文档名称 | 说明 |
|------|----------|------|
| 111 | 术后伤口红肿 | 红肿原因、就医指征 |
| 112 | 术后伤口渗液 | 渗液性质、护理要点 |
| 113 | 术后疤痕护理 | 疤痕预防、护理方法 |
| 114 | 术后拆线指引 | 拆线时间、注意事项 |
| 115 | 术后复查项目 | 复查项目、时间安排 |
| 116 | 术后异常预警 | 需就医的异常情况 |

### 3.3 文档格式模板
```txt
【文档标题】

【定义】
简要说明...

【典型表现】
- 症状1
- 症状2

【缓解方法】
- 方法1
- 方法2

【异常预警】
出现以下情况需就医：
- ...

【日常护理】
- ...
```

---

## 四、混合检索实现

### 4.1 检索流程

```
患者消息
     │
     ▼
┌────────────────────────────────────────┐
│  1. 本地 RAG 检索                      │
│     - post_surgery_care/ 文档          │
│     - 基于手术类型定向检索              │
└────────────────┬───────────────────────┘
           ┌──────┴──────┐
       检索到         未检索到
           │             │
           ▼             ▼
    文档 + LLM      ┌────────────────────────────────────────┐
   优化回答         │  2. 智谱知识库检索                     │
                   └────────────────┬───────────────────────┘
                                     │
                              ┌──────┴──────┐
                              ▼             ▼
                          检索到         未检索到
                              │             │
                              ▼             ▼
                        文档 + LLM      ┌────────────────────────────────────────┐
                       优化回答         │  3. LLM 自身知识回答                   │
                                       │     - 直接调用 LLM                     │
                                       │     - 基于医学知识生成                  │
```

### 4.2 核心代码逻辑

```python
def hybrid_retrieve(query, surgery_type):
    # 1. 本地 RAG 检索
    local_docs = local_rag_retrieve(query, surgery_type)
    if local_docs:
        return "doc_llm", local_docs

    # 2. 智谱知识库检索
    zhipu_docs = zhipu_knowledge.retrieve(query)
    if zhipu_docs:
        return "doc_llm", zhipu_docs

    # 3. LLM 自身知识
    return "llm_only", None
```

---

## 五、环境变量配置

```bash
# 智谱 API Key
ZHIPU_API_KEY=your_api_key

# 智谱知识库 ID
ZHIPU_KNOWLEDGE_ID=your_knowledge_id

# 本地 RAG
LOCAL_RAG_PATH=D:\Trea\medical systems\CareLinkAgent\GlmAI\zhipuGLM\post_surgery_care
CHROMA_DB_PATH=D:\Trea\medical systems\CareLinkAgent\GlmAI\zhipuGLM\chroma_db_medical

# gRPC
GRPC_PORT=50051
```

---

## 六、服务部署

### 6.1 启动
```bash
cd D:\Trea\medical systems\CareLinkAgent\GlmAI
python -u ai.py
```

### 6.2 验证步骤
1. 检查端口 50051 监听状态
2. 测试 CreateSession
3. 测试 Chat 流式对话
4. 测试 EndSession 生成报告

---

## 七、功能测试清单

### 7.1 对话流程
- [ ] 创建会话，获取 session_id
- [ ] AI 询问手术类型
- [ ] 患者输入手术类型
- [ ] AI 开始收集症状
- [ ] 本地 RAG 检索
- [ ] 智谱知识库检索
- [ ] 检索到文档时：文档 + LLM 优化
- [ ] 未检索到文档时：LLM 自身知识
- [ ] 流式输出正常
- [ ] 结束对话生成报告

### 7.2 报告生成
- [ ] 结构化病历格式正确
- [ ] 包含患者信息、主诉、现病史
- [ ] AI 辅助分析合理

---

## 八、进度跟踪

| 阶段 | 任务 | 状态 |
|------|------|------|
| **知识库** | 创建智谱知识库 | ⬜ |
| | 上传普通疾病文档 | ⬜ |
| **文档** | 创建术后护理文档（16篇） | ⬜ |
| **代码** | 修改 ai.py | ⬜ |
| | 修改 server.py | ⬜ |
| | 修改 medical_ai.proto | ⬜ |
| | 修改 service.py | ⬜ |
| | 修改 prompts.py | ⬜ |
| | 修改 rag_core.py | ⬜ |
| | 新增 zhipu_knowledge.py | ⬜ |
| **配置** | 配置 API Keys | ⬜ |
| **部署** | 启动 AI 服务 | ⬜ |
| | 功能测试 | ⬜ |
| | 对接后端（复查预约由后端实现） | ⬜ |
| | 部署上线 | ⬜ |

---

## 九、参考链接

| 项目 | 链接 |
|------|------|
| 智谱 AI 开放平台 | https://open.bigmodel.cn/ |
| API 文档 | https://open.bigmodel.cn/dev/api |
