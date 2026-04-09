# CareLinkAgent 项目启动指南

## 一、拉取最新代码

```bash
# 克隆项目（如果是第一次）
git clone https://github.com/Felicity-byte/CareLinkAgent.git
cd CareLinkAgent

# 拉取最新代码（如果已克隆）
git pull origin main
```

## 二、环境配置

### 2.1 配置后端环境变量

```bash
cd Backend
copy .env.example .env
```

编辑 `Backend/.env` 文件，修改以下配置：

```env
# 数据库配置
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/medimeow_db

# AI服务API密钥（必须配置）
GLM_API_KEY=你的智谱API密钥
GLM_4V_API_KEY=你的智谱4V API密钥

# JWT配置（可保持默认或修改）
SECRET_KEY=your-secret-key-here-change-in-production

# CORS配置（开发环境保持默认）
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 2.2 配置AI服务环境变量

```bash
cd ../GlmAI
copy .env.example .env
```

编辑 `GlmAI/.env` 文件：

```env
GLM_API_KEY=你的智谱API密钥
```

## 三、安装依赖

### 3.1 安装Python依赖

```bash
# 后端依赖
cd Backend
pip install -r requirements.txt

# AI服务依赖
cd ../GlmAI
pip install -r requirements.txt
```

### 3.2 安装前端依赖

```bash
cd ../Frontend
npm install
```

## 四、初始化数据库

登录MySQL，执行以下命令：

```sql
CREATE DATABASE medimeow_db;
```

> 数据库表会在后端首次启动时自动创建，无需手动执行。

## 五、启动开发服务器

**重要：必须按顺序启动三个服务**

### 5.1 启动AI服务（第一个）

```bash
cd GlmAI
python ai.py
```

等待看到类似输出：
```
INFO: Started server at 0.0.0.0:50053
```

### 5.2 启动后端服务（第二个）

新开一个终端窗口：

```bash
cd Backend
python main.py
```

等待看到类似输出：
```
INFO: Uvicorn running on http://0.0.0.0:8000
```

### 5.3 启动前端服务（第三个）

再新开一个终端窗口：

```bash
cd Frontend
npm run dev
```

等待看到类似输出：
```
Local: http://localhost:5173/
```

## 六、验证服务状态

### 检查端口占用

```bash
# AI服务 - 端口50053
netstat -an | findstr 50053

# 后端服务 - 端口8000
netstat -an | findstr 8000

# 前端服务 - 端口5173
netstat -an | findstr 5173
```

### 测试API

```bash
# 测试后端健康检查
curl http://localhost:8000/docs

# 测试AI服务健康检查
curl http://localhost:50054/health
```

## 七、服务访问地址

| 服务 | 地址 |
|------|------|
| 前端应用 | http://localhost:5173 |
| 后端API | http://localhost:8000 |
| API文档 | http://localhost:8000/docs |
| AI服务 | localhost:50053 (gRPC) |

## 八、常见问题解决

### Q1: pip install 失败

```bash
# 清理缓存重新安装
pip cache purge
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

### Q2: 端口被占用

```bash
# 查找占用端口的进程
netstat -ano | findstr :50053
netstat -ano | findstr :8000

# 终止进程（替换PID为实际进程ID）
taskkill /PID <PID> /F
```

### Q3: 数据库连接失败

```bash
# 检查MySQL服务状态
net start mysql

# 测试数据库连接
mysql -u root -p
```

### Q4: 前端npm install失败

```bash
# 清理后重新安装
cd Frontend
rd /s /q node_modules
del package-lock.json
npm install
```

### Q5: AI服务启动失败

检查 `.env` 文件中的 `GLM_API_KEY` 是否正确配置，确保API密钥有效且有余额。

## 九、项目结构

```
CareLinkAgent/
├── Frontend/          # Vue.js 前端项目
│   ├── src/
│   └── package.json
├── Backend/           # FastAPI 后端项目
│   ├── app/
│   ├── config.py
│   ├── main.py
│   └── requirements.txt
├── GlmAI/             # AI 服务 (gRPC)
│   ├── connect/
│   ├── zhipuGLM/
│   ├── ai.py
│   └── requirements.txt
└── README.md          # 本文件
```

## 十、技术栈

| 部分 | 技术 |
|------|------|
| 前端 | Vue.js 3 + Vite + Element Plus |
| 后端 | FastAPI + Tortoise ORM |
| 数据库 | MySQL 8.0 |
| AI服务 | gRPC + 智谱GLM API |
| 嵌入模型 | BGE (sentence-transformers) |
| 向量数据库 | ChromaDB |

## 十一、注意事项

1. **启动顺序**：AI服务 → 后端 → 前端
2. **API密钥**：必须正确配置才能使用AI功能
3. **数据库**：MySQL服务必须正常运行
4. **端口**：确保 50053、8000、5173 端口未被占用
5. **首次启动**：AI服务首次启动需要加载模型，约需10-20秒

---

如有问题，请检查：
- 环境变量是否正确配置
- 依赖是否全部安装成功
- 端口是否被占用
- 网络连接是否正常
