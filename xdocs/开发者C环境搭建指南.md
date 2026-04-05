# 开发者 C 环境搭建与测试指南

**项目名称**: CareLinkAgent - 智能医疗预诊系统\
**仓库地址**: https://github.com/Felicity-byte/CareLinkAgent.git

---

## 一、工作流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    开发者 C 工作流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 克隆项目                                                 │
│     git clone → cd CareLinkAgent                            │
│            ↓                                                │
│  2. 配置环境                                                 │
│     pip install → npm install → 配置.env                    │
│            ↓                                                │
│  3. 创建分支                                                 │
│     git checkout -b Test                                   │
│            ↓                                                │
│  4. 运行测试                                                │
│     启动AI服务 → 运行测试脚本 → 查看结果                     │
│            ↓                                                │
│  5. 提交推送                                                │
│     git add → git commit → git push                        │
│            ↓                                                │
│  6. 创建 PR（可选）                                          │
│     GitHub → Compare & pull request → 等待审核              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

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

### 第三步：创建 Test 分支

```bash
git checkout -b Test
git push -u origin Test
```

### 第四步：运行测试

```bash
# 终端1：启动AI服务
cd GlmAI
python connect/server.py

# 终端2：运行测试
cd test/Gtests
python test_streaming.py
```

### 第五步：提交推送

```bash
git add .
git commit -m "test: 描述"
git push origin Test
```

### 第六步：创建 PR（可选）

```
GitHub 仓库 → Compare & pull request → 选择 main ← Test → Create
```

---

## 三、日常测试流程

```
┌──────────────────────────────────────────────┐
│              日常测试循环                       │
├──────────────────────────────────────────────┤
│                                              │
│  git checkout Test       ← 切换分支           │
│         ↓                                   │
│  git pull origin Test   ← 拉取最新           │
│         ↓                                   │
│  启动AI服务                                  │
│         ↓                                   │
│  运行测试脚本                                │
│         ↓                                   │
│  查看测试结果                                │
│         ↓                                   │
│  git add . → commit → push                  │
│         ↓                                   │
│  GitHub 创建 PR（可选）                      │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 四、测试管理情况表

| 情况 | 操作 | 命令 |
| --- | --- | --- |
| 测试完成 | 添加 → 提交 → 推送 → PR | `git add .` → `commit` → `push` → GitHub |
| 测试未完成 | 正常提交暂存 | `git add .` → `commit` → `push` |
| 测试失败 | 修复后重新测试 | 修复 → `add` → `commit` → `push` |
| 仅暂存进度 | WIP 提交 | `git commit -m "WIP: ..."` → `push` |

---

## 五、注意事项

- 测试结果反馈给开发者 A
- 不需要推送代码到 main，通过 PR 提交
- 每次测试前先拉取最新代码

---

**更新日期**: 2026-04-05
