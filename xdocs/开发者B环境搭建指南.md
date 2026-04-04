# 开发者B环境搭建指南

---

## 一、安装软件

### 1. Node.js

1. 访问 https://nodejs.org
2. 下载 **LTS版本**（推荐）
3. 双击安装，一路下一步
4. 验证安装：
   ```bash
   node -v
   npm -v
   ```

### 2. Python

1. 访问 https://python.org/downloads/
2. 下载 **Python 3.8+**
3. 安装时勾选 **Add Python to PATH**
4. 验证安装：
   ```bash
   python --version
   pip --version
   ```

### 3. MySQL

1. 访问 https://dev.mysql.com/downloads/mysql/
2. 下载 **MySQL Community Server**
3. 安装时设置root密码（记住这个密码）
4. 验证安装：
   ```bash
   mysql -u root -p
   ```

### 4. Git

1. 访问 https://git-scm.com/downloads
2. 下载并安装
3. 配置用户信息：
   ```bash
   git config --global user.name "你的名字"
   git config --global user.email "你的GitHub邮箱"
   ```

---

## 二、克隆项目

```bash
git clone https://github.com/Felicity-byte/-.git
cd -
```

---

## 三、配置数据库

### 方法一：命令行

```bash
# 登录MySQL
mysql -u root -p
# 输入密码

# 创建数据库
CREATE DATABASE medimeow_db;

# 退出
exit;
```

### 方法二：MySQL Workbench（图形界面）

1. 打开 MySQL Workbench
2. 连接到本地MySQL
3. 执行SQL：
   ```sql
   CREATE DATABASE medimeow_db;
   ```

---

## 四、配置后端

```bash
# 进入Backend目录
cd Backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境配置文件
copy .env.example .env
```

### 编辑 .env 文件

用记事本或VS Code打开 `Backend\.env`，修改：

```env
# Database (MySQL)
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/medimeow_db

# JWT
SECRET_KEY=随便写一串字符
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Upload
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 五、配置前端

```bash
# 进入Frontend目录
cd ..\Frontend

# 安装依赖
npm install
```

---

## 六、启动服务

### 启动后端

```bash
# 在Backend目录
cd ..\Backend
venv\Scripts\activate
uvicorn main:app --reload
```

看到 `Application startup complete` 表示成功。

### 启动前端（新终端）

```bash
# 在Frontend目录
cd Frontend
npm run dev
```

看到 `Local: http://localhost:5173/` 表示成功。

---

## 七、验证

- 后端API文档：http://localhost:8000/docs
- 前端页面：http://localhost:5173

---

## 常见问题

### pip安装慢

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### npm安装慢

```bash
npm install --registry=https://registry.npmmirror.com
```

### MySQL连接失败

1. 确认MySQL服务已启动
2. 确认密码正确
3. 确认数据库 `medimeow_db` 已创建

---

**更新日期**: 2026-04-04
