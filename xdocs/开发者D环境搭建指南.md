# 开发者 D 环境搭建与开发指南

**项目名称**: CareLinkAgent - 智能医疗预诊系统
**仓库地址**: https://github.com/Felicity-byte/CareLinkAgent.git
**主要职责**: 后端开发 (Backend)

---

## 一、工作流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    开发者 D 工作流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 克隆项目                                                 │
│     git clone → cd CareLinkAgent                            │
│            ↓                                                │
│  2. 配置后端环境                                             │
│     pip install → 配置.env → 数据库初始化                    │
│            ↓                                                │
│  3. 创建分支                                                 │
│     git checkout -b Backend                                 │
│            ↓                                                │
│  4. 开发代码                                                 │
│     启动后端 → 编写API → 测试接口                            │
│            ↓                                                │
│  5. 提交推送                                                 │
│     git add → git commit → git push                         │
│            ↓                                                │
│  6. 创建 PR                                                 │
│     GitHub → Compare & pull request → 等待审核               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、后端架构概览

### 2.1 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| Web框架 | FastAPI | 0.124.0 |
| ASGI服务器 | Uvicorn | 0.38.0 |
| ORM | Tortoise-ORM (async) | - |
| 数据库 | MySQL (aiomysql驱动) | - |
| 认证 | python-jose (JWT) + bcrypt | - |
| 数据验证 | Pydantic v2 | 2.12.5 |
| 配置管理 | pydantic-settings | 2.12.0 |
| RPC通信 | gRPC + Protobuf | 1.76.0 |

### 2.2 目录结构

```
Backend/
├── main.py                 # 应用入口，FastAPI实例配置
├── config.py               # 配置管理（Pydantic Settings）
├── database.py             # Tortoise-ORM 数据库配置
├── requirements.txt        # Python依赖
├── .env.example            # 环境变量示例
│
└── app/
    ├── __init__.py
    ├── database_tortoise.py   # Tortoise数据库连接
    │
    ├── models/                # 数据模型层
    │   ├── __init__.py
    │   ├── doctor.py          # 医生模型
    │   ├── user.py            # 用户/患者模型
    │   ├── department.py      # 科室模型
    │   ├── appointment.py     # 预约模型
    │   ├── chat_record.py     # 聊天记录模型
    │   ├── visit_record.py    # 就诊记录模型
    │   └── ai_diagnosis_report.py  # AI诊断报告模型
    │
    ├── routers/               # 路由/控制器层
    │   ├── __init__.py
    │   ├── doctor.py          # 医生路由（注册、登录、患者管理）
    │   ├── user.py            # 用户路由（注册、登录、绑定医生）
    │   └── department.py      # 科室路由（CRUD）
    │
    ├── schemas/               # Pydantic数据验证层
    │   ├── __init__.py
    │   ├── base.py            # 基础响应结构
    │   ├── doctor.py          # 医生相关Schema
    │   ├── user.py            # 用户相关Schema
    │   └── department.py      # 科室相关Schema
    │
    ├── services/              # 业务逻辑服务层
    │   ├── __init__.py
    │   ├── ai_service.py      # AI服务（gRPC调用）
    │   └── grpc_client/       # gRPC客户端
    │       ├── medical_ai.proto        # Protocol Buffers定义
    │       ├── medical_ai_pb2.py       # 生成的PB代码
    │       └── medical_ai_pb2_grpc.py  # 生成的gRPC代码
    │
    └── utils/                 # 工具函数层
        ├── __init__.py        # 统一导出
        ├── auth.py            # 认证工具（JWT、密码加密）
        ├── response.py        # 统一响应格式
        └── file_handler.py    # 文件处理工具
```

### 2.3 数据库模型关系

```
Department (科室)
    ├── 1:N → Doctor (医生)
    │           └── 1:N → User (患者) [responsible_doctor]
    │
User (用户/患者)
    └── N:1 → Doctor (负责医生)
```

---

## 三、环境搭建详细步骤

### 第一步：克隆项目

```bash
git clone https://github.com/Felicity-byte/CareLinkAgent.git
cd CareLinkAgent
```

### 第二步：创建 Backend 分支

```bash
git checkout -b Backend
git push -u origin Backend
```

### 第三步：配置 Python 环境

```bash
# 进入后端目录
cd Backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat

# 安装依赖
pip install -r requirements.txt
```

### 第四步：配置环境变量

```bash
# 复制环境变量示例文件
copy .env.example .env
```

编辑 `.env` 文件，填入实际配置：

```env
# Database (MySQL)
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/medimeow_db
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=medimeow_db

# JWT
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Service
GLM_API_KEY=your-glm-api-key
AI_SERVICE_HOST=127.0.0.1:50051

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Debug
DEBUG=True
```

### 第五步：初始化数据库

```bash
# 确保 MySQL 服务已启动，数据库已创建
# CREATE DATABASE medimeow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 启动后端服务（会自动创建表结构）
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或访问迁移接口
curl http://localhost:8000/migrate
```

---

## 四、后端与 AI 服务连接

### 4.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        系统架构图                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐     HTTP/REST      ┌─────────────────────┐   │
│   │   前端      │ ◄───────────────► │   Backend (FastAPI) │   │
│   │  (Vue.js)   │                    │      :8000          │   │
│   └─────────────┘                    └──────────┬──────────┘   │
│                                                 │              │
│                                                 │ gRPC         │
│                                                 │ :50051       │
│                                                 ▼              │
│                                      ┌─────────────────────┐   │
│                                      │   AI Service        │   │
│                                      │   (Python/gRPC)     │   │
│                                      └──────────┬──────────┘   │
│                                                 │              │
│                                                 │ HTTP API     │
│                                                 ▼              │
│                                      ┌─────────────────────┐   │
│                                      │   智谱 GLM API      │   │
│                                      │   (大语言模型)       │   │
│                                      └─────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 gRPC 通信配置

#### Proto 文件定义 (medical_ai.proto)

```protobuf
syntax = "proto3";
package medical_ai;

// 输入请求
message AnalysisRequest {
  string patient_text_data = 1;  // 病人文本（UTF-8字符串）
  string image_base64 = 2;       // Base64图片（字符串）
  bool stream = 3;               // 是否流式
  string patient_department = 4; // 选择科室
}

// 同步响应（完整报告）
message AnalysisReport {
  string structured_report = 1;  // 结构化报告
  string status = 2;             // 状态（SUCCESS/DEPARTMENT_MISMATCH）
  string message = 3;            // 附加信息
}

// 流式响应
message StreamChunk {
  bytes chunk_data = 1;          // 二进制数据
  bool is_end = 2;               // 结束标记
}

// gRPC服务接口
service MedicalAIService {
  // 非流式（同步）接口 - 推荐使用
  rpc ProcessMedicalAnalysisSync (AnalysisRequest) returns (AnalysisReport);
  
  // 流式接口 - 保留用于特殊场景
  rpc ProcessMedicalAnalysis (AnalysisRequest) returns (stream StreamChunk);
}
```

#### 配置项 (config.py)

```python
class Settings(BaseSettings):
    # AI服务配置
    GLM_API_KEY: str
    AI_SERVICE_HOST: str = "127.0.0.1:50051"
```

### 4.3 AI 服务调用流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI 服务调用流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 前端提交问卷数据                                             │
│     POST /user/questionnaire/submit                             │
│            ↓                                                    │
│  2. 后端接收并验证数据                                           │
│     - 获取问卷内容、用户信息、科室信息                            │
│     - 构造患者文本数据                                           │
│            ↓                                                    │
│  3. 调用 AI 服务 (ai_service.py)                                │
│     - 创建 gRPC 通道                                            │
│     - 发送 AnalysisRequest                                      │
│            ↓                                                    │
│  4. AI 服务处理                                                  │
│     - 调用智谱 GLM API                                          │
│     - 生成结构化报告                                             │
│     - 返回 AnalysisReport                                       │
│            ↓                                                    │
│  5. 后端处理响应                                                 │
│     - 解析 structured_report                                    │
│     - 判断科室是否匹配                                           │
│     - 返回分析结果给前端                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 AI 服务调用代码示例

```python
# app/services/ai_service.py

import grpc
from .grpc_client import medical_ai_pb2 as pb2
from .grpc_client import medical_ai_pb2_grpc as pb2_grpc

class AIService:
    @staticmethod
    def _call_grpc_ai_service(patient_text_data: str, image_base64: str, department_name: str) -> Dict[str, Any]:
        """调用gRPC AI服务"""
        try:
            ai_service_host = os.getenv('AI_SERVICE_HOST', '127.0.0.1:50051')
            
            with grpc.insecure_channel(ai_service_host) as channel:
                stub = pb2_grpc.MedicalAIServiceStub(channel)
                
                request = pb2.AnalysisRequest(
                    patient_text_data=patient_text_data,
                    image_base64=image_base64,
                    stream=False,
                    patient_department=department_name
                )

                # 调用同步接口
                sync_report = stub.ProcessMedicalAnalysisSync(request)
                
                if sync_report.status == "SUCCESS":
                    result_data = json.loads(sync_report.structured_report)
                    return {
                        "is_department": True,
                        "key_info": result_data.get("key_info", {}),
                        "status": "success"
                    }
                    
        except Exception as e:
            # 降级策略
            return AIService._get_fallback_result(department_name)
```

### 4.5 启动 AI 服务

```bash
# 在另一个终端启动 AI 服务
cd GlmAI
python connect/server.py
```

AI 服务启动后会监听 `127.0.0.1:50051`，后端通过 gRPC 连接。

---

## 五、API 接口文档

### 5.1 用户模块 (/user)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /user/register | 患者注册 | 否 |
| POST | /user/login | 患者登录 | 否 |
| POST | /user/bind | 绑定负责医生 | 是 |
| POST | /user/refresh | 刷新Token | 是 |

### 5.2 医生模块 (/doctor)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /doctor/register | 医生注册 | 否 |
| POST | /doctor/login | 医生登录 | 否 |
| GET | /doctor/info | 获取医生信息 | 是 |
| POST | /doctor/patient/register | 注册新患者 | 是 |
| GET | /doctor/patients | 获取患者列表 | 是 |
| POST | /doctor/patient/bind | 绑定患者 | 是 |
| POST | /doctor/refresh | 刷新Token | 是 |

### 5.3 科室模块 (/department)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | /department/list | 获取所有科室 | 否 |
| POST | /department/create | 创建科室 | 是 |

### 5.4 统一响应格式

**成功响应：**
```json
{
    "base": {
        "code": "10000",
        "msg": "success"
    },
    "data": { ... }
}
```

**错误响应：**
```json
{
    "base": {
        "code": "30001",
        "msg": "错误信息"
    }
}
```

### 5.5 错误码规范

| 代码范围 | 类型 |
|----------|------|
| 10000 | 成功 |
| 10001-10099 | 系统通用错误 |
| 30001-30099 | 医生模块错误 |
| 40001-40099 | 用户模块错误 |
| 50001-50099 | 科室模块错误 |

---

## 六、认证流程

### 6.1 登录流程

```
前端发送手机号+密码
    ↓
后端验证密码(bcrypt)
    ↓
生成 Access Token (30分钟) + Refresh Token (7天)
    ↓
返回双Token给前端
```

### 6.2 Token 刷新流程

```
前端携带Refresh Token
    ↓
后端验证Refresh Token有效性
    ↓
生成新的Access Token + Refresh Token
    ↓
返回新的双Token
```

### 6.3 依赖注入链

```python
# 认证依赖
from fastapi.security import HTTPBearer
from app.utils.auth import get_current_user, get_current_doctor

# 使用示例
@router.get("/info")
async def get_info(user: dict = Depends(get_current_user)):
    return {"user_id": user["user_id"]}
```

---

## 七、日常开发流程

### 7.1 启动开发服务器

```bash
# 终端1：启动后端
cd Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 终端2：启动AI服务（如需AI功能）
cd GlmAI
python connect/server.py
```

### 7.2 开发循环

```
┌──────────────────────────────────────────────┐
│              日常开发循环                      │
├──────────────────────────────────────────────┤
│                                              │
│  git checkout Backend     ← 切换分支          │
│         ↓                                   │
│  git pull origin Backend  ← 拉取最新         │
│         ↓                                   │
│  编写/修改代码                               │
│         ↓                                   │
│  测试API接口                                │
│         ↓                                   │
│  git add . → commit → push                  │
│         ↓                                   │
│  GitHub 创建 PR                             │
│         ↓                                   │
│  等待审核合并                               │
│                                              │
└──────────────────────────────────────────────┘
```

### 7.3 提交规范

```bash
# 功能开发
git commit -m "feat: 添加XX接口"

# Bug修复
git commit -m "fix: 修复XX问题"

# 文档更新
git commit -m "docs: 更新XX文档"

# 重构
git commit -m "refactor: 重构XX模块"
```

---

## 八、常见问题

### 8.1 数据库连接失败

```bash
# 检查 MySQL 服务状态
# Windows
net start MySQL80

# 检查数据库是否存在
mysql -u root -p
CREATE DATABASE medimeow_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 8.2 AI 服务连接失败

```bash
# 检查 AI 服务是否启动
netstat -an | findstr 50051

# 启动 AI 服务
cd GlmAI
python connect/server.py
```

### 8.3 端口被占用

```bash
# 查找占用进程
netstat -ano | findstr :8000

# 终止进程
taskkill /PID <PID> /F
```

### 8.4 主干 main 更新了代码

```bash
# 1. 先暂存当前进度
git stash

# 2. 拉取最新代码
git pull origin main

# 3. 恢复进度
git stash pop
```

---

## 九、调试技巧

### 9.1 API 测试

- 使用 FastAPI 自动文档：http://localhost:8000/docs
- 使用 Postman 或 Thunder Client

### 9.2 日志调试

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 9.3 数据库查看

```bash
# 使用 MySQL Workbench 或 Navicat
# 或命令行
mysql -u root -p medimeow_db
```

---

**更新日期**: 2026-04-08
