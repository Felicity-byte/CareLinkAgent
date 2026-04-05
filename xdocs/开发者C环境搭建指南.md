# 开发者 C 环境搭建与测试指南

**项目名称**: CareLinkAgent - 智能医疗预诊系统\
**仓库地址**: https://github.com/Felicity-byte/CareLinkAgent.git

---

## 一、克隆项目

打开终端，执行：

```bash
git clone https://github.com/Felicity-byte/CareLinkAgent.git
cd CareLinkAgent
```

---

## 二、配置环境

### 1. 安装后端依赖

```bash
cd Backend
pip install -r requirements.txt
cd ..
```

### 2. 安装前端依赖

```bash
cd Frontend
npm install
cd ..
```

### 3. 配置 AI 服务

```bash
cd GlmAI
copy .env.example .env
```

用记事本或 VS Code 打开 `.env` 文件，填入智谱 API 密钥：

```
ZHIPU_API_KEY=你的智谱API密钥
```

---

## 三、创建 Test 分支

```bash
git checkout -b Test
git push -u origin Test
```

---

## 四、开始测试

### 1. 启动 AI 服务

新开一个终端窗口，执行：

```bash
cd D:\Trea\medical systems\CareLinkAgent\GlmAI
python connect/server.py
```

等待看到 `AI服务启动成功!` 表示成功。

### 2. 运行测试

再新开一个终端窗口，执行：

```bash
cd D:\Trea\medical systems\CareLinkAgent\test\Gtests
python test_streaming.py
```

---

## 五、日常更新

每次测试前，先更新到最新代码：

```bash
git checkout Test
git pull origin Test
```

---

## 六、测试提示词汇总

详见 [主要测试流程.md](../test/Gtests/主要测试流程.md)

---

## 七、注意事项

- 测试结果反馈给开发者 A
- 不需要直接推送代码到 main，通过 PR 提交
- 每次测试前先拉取最新代码

---

**更新日期**: 2026-04-05
