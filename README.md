# TaskCaptain

[English](#english) | [中文](#中文)

---

## English

### The AI captain for autonomous task delivery

**TaskCaptain is an AI execution lead that keeps a task moving until the result is delivered.**

More simply:

**TaskCaptain helps you turn goals into shipped results.**

TaskCaptain is an autonomous execution layer for Codex. Instead of giving you another chat window, it takes ownership of a task, drives the next step, and keeps work moving until the outcome is delivered.

### Slogan

**Run work until it ships.**

---

## What makes TaskCaptain different

### 1. It keeps running, not just replying

TaskCaptain does not stop at suggestions. It keeps the task moving until there is a result.

### 2. It directs Codex step by step

It directs Codex step by step, manages execution flow, and keeps the work on course.

### 3. It keeps moving without supervision

Work keeps running while you sleep, switch context, or leave the keyboard.

---

## What it is

TaskCaptain is built for people who do not want to babysit AI tools.

Give it a goal, and it keeps Codex moving through the work until there is a real outcome — not just a promising draft.

It is not positioned as a “smart assistant” or a generic productivity booster.
It is closer to an execution owner:
- it owns the task
- it drives the next step
- it keeps the flow moving
- it pushes toward delivery

---

## Core product model

TaskCaptain separates the workflow into 3 visible layers:

- **User ↔ Agent** dialogue
- **Agent ↔ Codex** dialogue
- **raw execution logs**

This gives you a system that is easier to inspect, debug, and trust.

Each task gets:
- isolated config
- isolated state
- isolated logs
- a reusable Agent profile
- a Codex execution thread/session

---

## Why teams and builders use it

TaskCaptain is useful when you want:
- task ownership instead of another AI chat tab
- visible supervision over Codex execution
- work that continues while your attention moves elsewhere
- a reusable Agent identity across tasks
- a local, hackable workflow you can actually inspect

---

## Features

- local browser UI
- isolated per-task state
- reusable Agent Profiles
- self-test
- start / continue run
- stop run
- save current Agent identity as reusable profile
- append new instructions mid-task
- bilingual UI (Chinese / English)
- separate dialogue views + raw logs
- no frontend build step

---

## Quick start

### Clone

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git
cd taskcaptain
```

### Start

```bash
./run.sh
```

Open:

```text
http://127.0.0.1:8765
```

### Optional local config

```bash
cp .env.example .env
set -a
source .env
set +a
./run.sh
```

---

## Fast deploy commands

### One-line local start

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git && cd taskcaptain && chmod +x run.sh restart.sh && ./run.sh
```

### With explicit `acpx` path

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git
cd taskcaptain
export ACPX_BIN=/absolute/path/to/acpx
./run.sh
```

### With custom port / endpoint

```bash
export PRODUCTS_UI_PORT=8877
export PRODUCTS_UI_DEFAULT_OPENAI_BASE_URL=http://127.0.0.1:8317/v1
./run.sh
```

---

## Repository layout

```text
taskcaptain/
├── app/
│   └── server.py
├── data/
│   ├── claw-profiles/
│   ├── products/
│   └── trash/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BRAND.md
│   ├── DATA_MODEL.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
├── logs/
├── runs/
├── workspace/
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
├── README.md
├── restart.sh
└── run.sh
```

---

## Brand voice

TaskCaptain should sound:
- calm
- commanding
- outcome-driven

Words it should lean toward:
- run
- drive
- direct
- move
- deliver
- finish
- ship
- own

Words it should avoid:
- magical
- revolutionary
- next-generation
- intelligent assistant
- productivity booster

TaskCaptain should not feel like “a clever helper”.
It should feel like “someone actually responsible for getting the work done”.

---

## More docs

- [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md)
- [docs/BRAND.md](docs/BRAND.md)

---

## License

MIT

---

## 中文

### 自动推进任务直到交付的 AI captain

**TaskCaptain 是一个自动推进任务直到交付结果的 AI 执行负责人。**

更产品化一点地说：

**TaskCaptain 把目标变成持续执行，直到交付结果。**

TaskCaptain 是一层面向 Codex 的自治执行系统。它不是再给你一个聊天窗口，而是接管任务、判断下一步、持续推动执行，直到结果真正交付。

### 品牌口号

**把任务一路推进到交付。**

---

## 它为什么不一样

### 1. 持续执行，不是一次性回答

TaskCaptain 不是给出建议就结束，而是持续推进，直到拿出结果。

### 2. 自动指挥 Codex

它会自动指挥 Codex 分步执行，管理流程，并让任务始终朝交付前进。

### 3. 无人值守也能推进

即使你去忙别的、离开键盘或正在睡觉，任务也会继续推进。

---

## 它是什么

TaskCaptain 适合那些不想一直盯着 AI 工具的人。

你只需要给它一个目标，它就会持续驱动 Codex 把事情往前做，直到出现真正的交付结果，而不是停留在一个“看起来不错的草稿”。

它不应该被理解成“一个更聪明的助手”或“生产力增强器”。
它更像一个真正负责推进执行的人：
- 它接任务
- 它判断下一步
- 它驱动流程继续前进
- 它把事情往交付推

---

## 核心工作方式

TaskCaptain 把流程拆成 3 个可见层：

- **User ↔ Agent** 对话
- **Agent ↔ Codex** 对话
- **原始执行日志**

这样更容易：
- 理解任务是怎么被推进的
- 排查卡点
- 审视 Agent 对 Codex 的指挥
- 建立对执行过程的信任

每个任务都会有：
- 独立配置
- 独立状态
- 独立日志
- 可复用的 Agent Profile
- 对应的 Codex 执行会话

---

## 为什么值得用

如果你想要的是：
- 不是再开一个 AI 聊天页，而是真正有人负责推进
- 能看见 Codex 是怎么被调度的
- 你去处理别的事情时任务还能继续跑
- 一个可跨任务复用的 Agent 身份
- 一个本地、可改、可检查的工作流

那 TaskCaptain 就适合你。

---

## 功能

- 本地浏览器 UI
- 每个任务独立状态
- 可复用 Agent Profiles
- 自检
- Start / Continue Run
- Stop Run
- 把当前 Agent 保存为可复用 Profile
- 任务中途追加新要求
- 中英双语 UI
- 对话视图与原始日志并存
- 无前端构建步骤

---

## 快速开始

### 克隆

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git
cd taskcaptain
```

### 启动

```bash
./run.sh
```

打开：

```text
http://127.0.0.1:8765
```

### 可选：本地配置

```bash
cp .env.example .env
set -a
source .env
set +a
./run.sh
```

---

## 快速部署命令

### 一行启动

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git && cd taskcaptain && chmod +x run.sh restart.sh && ./run.sh
```

### 指定 `acpx` 路径

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git
cd taskcaptain
export ACPX_BIN=/absolute/path/to/acpx
./run.sh
```

### 自定义端口 / endpoint

```bash
export PRODUCTS_UI_PORT=8877
export PRODUCTS_UI_DEFAULT_OPENAI_BASE_URL=http://127.0.0.1:8317/v1
./run.sh
```

---

## 品牌语气

TaskCaptain 的品牌语气应该是：
- 冷静
- 有掌控感
- 结果导向

应该多用的词：
- run
- drive
- direct
- move
- deliver
- finish
- ship
- own

尽量少用的词：
- magical
- revolutionary
- next-generation
- intelligent assistant
- productivity booster

TaskCaptain 不应该像“一个聪明助手”。
它应该像“一个真正负责的人”。

---

## 更多文档

- [docs/USER_GUIDE.md](docs/USER_GUIDE.md)
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md)
- [docs/BRAND.md](docs/BRAND.md)

---

## License

MIT
