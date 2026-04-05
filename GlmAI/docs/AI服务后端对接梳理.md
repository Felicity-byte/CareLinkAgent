# AI服务后端对接梳理

**文档版本**: v1.0\
**梳理日期**: 2026-04-04\
**服务名称**: GlmAI 术后随访智能助手

***

## 一、对接架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        外部调用方                                │
│                   (前端/其他微服务)                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ gRPC (端口: 50053)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AI服务核心层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ gRPC Server │  │   Service   │  │  Session    │             │
│  │ (server.py) │──│ (service.py)│──│  Manager    │             │
│  └─────────────┘  └──────┬──────┘  └─────────────┘             │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   智谱AI API  │  │  本地向量库   │  │  智谱知识库   │
│  (GLM-4.7)    │  │   (Chroma)    │  │   (可选)      │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │
        │                  │
        ▼                  ▼
┌───────────────┐  ┌───────────────┐
│  API Key认证  │  │  BGE嵌入模型  │
└───────────────┘  └───────────────┘
```

***

## 二、外部API对接

### 2.1 智谱AI API (必需)

**对接内容**: GLM-4.7-flash 大语言模型

| 配置项 | 值 | 说明 |
| --- | --- | --- |
| API Base URL | `https://open.bigmodel.cn/api/paas/v4/` | 智谱AI开放平台 |
| 模型名称 | `glm-4.7-flash` | 对话模型 |
| 认证方式 | API Key | 环境变量 `GLM_API_KEY` |
| 调用方式 | SDK (`zhipuai`) | Python SDK |

**对接代码位置**: `zhipuGLM/service.py`

```python
from zhipuai import ZhipuAI

api_key = os.environ.get("GLM_API_KEY")
GLOBAL_CLIENT = ZhipuAI(api_key=api_key)

# 调用示例
response = GLOBAL_CLIENT.chat.completions.create(
    model="glm-4.7-flash",
    messages=messages,
    temperature=0.7,
    max_tokens=2048,
    stream=True  # 流式输出
)
```

**对接要求**:
- ✅ 需要申请智谱AI开发者账号
- ✅ 需要获取API Key
- ✅ 需要配置环境变量 `GLM_API_KEY`
- ⚠️ 注意API调用频率限制

---

### 2.2 智谱知识库 API (可选)

**对接内容**: 智谱云端知识库检索

| 配置项 | 值 | 说明 |
| --- | --- | --- |
| API Key | 环境变量 `ZHIPU_API_KEY` | 可与GLM共用 |
| Knowledge ID | 环境变量 `ZHIPU_KNOWLEDGE_ID` | 知识库ID |
| 嵌入模型 | `embedding-3` | 向量化模型 |

**对接代码位置**: `zhipuGLM/knowledge/zhipu_knowledge.py`

```python
class ZhipuKnowledge:
    def __init__(self, api_key: str = None, knowledge_id: str = None):
        self.api_key = api_key or os.environ.get("ZHIPU_API_KEY")
        self.knowledge_id = knowledge_id or os.environ.get("ZHIPU_KNOWLEDGE_ID")
        self.client = ZhipuAI(api_key=self.api_key)
    
    def retrieve(self, query: str, top_k: int = 5):
        # 1. 生成查询向量
        response = self.client.embeddings.create(
            model="embedding-3",
            input=query
        )
        query_embedding = response.data[0].embedding
        
        # 2. 知识库检索
        knowledge_response = self.client.knowledge.search(
            knowledge_id=self.knowledge_id,
            embedding=query_embedding,
            top_k=top_k
        )
        return knowledge_response.results
```

**对接要求**:
- ⚠️ 需要在智谱平台创建知识库
- ⚠️ 需要上传医疗文档到知识库
- ✅ 如未配置，系统会自动降级使用本地RAG

***

## 三、本地资源对接

### 3.1 Chroma向量数据库 (必需)

**对接内容**: 本地向量数据库，存储医疗文档向量

| 配置项 | 路径 | 说明 |
| --- | --- | --- |
| 医疗文档库 | `zhipuGLM/medical_docs/` | 100个疾病文档 |
| 术后护理库 | `zhipuGLM/post_surgery_care/` | 术后护理文档 |
| 向量存储路径 | `zhipuGLM/chroma_db_medical/` | Chroma持久化目录 |
| 术后向量存储 | `zhipuGLM/chroma_db_post_surgery/` | 术后护理向量库 |

**对接代码位置**: `zhipuGLM/rag/rag_core.py`

```python
from langchain_chroma import Chroma

def build_or_load_rag_index(docs_dir: str, persist_dir: str):
    # 加载嵌入模型
    bge_embeddings = utils.get_bge_embedding_model()
    
    # 加载或创建向量库
    if os.path.exists(persist_dir):
        vectorstore = Chroma(
            persist_directory=persist_dir, 
            embedding_function=bge_embeddings
        )
    else:
        # 从文档构建
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=bge_embeddings,
            persist_directory=persist_dir
        )
    return vectorstore
```

**对接要求**:
- ✅ 自动创建，无需手动配置
- ⚠️ 首次启动需要加载BGE模型（约6秒）
- ⚠️ 需要确保磁盘空间充足

---

### 3.2 BGE嵌入模型 (必需)

**对接内容**: 中文文本嵌入模型，用于向量化

| 配置项 | 值 | 说明 |
| --- | --- | --- |
| 模型名称 | `BAAI/bge-small-zh-v1.5` | 中文小型嵌入模型 |
| 加载方式 | HuggingFace | 自动下载 |
| 模型大小 | ~100MB | 首次下载 |

**对接代码位置**: `zhipuGLM/utils/utils.py`

```python
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

def get_bge_embedding_model():
    embeddings = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-small-zh-v1.5",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    return embeddings
```

**对接要求**:
- ✅ 首次运行自动下载
- ⚠️ 需要网络连接（首次）
- ⚠️ 加载耗时约6秒

---

### 3.3 医疗文档库 (必需)

**对接内容**: 本地医疗知识文档

| 文档类型 | 数量 | 路径 |
| --- | --- | --- |
| 疾病文档 | 100个 | `zhipuGLM/medical_docs/*.txt` |
| 术后护理文档 | 1个 | `zhipuGLM/post_surgery_care/*.txt` |

**文档格式示例**:
```
文件名: 001_急性感染性疾病.txt
内容:
【疾病名称】急性感染性疾病
【症状描述】...
【治疗方法】...
【注意事项】...
```

**对接要求**:
- ✅ 已预置，无需配置
- ⚠️ 可扩展添加更多文档

***

## 四、gRPC服务接口

### 4.1 服务配置

| 配置项 | 值 | 说明 |
| --- | --- | --- |
| 服务端口 | `50053` | gRPC服务端口 |
| 协议定义 | `connect/medical_ai.proto` | Protobuf定义 |
| 服务实现 | `connect/server.py` | gRPC服务端 |

### 4.2 接口列表

#### 接口1: CreateSession - 创建会话

**请求参数**:
```protobuf
message CreateSessionRequest {
    string patient_id = 1;      // 患者ID
    string patient_name = 2;    // 患者姓名
    string surgery_date = 3;    // 手术日期
}
```

**响应参数**:
```protobuf
message CreateSessionResponse {
    string session_id = 1;      // 会话ID
    string created_at = 2;      // 创建时间
    string welcome_message = 3; // 欢迎语
}
```

---

#### 接口2: Chat - 流式对话

**请求参数** (流式):
```protobuf
message ChatRequest {
    string session_id = 1;  // 会话ID
    string message = 2;     // 用户消息
    bool is_end = 3;        // 是否结束对话
}
```

**响应参数** (流式):
```protobuf
message ChatResponse {
    string content = 1;     // AI回复内容
    bool is_final = 2;      // 是否最后一条消息
    string reference = 3;   // 参考文档
}
```

---

#### 接口3: EndSession - 结束会话

**请求参数**:
```protobuf
message EndSessionRequest {
    string session_id = 1;  // 会话ID
}
```

**响应参数**:
```protobuf
message EndSessionResponse {
    MedicalReport report = 1;  // 结构化病历
}

message MedicalReport {
    PatientInfo patient_info = 1;
    PostSurgeryStatus surgery_status = 2;
    PastHistory past_history = 3;
    string present_illness = 4;
    string advice = 5;
    string risk_alerts = 6;
}
```

---

#### 接口4: GetSessionHistory - 获取历史

**请求参数**:
```protobuf
message GetSessionHistoryRequest {
    string session_id = 1;  // 会话ID
}
```

**响应参数**:
```protobuf
message GetSessionHistoryResponse {
    string session_id = 1;
    string surgery_type = 2;
    repeated Message messages = 3;
    string created_at = 4;
    string status = 5;
}
```

***

## 五、环境变量配置

### 5.1 必需配置

| 变量名 | 说明 | 示例值 |
| --- | --- | --- |
| `GLM_API_KEY` | 智谱AI API密钥 | `your_api_key_here` |

### 5.2 可选配置

| 变量名 | 说明 | 示例值 |
| --- | --- | --- |
| `ZHIPU_API_KEY` | 智谱知识库API密钥 | 与GLM_API_KEY相同 |
| `ZHIPU_KNOWLEDGE_ID` | 智谱知识库ID | `knowledge_xxx` |

### 5.3 配置文件

**文件路径**: `GlmAI/.env`

```env
GLM_API_KEY=your_glm_api_key_here
ZHIPU_API_KEY=your_zhipu_api_key_here
ZHIPU_KNOWLEDGE_ID=your_knowledge_id_here
```

***

## 六、数据流转图

### 6.1 对话流程

```
用户消息
    │
    ▼
┌─────────────────┐
│  gRPC Server    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Session Manager │ ← 检查会话状态
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  混合检索引擎   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│本地RAG│ │智谱知识库 │
└───┬───┘ └─────┬─────┘
    │           │
    └─────┬─────┘
          │
          ▼
┌─────────────────┐
│   智谱AI LLM    │ ← 生成回复
└────────┬────────┘
         │
         ▼
    流式返回用户
```

### 6.2 病历生成流程

```
结束会话请求
    │
    ▼
┌─────────────────┐
│ Session Manager │ ← 获取对话历史
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   智谱AI LLM    │ ← 生成结构化病历
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Medical Report  │ ← 返回病历
└─────────────────┘
```

***

## 七、对接检查清单

### 7.1 必需项检查

| 检查项 | 状态 | 说明 |
| --- | --- | --- |
| 智谱AI API Key | ⬜ | 需要申请并配置 |
| Python环境 | ⬜ | Python 3.8+ |
| 依赖安装 | ⬜ | `pip install -r requirements.txt` |
| 端口50053可用 | ⬜ | 确保端口未被占用 |
| 磁盘空间 | ⬜ | 至少1GB（向量库+模型） |

### 7.2 可选项检查

| 检查项 | 状态 | 说明 |
| --- | --- | --- |
| 智谱知识库ID | ⬜ | 如需云端知识库 |
| 自定义医疗文档 | ⬜ | 可扩展文档库 |

### 7.3 启动命令

```bash
# 1. 进入项目目录
cd GlmAI

# 2. 配置环境变量
# 创建 .env 文件并填入 API Key

# 3. 启动服务
python connect/server.py
```

***

## 八、依赖包列表

```
zhipuai              # 智谱AI SDK
grpcio               # gRPC框架
grpcio-tools         # gRPC工具
langchain-community  # LangChain社区版
langchain-chroma     # Chroma向量库集成
langchain-text-splitters  # 文本分割
chromadb             # Chroma数据库
sentence-transformers  # 嵌入模型
python-dotenv        # 环境变量管理
```

***

## 九、常见问题

### Q1: API Key如何获取？

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册开发者账号
3. 创建应用获取API Key

### Q2: 向量数据库加载慢？

- 首次启动需要加载BGE模型（约6秒）
- 已实现后台加载，不影响服务启动
- 后续启动会从缓存加载，速度更快

### Q3: 如何扩展医疗文档？

1. 在 `zhipuGLM/medical_docs/` 添加TXT文件
2. 删除 `chroma_db_medical/` 目录
3. 重启服务，自动重建向量库

### Q4: 如何切换模型？

修改 `zhipuGLM/service.py` 中的模型名称：
```python
model="glm-4.7-flash"  # 可改为其他智谱模型
```

***

**文档编写**: AI Assistant\
**更新日期**: 2026-04-04
