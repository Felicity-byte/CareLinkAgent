# 开发者 B 环境搭建与测试指南

**项目名称**: CareLinkAgent - 智能医疗预诊系统\
**仓库地址**: https://github.com/Felicity-byte/CareLinkAgent.git

---

## 一、克隆项目

打开终端，执行：

```bash
# 1. 克隆仓库到本地
git clone https://github.com/Felicity-byte/CareLinkAgent.git

# 2. 进入项目目录
cd CareLinkAgent
```

---

## 二、配置环境

### 1. 安装后端依赖

```bash
# 进入后端目录
cd Backend

# 安装Python依赖
pip install -r requirements.txt

# 返回项目根目录
cd ..
```

### 2. 安装前端依赖

```bash
# 进入前端目录
cd Frontend

# 安装Node.js依赖
npm install

# 返回项目根目录
cd ..
```

### 3. 配置 AI 服务

```bash
# 进入AI服务目录
cd GlmAI

# 复制环境变量配置文件
copy .env.example .env
```

用记事本或 VS Code 打开 `.env` 文件，填入智谱 API 密钥：

```
ZHIPU_API_KEY=你的智谱API密钥
```

---

## 三、创建 Frontend 分支

```bash
# 1. 创建本地 Frontend 分支
git checkout -b Frontend

# 2. 推送 Frontend 分支到远程仓库并跟踪
git push -u origin Frontend
```

---

## 四、开始开发

### 1. 启动后端服务

新开一个终端窗口，执行：

```bash
# 进入后端目录
cd D:\Trea\medical systems\CareLinkAgent\Backend

# 启动后端服务
uvicorn main:app --reload
```

等待看到 `Application startup complete` 表示成功。

### 2. 启动前端服务

再新开一个终端窗口，执行：

```bash
# 进入前端目录
cd D:\Trea\medical systems\CareLinkAgent\Frontend

# 启动前端服务
npm run dev
```

等待看到 `Local: http://localhost:5173/` 表示成功。

---

## 五、日常更新

每次开发前，先更新到最新代码：

```bash
# 1. 切换到 Frontend 分支
git checkout Frontend

# 2. 拉取远程最新代码
git pull origin Frontend
```

---

## 六、开发代码管理

### 情况一：功能开发完成，创建 PR

```bash
# 1. 添加所有修改的文件
git add .

# 2. 提交并写上描述
git commit -m "feat: 完成XX功能"

# 3. 推送到远程 Frontend 分支
git push origin Frontend

# 4. 在GitHub上创建PR，等待开发者A审核
# 1. 打开 https://github.com/Felicity-byte/CareLinkAgent
# 2. 点击 "Compare & pull request"
# 3. 选择 base: main ← head: Frontend
# 4. 填写描述，点击 "Create pull request"
# 5. 等待开发者A审核
```

### 情况二：功能没完成，需要暂存代码

```bash
# 1. 添加所有修改的文件
git add .

# 2. 提交（说明正在开发中）
git commit -m "feat: 正在进行XX功能开发，暂存"

# 3. 推送到远程 Frontend 分支
git push origin Frontend

# 4. 继续开发...
# 开发完成后，再添加、提交、推送
```

### 情况三：功能开发失败，需要修复后重新开发

```bash
# 1. 修复代码...
# 2. 添加修改
git add .

# 3. 提交
git commit -m "feat: 修复XX问题"

# 4. 推送
git push origin Frontend

# 5. 继续开发
```

### 情况四：不需要创建 PR，仅暂存进度

```bash
# 1. 添加修改
git add .

# 2. 提交（加WIP表示工作进行中）
git commit -m "WIP: 继续开发XX功能"

# 3. 推送（不创建PR，本地进度保存）
git push origin Frontend
```

---

## 七、同步与推送

### 推送代码到远程

```bash
# 1. 添加所有修改的文件
git add .

# 2. 提交并写上描述
git commit -m "feat: 描述"

# 3. 推送到远程 Frontend 分支
git push origin Frontend
```

### 同步远程最新代码

```bash
# 1. 切换到 Frontend 分支
git checkout Frontend

# 2. 拉取远程最新代码
git pull origin Frontend
```

### 创建 PR 合并到 main

```bash
# 1. 确保在 Frontend 分支且代码已推送
git checkout Frontend
git push origin Frontend

# 2. 在GitHub上操作：
#    打开 https://github.com/Felicity-byte/CareLinkAgent
#    点击 "Compare & pull request"
#    选择 base: main ← head: Frontend
#    填写描述，点击 "Create pull request"

# 3. 等待开发者A审核合并
```

---

## 八、注意事项

| 情况 | 操作 |
| --- | --- |
| 功能完成 | 提交代码 → 推送 → 创建 PR |
| 功能没完成 | 正常提交暂存进度，不需要特殊处理 |
| 功能失败 | 修复后重新提交推送，继续开发 |
| 仅暂存进度 | 提交时加 WIP 标记，push 即可 |

---

**更新日期**: 2026-04-05
