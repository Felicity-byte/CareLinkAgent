# 开发者 C 环境搭建与测试指南

**项目名称**: CareLinkAgent - 智能医疗预诊系统\
**仓库地址**: <https://github.com/Felicity-byte/CareLinkAgent.git>

***

## 一、克隆项目

打开终端，执行：

```bash
# 1. 克隆仓库到本地
git clone https://github.com/Felicity-byte/CareLinkAgent.git

# 2. 进入项目目录
cd CareLinkAgent
```

***

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

***

## 三、创建 Test 分支

```bash
# 1. 创建本地 Test 分支
git checkout -b Test

# 2. 推送 Test 分支到远程仓库并跟踪
git push -u origin Test
```

***

## 四、开始测试

### 1. 启动 AI 服务

新开一个终端窗口，执行：

```bash
# 进入AI服务目录
cd D:\Trea\medical systems\CareLinkAgent\GlmAI

# 启动AI服务
python connect/server.py
```

等待看到 `AI服务启动成功!` 表示成功。

### 2. 运行测试

再新开一个终端窗口，执行：

```bash
# 进入测试目录
cd D:\Trea\medical systems\CareLinkAgent\test\Gtests

# 运行测试脚本
python test_streaming.py
```

***

## 五、日常更新

每次测试前，先更新到最新代码：

```bash
# 1. 切换到 Test 分支
git checkout Test

# 2. 拉取远程最新代码
git pull origin Test
```

***

## 六、测试代码管理

### 测试完成，创建 PR

```bash
# 1. 添加所有修改的文件
git add .

# 2. 提交并写上描述
git commit -m "test: 完成XX测试"

# 3. 推送到远程 Test 分支
git push origin Test

# 4. 在GitHub上创建PR，等待开发者A审核
# 1. 打开 https://github.com/Felicity-byte/CareLinkAgent
# 2. 点击 "Compare & pull request"
# 3. 选择 base: main ← head: Test
# 4. 填写描述，点击 "Create pull request"
# 5. 等待开发者A审核
```

<br />

***

## 七、同步与推送

### 推送代码到远程

```bash
# 1. 添加所有修改的文件
git add .

# 2. 提交并写上描述
git commit -m "test: 描述"

# 3. 推送到远程 Test 分支
git push origin Test
```

### 同步远程最新代码

```bash
# 1. 切换到 Test 分支
git checkout Test

# 2. 拉取远程最新代码
git pull origin Test
```

### 创建 PR 合并到 main

```bash
# 1. 确保在 Test 分支且代码已推送
git checkout Test
git push origin Test

# 2. 在GitHub上操作：
#    打开 https://github.com/Felicity-byte/CareLinkAgent
#    点击 "Compare & pull request"
#    选择 base: main ← head: Test
#    填写描述，点击 "Create pull request"

# 3. 等待开发者A审核合并
```

---

## 八、注意事项

| 情况 | 操作 |
| --- | --- |
| 测试完成 | 提交代码 → 推送 → 创建 PR |
| 测试没完成 | 正常提交暂存进度，不需要特殊处理 |
| 测试失败 | 修复后重新提交推送，继续测试 |
| 仅暂存进度 | 提交时加 WIP 标记，push 即可 |

---

**更新日期**: 2026-04-05
