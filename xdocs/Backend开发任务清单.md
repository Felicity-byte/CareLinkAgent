# Backend应用后端开发任务清单

**文档版本**: v1.0\
**创建日期**: 2026-04-04\
**服务名称**: MediMeow Backend API

***

## 一、架构说明

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端应用                                │
│                     (Vue/React/小程序)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP REST API
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (应用后端)                           │
│                    FastAPI + TortoiseORM                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  REST API   │  │  Database   │  │  gRPC Client│             │
│  │  Routers    │  │  Models     │  │  (调用AI)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────┬───────────────────────────────────────┘
                          │ gRPC (端口: 50053)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GlmAI (AI服务)                               │
│                    术后随访智能助手                              │
└─────────────────────────────────────────────────────────────────┘
```

***

## 二、Backend需要做的事

### 2.1 对接GlmAI服务 (必需)

| 编号 | 任务 | 说明 | 状态 |
| --- | --- | --- | --- |
| B1 | 更新gRPC客户端 | 复制GlmAI的proto文件，生成新的客户端代码 | ⬜ 待开发 |
| B2 | 创建术后随访服务类 | 封装对GlmAI的gRPC调用 | ⬜ 待开发 |
| B3 | 配置AI服务地址 | 环境变量配置GlmAI服务地址(localhost:50053) | ⬜ 待开发 |

### 2.2 创建API接口 (必需)

| 编号 | 任务 | 说明 | 状态 |
| --- | --- | --- | --- |
| B4 | 创建随访会话接口 | POST /followup/session | ⬜ 待开发 |
| B5 | 创建对话接口 | POST /followup/chat (流式) | ⬜ 待开发 |
| B6 | 结束会话接口 | POST /followup/end | ⬜ 待开发 |
| B7 | 获取历史接口 | GET /followup/history/{session_id} | ⬜ 待开发 |

### 2.3 数据存储 (必需)

| 编号 | 任务 | 说明 | 状态 |
| --- | --- | --- | --- |
| B8 | 对话记录存储 | 存储每条对话到chat_records表 | ⬜ 待开发 |
| B9 | 病历报告存储 | 存储AI生成的病历到ai_diagnosis_report表 | ⬜ 待开发 |
| B10 | 会话状态管理 | 管理随访会话的生命周期 | ⬜ 待开发 |

### 2.4 用户系统集成 (必需)

| 编号 | 任务 | 说明 | 状态 |
| --- | --- | --- | --- |
| B11 | 患者身份验证 | 验证患者身份，获取患者信息 | ⬜ 待开发 |
| B12 | 医生查看权限 | 医生可查看患者的随访记录 | ⬜ 待开发 |
| B13 | 关联就诊记录 | 随访记录关联到visit_record | ⬜ 待开发 |

***

## 三、任务详细说明

### B1: 更新gRPC客户端

**当前问题**: Backend的gRPC客户端连接的是旧AI服务(端口50051)，需要更新为GlmAI(端口50053)

**需要做的事**:

1. **复制Proto文件**
   ```bash
   # 从GlmAI复制proto文件到Backend
   cp GlmAI/connect/medical_ai.proto Backend/app/services/grpc_client/
   ```

2. **重新生成客户端代码**
   ```bash
   cd Backend/app/services/grpc_client
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. medical_ai.proto
   ```

3. **Proto文件差异**

   **旧版 (Backend当前)**:
   ```protobuf
   service MedicalAIService {
       rpc ProcessMedicalAnalysisSync(AnalysisRequest) returns (AnalysisReport);
       rpc ProcessMedicalAnalysis(AnalysisRequest) returns (stream StreamChunk);
   }
   ```

   **新版 (GlmAI)**:
   ```protobuf
   service PostSurgeryFollowUpService {
       rpc CreateSession(CreateSessionRequest) returns (CreateSessionResponse);
       rpc Chat(stream ChatRequest) returns (stream ChatResponse);
       rpc EndSession(EndSessionRequest) returns (EndSessionResponse);
       rpc GetSessionHistory(GetSessionHistoryRequest) returns (GetSessionHistoryResponse);
   }
   ```

**文件位置**: `Backend/app/services/grpc_client/`

---

### B2: 创建术后随访服务类

**需要做的事**:

创建新文件 `Backend/app/services/followup_service.py`:

```python
import grpc
from .grpc_client import medical_ai_pb2 as pb2
from .grpc_client import medical_ai_pb2_grpc as pb2_grpc

class FollowUpService:
    """术后随访服务"""
    
    def __init__(self):
        self.host = os.getenv('GLM_AI_HOST', '127.0.0.1:50053')
    
    def create_session(self, patient_id: str, patient_name: str, surgery_date: str):
        """创建随访会话"""
        with grpc.insecure_channel(self.host) as channel:
            stub = pb2_grpc.PostSurgeryFollowUpServiceStub(channel)
            request = pb2.CreateSessionRequest(
                patient_id=patient_id,
                patient_name=patient_name,
                surgery_date=surgery_date
            )
            response = stub.CreateSession(request)
            return {
                "session_id": response.session_id,
                "created_at": response.created_at,
                "welcome_message": response.welcome_message
            }
    
    async def chat_stream(self, session_id: str, message: str):
        """流式对话"""
        # 实现流式对话
        pass
    
    def end_session(self, session_id: str):
        """结束会话，获取病历"""
        pass
    
    def get_history(self, session_id: str):
        """获取对话历史"""
        pass
```

**文件位置**: `Backend/app/services/followup_service.py`

---

### B3: 配置AI服务地址

**需要做的事**:

修改 `Backend/.env`:
```env
# GlmAI 服务地址
GLM_AI_HOST=127.0.0.1:50053
```

修改 `Backend/config.py`:
```python
class Settings(BaseSettings):
    # ... 其他配置 ...
    GLM_AI_HOST: str = "127.0.0.1:50053"
```

---

### B4-B7: 创建API接口

**需要做的事**:

创建新文件 `Backend/app/routers/followup.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.services.followup_service import FollowUpService
from app.utils.auth import get_current_user

router = APIRouter()
followup_service = FollowUpService()

@router.post("/session")
async def create_session(
    patient_id: str,
    patient_name: str,
    surgery_date: str,
    user = Depends(get_current_user)
):
    """创建随访会话"""
    result = followup_service.create_session(patient_id, patient_name, surgery_date)
    return {"code": "200", "data": result}

@router.post("/chat")
async def chat(
    session_id: str,
    message: str,
    user = Depends(get_current_user)
):
    """流式对话"""
    async def generate():
        async for chunk in followup_service.chat_stream(session_id, message):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/end")
async def end_session(
    session_id: str,
    user = Depends(get_current_user)
):
    """结束会话，生成病历"""
    result = followup_service.end_session(session_id)
    return {"code": "200", "data": result}

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    user = Depends(get_current_user)
):
    """获取对话历史"""
    result = followup_service.get_history(session_id)
    return {"code": "200", "data": result}
```

**文件位置**: `Backend/app/routers/followup.py`

---

### B8-B10: 数据存储

**需要做的事**:

1. **对话记录存储** - 使用现有 `ChatRecord` 模型
2. **病历报告存储** - 使用现有 `AIDiagnosisReport` 模型
3. **会话状态管理** - 可能需要新建 `FollowUpSession` 模型

新建模型 `Backend/app/models/followup_session.py`:
```python
class FollowUpSession(Model):
    """随访会话表"""
    id = fields.CharField(max_length=36, pk=True)
    patient_id = fields.CharField(max_length=36)
    surgery_date = fields.DateField()
    surgery_type = fields.CharField(max_length=100, null=True)
    status = fields.CharField(max_length=20)  # ACTIVE, COMPLETED
    ai_session_id = fields.CharField(max_length=100)  # GlmAI的session_id
    created_at = fields.DatetimeField(auto_now_add=True)
    ended_at = fields.DatetimeField(null=True)
```

---

### B11-B13: 用户系统集成

**需要做的事**:

1. **患者身份验证** - 使用现有 `get_current_user` 验证
2. **医生查看权限** - 添加医生角色检查
3. **关联就诊记录** - 在 `FollowUpSession` 中添加 `visit_record_id` 字段

***

## 四、文件修改清单

| 文件 | 操作 | 任务 |
| --- | --- | --- |
| `app/services/grpc_client/medical_ai.proto` | 更新 | B1 |
| `app/services/grpc_client/medical_ai_pb2.py` | 重新生成 | B1 |
| `app/services/grpc_client/medical_ai_pb2_grpc.py` | 重新生成 | B1 |
| `app/services/followup_service.py` | 新建 | B2 |
| `config.py` | 修改 | B3 |
| `.env` | 修改 | B3 |
| `app/routers/followup.py` | 新建 | B4-B7 |
| `app/models/followup_session.py` | 新建 | B10 |
| `main.py` | 修改 | 注册路由 |

***

## 五、开发顺序建议

```
第1步: B1(更新gRPC客户端) + B3(配置服务地址)
第2步: B2(创建服务类)
第3步: B4-B7(创建API接口)
第4步: B8-B10(数据存储)
第5步: B11-B13(用户系统集成)
第6步: 测试验证
```

***

## 六、验收标准

| 任务 | 验收标准 |
| --- | --- |
| B1-B3 | gRPC客户端可正常连接GlmAI服务 |
| B4 | 创建会话成功返回session_id和欢迎语 |
| B5 | 流式对话正常返回AI回复 |
| B6 | 结束会话成功返回病历报告 |
| B7 | 可查询对话历史 |
| B8-B10 | 数据正确存储到数据库 |
| B11-B13 | 权限验证正确，记录关联正确 |

***

## 七、与GlmAI的接口对照

| Backend接口 | GlmAI接口 | 说明 |
| --- | --- | --- |
| POST /followup/session | CreateSession | 创建会话 |
| POST /followup/chat | Chat | 流式对话 |
| POST /followup/end | EndSession | 结束会话 |
| GET /followup/history/{id} | GetSessionHistory | 获取历史 |

***

**文档编写**: AI Assistant\
**更新日期**: 2026-04-04
