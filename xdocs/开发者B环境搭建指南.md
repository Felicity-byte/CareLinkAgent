# 开发者 B 环境搭建与开发指南

**项目名称**: CareLinkAgent - 智能医疗预诊系统\
**仓库地址**: <https://github.com/Felicity-byte/CareLinkAgent.git>

***

## 一、工作流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    开发者 B 工作流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 克隆项目                                                 │
│     git clone → cd CareLinkAgent                            │
│            ↓                                                │
│  2. 配置环境                                                 │
│     pip install → npm install → 配置.env                    │
│            ↓                                                │
│  3. 创建分支                                                 │
│     git checkout -b Frontend                                │
│            ↓                                                │
│  4. 开发代码                                                 │
│     启动服务 → 编写代码 → 测试                               │
│            ↓                                                │
│  5. 提交推送                                                │
│     git add → git commit → git push                        │
│            ↓                                                │
│  6. 创建 PR                                                 │
│     GitHub → Compare & pull request → 等待审核              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

***

## 二、详细步骤

### 第一步：克隆项目

```bash
git clone https://github.com/Felicity-byte/CareLinkAgent.git
cd CareLinkAgent
```

### 第二步：配置环境

```bash
# 安装后端依赖
cd Backend
pip install -r requirements.txt
cd ..

# 安装前端依赖
cd Frontend
npm install
cd ..

# 配置AI服务
cd GlmAI
copy .env.example .env
# 编辑 .env 填入 ZHIPU_API_KEY
```

### 第三步：创建 Frontend 分支

```bash
git checkout -b Frontend
git push -u origin Frontend
```

### 第四步：开发代码

```bash
# 终端1：启动后端
cd Backend
uvicorn main:app --reload

# 终端2：启动前端
cd Frontend
npm run dev
```

### 第五步：提交推送

```bash
git add .
git commit -m "feat: 描述"
git push origin Frontend
```

### 第六步：创建 PR

```
GitHub 仓库 → Compare & pull request → 选择 main ← Frontend → Create

```

#### 当正在编写，主干main更新了代码

```
# 1. 先暂存当前进度
git stash

# 2. 拉取最新代码
git pull origin main

# 3. 恢复进度
git stash pop
```

## 三、日常开发流程

```
┌──────────────────────────────────────────────┐
│              日常开发循环                      │
├──────────────────────────────────────────────┤
│                                              │
│  git checkout Frontend    ← 切换分支          │
│         ↓                                   │
│  git pull origin Frontend ← 拉取最新         │
│         ↓                                   │
│  编写/修改代码                              │
│         ↓                                   │
│  git add . → commit → push                  │
│         ↓                                   │
│  GitHub 创建 PR                             │
│         ↓                                   │
│  等待审核合并                               │
│         ↓                                   │
│  ← 返回继续开发                             │
│                                              │
└──────────────────────────────────────────────┘
```

***

## 四、代码管理情况表

| 情况    | 操作                | 命令                                       |
| ----- | ----------------- | ---------------------------------------- |
| 功能完成  | 添加 → 提交 → 推送 → PR | `git add .` → `commit` → `push` → GitHub |
| 功能未完成 | 正常提交暂存            | `git add .` → `commit` → `push`          |
| 代码失败  | 修复后重新提交           | `git add .` → `commit` → `push`          |
| 仅暂存进度 | WIP 提交            | `git commit -m "WIP: ..."` → `push`      |

***

**更新日期**: 2026-04-05
