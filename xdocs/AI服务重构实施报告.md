# AI 服务重构实施报告

## 一、实施概述

| 项目 | 内容 |
|------|------|
| 项目名称 | 术后随访 AI 协同系统 - AI 服务重构 |
| 实施日期 | 2026-04-03 |
| 实施范围 | Phase 1-3, Phase 5（核心功能） |
| 技术栈 | Python / gRPC / GLM-4.7-Flash / Chroma / BGE |

---

## 二、实施流程

### Phase 1: 基础框架

```
步骤 1: 重构 Proto 定义
  └── 文件: GlmAI/connect/medical_ai.proto
  ├── CreateSession - 创建会话
  ├── Chat (流式) - 流式对话
  ├── EndSession - 结束会话，返回病历
  ├── GetSessionHistory - 获取对话历史
  └── MedicalReport - 结构化病历定义

步骤 2: 实现会话管理模块
  └── 新增文件: GlmAI/zhipuGLM/session_manager.py
  ├── Session 类：会话数据结构
  ├── SessionManager 类：会话管理器
  ├── 会话状态：WAITING_SURGERY → ACTIVE → COMPLETED/CANCELLED
  └── 全局实例：session_manager

步骤 3: 重构 gRPC 服务端
  └── 文件: GlmAI/connect/server.py
  ├── PostSurgeryFollowUpServicer 类
  ├── 实现 4 个 RPC 接口
  └── 启动端口: 50051
```

### Phase 2: AI 对话 + 混合检索

```
步骤 4: 更新提示词
  └── 文件: GlmAI/zhipuGLM/prompts/prompts.py
  ├── WELCOME_PROMPT - 欢迎语（询问手术类型）
  ├── SURGERY_CONFIRMED_PROMPT - 手术确认后开场
  ├── CHAT_SYSTEM_PROMPT - 对话阶段系统提示词
  ├── RAG_CONTEXT_TEMPLATE - RAG 上下文模板
  ├── MEDICAL_REPORT_PROMPT - 病历生成提示词
  └── END_CONFIRMATION_PROMPT - 结束询问

步骤 5: 新增智谱知识库模块
  └── 新增目录: GlmAI/zhipuGLM/knowledge/
      ├── __init__.py
      └── zhipu_knowledge.py
          ├── ZhipuKnowledge 类
          ├── retrieve() - 检索文档
          └── is_relevant() - 判断相关性

步骤 6: 更新 RAG 检索
  └── 文件: GlmAI/zhipuGLM/rag/rag_core.py
  ├── retrieve_by_surgery_type() - 支持手术类型定向检索
  ├── format_retrieved_context() - 格式化检索结果
  ├── build_post_surgery_rag_index() - 构建术后护理向量库
  └── build_general_rag_index() - 构建通用疾病向量库

步骤 7: 实现混合检索逻辑 + 流式对话
  └── 文件: GlmAI/zhipuGLM/service.py
  ├── initialize_service() - 服务初始化
  ├── hybrid_retrieve() - 混合检索逻辑
  │   ├── 1. 本地 RAG 检索（术后护理文档）
  │   ├── 2. 智谱知识库检索（普通疾病文档）
  │   └── 3. LLM 自身知识（无相关文档时）
  ├── create_session() - 创建会话
  ├── chat_stream() - 流式对话
  │   ├── 阶段1: 确认手术类型
  │   ├── 阶段2: 症状收集（混合检索 + LLM）
  │   └── 阶段3: 结束对话
  ├── generate_medical_report() - 生成病历
  ├── get_session_history() - 获取历史
  └── end_session() - 结束会话
```

### Phase 3: 报告生成

```
步骤 8: 实现结构化病历生成
  └── 已在 service.py 中实现
  ├── generate_medical_report() 函数
  ├── 使用 MEDICAL_REPORT_PROMPT 提示词
  └── 输出格式：
      ├── 一、患者信息
      ├── 二、主诉
      ├── 三、现病史
      ├── 四、术后恢复情况
      ├── 五、AI 辅助分析
      └── 六、会话信息
```

### Phase 5: 配置和启动

```
步骤 9: 更新启动脚本
  └── 文件: GlmAI/ai.py
  ├── 加载 .env 文件
  ├── 检查环境变量
  ├── 启动 gRPC 服务
  └── 打印服务状态信息
```

---

## 三、修改/新增文件清单

### 修改的文件（7个）

| 文件路径 | 修改内容 |
|----------|----------|
| `GlmAI/connect/medical_ai.proto` | 重构为新的接口定义 |
| `GlmAI/connect/server.py` | 重构为新的 gRPC 服务端 |
| `GlmAI/zhipuGLM/service.py` | 实现混合检索和流式对话 |
| `GlmAI/zhipuGLM/prompts/prompts.py` | 更新为术后随访提示词 |
| `GlmAI/zhipuGLM/rag/rag_core.py` | 支持手术类型定向检索 |
| `GlmAI/zhipuGLM/config/config.py` | 配置保持不变 |
| `GlmAI/ai.py` | 更新启动脚本 |

### 新增的文件（4个）

| 文件路径 | 说明 |
|----------|------|
| `GlmAI/zhipuGLM/session_manager.py` | 会话管理模块 |
| `GlmAI/zhipuGLM/knowledge/__init__.py` | 知识库模块初始化 |
| `GlmAI/zhipuGLM/knowledge/zhipu_knowledge.py` | 智谱知识库调用模块 |

---

## 四、API 接口列表

| RPC 方法 | 功能 | 请求 | 响应 |
|----------|------|------|------|
| CreateSession | 创建会话 | patient_id, name, date | session_id, welcome_msg |
| Chat | 流式对话 | session_id, message, is_end | content (流式) |
| EndSession | 结束会话 | session_id | MedicalReport |
| GetSessionHistory | 获取历史 | session_id | messages[] |

---

## 五、混合检索架构

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
                          检索到         未检索到
                              │             │
                              ▼             ▼
                        文档 + LLM      ┌────────────────────────────────────────┐
                       优化回答         │  3. LLM 自身知识回答                   │
                                       │     - 直接调用 LLM                     │
                                       └────────────────┬───────────────────────┘
                                                        │
                                                        ▼
                                                  AI 回复
```

---

## 六、环境变量配置

```bash
# 必需
GLM_API_KEY=your_api_key

# 可选（智谱知识库）
ZHIPU_API_KEY=your_zhipu_key
ZHIPU_KNOWLEDGE_ID=your_knowledge_id

# 自动设置
HF_ENDPOINT=https://hf-mirror.com
```

---

## 七、启动命令

```bash
cd D:\Trea\medical systems\CareLinkAgent\GlmAI
python -u ai.py
```

---

## 八、测试验证

### 8.1 功能测试清单

- [ ] 启动服务，端口 50051 正常监听
- [ ] 调用 CreateSession 创建会话
- [ ] 调用 Chat 进行流式对话
- [ ] 手术类型确认流程正常
- [ ] 本地 RAG 检索正常
- [ ] 智谱知识库检索正常（如已配置）
- [ ] 调用 EndSession 生成病历
- [ ] 调用 GetSessionHistory 获取历史

### 8.2 后续工作（后端负责）

- 复查预约功能实现
- 对话历史存储到数据库
- 结构化病历存储到数据库
- API 网关 SSE 转发
- 前端对接

---

## 九、注意事项

1. **首次运行**需要构建向量数据库（post_surgery_care/ 目录）
2. **智谱知识库**需要先在平台创建并上传文档
3. **会话超时**默认 30 分钟无活动自动结束
4. **流式输出**使用 gRPC 双向流协议

---

## 十、总结

本次重构完成了 AI 服务的核心功能：

| 功能 | 状态 |
|------|------|
| 会话管理 | ✅ 完成 |
| 流式对话 | ✅ 完成 |
| 混合检索 | ✅ 完成 |
| 病历生成 | ✅ 完成 |
| gRPC 接口 | ✅ 完成 |

**下一步**：后端对接、前端开发、功能测试
