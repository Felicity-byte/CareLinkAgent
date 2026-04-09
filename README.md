# CareLinkAgent 项目启动指南

## 项目概述
CareLinkAgent 是一个医疗AI问诊系统，包含前端、后端和AI服务三个部分。

## 系统要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+
- Windows/Linux/macOS

## 快速启动步骤

### 1. 克隆项目
```bash
git clone https://github.com/Felicity-byte/CareLinkAgent.git
cd CareLinkAgent
```

### 2. 配置环境变量

#### Backend 配置
```bash
cd Backend
cp .env.example .env
# 编辑 .env 文件，配置以下内容：
# DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/medimeow_db
# GLM_API_KEY=your-glm-api-key-here
# GLM_4V_API_KEY=your-glm-4v-flash-api-key-here
```

#### AI 服务配置
```bash
cd GlmAI
cp .env.example .env
# 编辑 .env 文件，配置以下内容：
# GLM_API_KEY=your_glm_api_key_here
```

### 3. 安装依赖

#### Backend 依赖
```bash
cd Backend
pip install -r requirements.txt
```

#### AI 服务依赖
```bash
cd GlmAI
pip install -r requirements.txt
```

#### Frontend 依赖
```bash
cd Frontend
npm install
```

### 4. 数据库初始化
```sql
-- 创建数据库
CREATE DATABASE medimeow_db;

-- 数据库表会自动创建，无需手动执行
```

### 5. 启动服务

#### 启动 AI 服务 (必须先启动)
```bash
cd GlmAI
python ai.py
# 或
python -m connect.server
```

#### 启动 Backend 服务
```bash
cd Backend
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 启动 Frontend 服务
```bash
cd Frontend
npm run dev
# 或
npm run serve
```

## 服务访问地址
- **前端**: http://localhost:3000 或 http://localhost:5173
- **后端API**: http://localhost:8000
- **AI服务**: localhost:50053 (gRPC)
- **API文档**: http://localhost:8000/docs

## 常见问题解决

### 1. 依赖安装失败
```bash
# 清理缓存重新安装
pip cache purge
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. AI 服务启动失败
- 检查 API 密钥是否正确配置
- 确保端口 50053 未被占用
- 检查网络连接

### 3. 数据库连接失败
- 确保 MySQL 服务正在运行
- 检查数据库用户名和密码
- 确认数据库端口为 3306

### 4. 前端启动失败
```bash
# 清理 node_modules 重新安装
rm -rf node_modules package-lock.json
npm install
```

## 项目结构
```
CareLinkAgent/
├── Frontend/          # Vue.js 前端
├── Backend/           # FastAPI 后端
├── GlmAI/             # AI 服务 (gRPC)
├── test/              # 测试文件
└── README.md          # 本文件
```

## 技术支持
如遇问题，请检查：
1. 所有服务依赖是否安装成功
2. 环境变量是否正确配置
3. 端口是否被占用
4. 网络连接是否正常

## 注意事项
- AI 服务需要有效的智谱 API 密钥
- 首次启动可能需要较长时间（AI模型加载）
- 建议按顺序启动：AI服务 → 后端 → 前端