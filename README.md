
</div>

![TaskCaptain hero](./hero2.png)

<div align="center"> 
Claw 负责想，Codex 负责写，你负责睡。
</br>
<em>Claw vibes. Codex codes. You sleep.</em>

<a href="https://openclaw.ai/" target="_blank"><img src="./openclaw_logo.png" alt="LongWeihan/taskcaptain | OpenClaw" height="60"/></a>
  
[![GitHub Stars](https://img.shields.io/github/stars/LongWeihan/taskcaptain?style=flat-square&color=DAA520)](https://github.com/LongWeihan/taskcaptain/stargazers)
[![GitHub Watchers](https://img.shields.io/github/watchers/LongWeihan/taskcaptain?style=flat-square)](https://github.com/LongWeihan/taskcaptain/watchers)
[![GitHub Forks](https://img.shields.io/github/forks/LongWeihan/taskcaptain?style=flat-square)](https://github.com/LongWeihan/taskcaptain/network)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/LongWeihan/taskcaptain)

![MIT License](https://img.shields.io/badge/License-MIT-111827?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![macOS Linux](https://img.shields.io/badge/macOS%20%7C%20Linux-Supported-1F2937?style=flat-square)

[English](./README-EN.md) · [用户指南](./docs/USER_GUIDE.md) · [部署说明](./docs/DEPLOYMENT.md)


</div>


⚡ 项目概述
------

**TaskCaptain** 是一个以 OpenClaw 为内核的监督式执行平台。它重构了 vibe coding 的主语：不再是人类对着聊天框一点点提修改，而由智能体在真实工作区中持续规划、执行、审查与推进任务，人类则只需要设定一次目标。通过将用户控制、Agent 监督、执行器落地与原始日志拆分为清晰可见的执行链路，TaskCaptain 让任务变成一场全自动驾驶体验——**你不再需要 vibe coding，OpenClaw 将自主指挥一切**。

> 你只需：描述想要交付什么，并在过程中随时用自然语言修正任务方向</br>
> TaskCaptain 将返回：一条可持续运行的监督式执行链路，以及完整保留规划、执行、审查与日志证据的任务记录

### 我们的愿景

TaskCaptain 致力于把 AI coding 从“聊天式生成”推进到“监督式执行”，通过显式拆分人类、监督 Agent 与实现执行器的职责边界，突破传统 coding agent 在可控性、可见性与可靠性上的局限：
*   **于工程实践**：我们是开发者的本地指挥台，让长任务执行、过程审查、故障复盘与中途变更都能在一个透明闭环中完成
*   **于 agent 未来**：我们是 agent software engineering 的早期范式，智能体不再只是回答问题，而在人的指挥下承担真实的软件生产责任

## 📸 系统截图


<div align="center">
<table>
<tr>
<td><img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/bf3c510a-e9b3-42b4-a2b1-5ecfeb93f3eb" />
</td>
<td><img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/b85480c3-e14e-4b7f-8c2c-23a4049d31fa" />
</td>
</tr>
<tr>
<td><img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/6487019a-620c-4296-b605-bd92668e6c92" />
</td>
<td><img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/d037ee6e-f620-499e-8257-5944249580cc" />
</td>
</tr>
</table>
</div>


## 🏭 演示项目

### 1. 本地库存采购联动台
一句话：
```
做一个本地库存采购联动台。界面精美。其他的自己想
```
<div align="center">
  <img src="./交付产品演示.gif" width="800" alt="项目演示动画" />
</div>

### 2. 优化 softmax 性能
一句话：
```
梳理目前softmax优化版本的sota，设计能超过当前sota的softmax优化版本，你自己运行并给出结果的对比。我的电脑是7950x+128g+4060ti16g
```
<div align="center">

### 按 `N` 聚合后的中位 speedup（candidate vs torch）

|场景|N=128|256|512|1024|2048|4096|
| --- | --- | --- | --- | --- | --- | --- |
|`fp16 / none`|0.38x|0.55x|0.27x|1.41x|**2.87x**|1.02x|
|`bf16 / none`|0.39x|0.55x|0.48x|1.40x|**2.39x**|1.03x|
|`fp16 / pad`|0.78x|1.13x|2.00x|3.07x|**3.72x**|2.40x|
|`bf16 / pad`|0.80x|1.18x|2.00x|3.04x|**3.38x**|2.44x|


</div>

### 2. a股交易策略与回测
一句话：
```
设计一套专家级a股交易策略，并对真实历史数据完成回测。年化收益要够高，也要足够稳健，让我真的能赚到钱
```
<div align="center">

<img width="500" height="500" alt="equity" src="https://github.com/user-attachments/assets/93bb2318-cd19-4634-87f6-9b315a3e9ebe" />


### 策略与基准核心表现对比表（2017-2024）

| 维度 | 指标 | 本策略 (Expert) | 沪深300基准 |
| --- | --- | --- | --- |
| 资金概况 | 初始投入 | 1,000,000 元 | 1,000,000 元 |
|  | 期末总资金 | 2,334,288 元 | 1,177,331 元 |
|  | 累计净赚（利润） | +1,334,288 元 | +177,331 元 |
| 收益能力 | 年化收益率 | 11.63% | 2.14% |
| 风险控制 | 最大回撤 | -21.08% | -45.60% |
| 综合性价比 | 夏普比率 | 0.79 | 0.11 |


</div>

> **一键可邮件注册论坛搭建**、**llama2.c优化**等示例陆续更新中...

## 项目架构
<div align="center">
<img width="600" height="600" alt="image" src="https://github.com/user-attachments/assets/ef0802d9-46ec-44fb-b293-595c0fc2bd2f" />
</div>

## 核心能力

### 持续推进，而不是一次性回答

TaskCaptain 会把任务作为连续执行流来处理，而不是在给出一轮建议后结束。

### Agent 与 Codex 分工清晰

- **Agent**：负责理解目标、规划步骤、监督进度、整理新增要求
- **Codex**：负责在工作目录内执行实现、产出交付物、返回执行结果

### 全程可见、便于排障

界面保留三类信息：

- **User ↔ Agent** 控制对话
- **Agent ↔ Codex** 执行对话
- **原始日志**

这使得任务为什么继续、为什么失败、卡在什么位置，都有迹可查。

### 本地优先，结构清晰

每个任务拥有独立的：

- 配置
- 状态
- 日志
- Agent Profile
- Codex 会话

状态以磁盘文件形式持久化，便于检查、备份、迁移和手工修复。

---

## 适用场景

TaskCaptain 适合以下类型的工作：

- 需要 AI 连续推进，而不是只回答问题
- 需要在后台持续执行的开发或自动化任务
- 需要保留完整过程以便复盘、调试或继续推进的项目
- 需要复用稳定 Agent 身份与配置的多任务工作流
- 需要把“监督者”和“执行者”明确分离的 Codex 工作台

---

## 产品结构

### 首页

首页提供：

- 任务列表
- Agent Profiles 列表
- 创建新任务
- 创建可复用 Profile
- 批量删除非运行中任务

### 任务详情页

任务详情页提供：

- 配置详情
- User ↔ Agent 对话区
- Agent ↔ Codex 对话区
- Self-Test 结果
- Agent 日志
- Codex 日志

### 可复用 Agent Profile

Profile 用于保存 Agent 的默认身份与行为配置，例如：

- model
- thinking
- soul
- skills
- description

任务可继承 Profile，并在单任务范围内进行局部覆盖。

---

## 主要功能

- 本地浏览器 UI
- 每个任务独立状态与日志
- 可复用 Agent Profiles
- Self-Test 自检
- Start / Continue Run
- Stop Run
- 中途追加新要求
- 保存当前 Agent 为可复用 Profile
- 中英双语界面
- 无前端构建步骤

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/LongWeihan/taskcaptain.git
cd taskcaptain
```

### 2. 启动

```bash
chmod +x run.sh restart.sh
./run.sh
```

默认访问地址：

```text
http://127.0.0.1:8765
```

### 3. 可选：加载本地环境配置

```bash
cp .env.example .env
set -a
source .env
set +a
./run.sh
```

---

## 运行要求

- Linux / WSL2 推荐
- Python 3.10+
- `bash`
- `ss`
- `acpx` 已安装，或通过 `ACPX_BIN` 指定路径

---

## 配置项

TaskCaptain 支持通过环境变量调整启动行为。

### 常用环境变量

```bash
export PRODUCTS_UI_HOST=127.0.0.1
export PRODUCTS_UI_PORT=8765
export PRODUCTS_UI_DEFAULT_LANG=zh
export PRODUCTS_UI_DEFAULT_OPENAI_BASE_URL=http://127.0.0.1:8317/v1
export PRODUCTS_UI_DEFAULT_PRODUCT_FOLDER="$PWD/workspace"
export PRODUCTS_UI_PROXY=
export PRODUCTS_UI_NO_PROXY=127.0.0.1,localhost,::1
export ACPX_BIN=/absolute/path/to/acpx
```

### 示例

```bash
export PRODUCTS_UI_PORT=8877
export PRODUCTS_UI_DEFAULT_OPENAI_BASE_URL=http://127.0.0.1:8317/v1
./run.sh
```

更多部署说明见：[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

---

## 运行方式说明

### `run.sh`

- 若端口未占用，则后台启动 TaskCaptain
- 若服务已在运行，则直接提示现有地址和日志位置，不重复拉起

### `restart.sh`

- 停止当前端口上的 TaskCaptain 进程
- 等待端口释放
- 必要时强制结束残留进程
- 清空日志后重新启动

---

## 目录结构

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
├── README-EN.md
├── SECURITY.md
├── hero.png
├── restart.sh
└── run.sh
```

---

## 文档

- [英文 README](./README-EN.md)
- [用户指南](./docs/USER_GUIDE.md)
- [部署说明](./docs/DEPLOYMENT.md)
- [架构说明](./docs/ARCHITECTURE.md)
- [数据模型](./docs/DATA_MODEL.md)
- [贡献指南](./CONTRIBUTING.md)
- [安全策略](./SECURITY.md)

---

## 安全说明

TaskCaptain 当前定位为**可信本地环境中的本地控制台**。

仓库当前不包含：

- 多用户认证
- 权限隔离
- 面向公网暴露的访问控制

如果需要远程访问，请务必在反向代理之后部署，并自行补充：

- 身份认证
- HTTPS
- IP 限制
- 最小权限运行策略

详细建议见：[SECURITY.md](./SECURITY.md)

---

## 开源与规范

- License: [MIT](./LICENSE)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Security: [SECURITY.md](./SECURITY.md)

---

## License

本项目采用 [MIT License](./LICENSE)。

## 📄 致谢

**TaskCaptain 得到了 Ramen 集团的战略支持和孵化！** 我们衷心感谢 Ramen 的技术支持！

## 📈 项目统计

![Star History Light](https://api.star-history.com/svg?repos=LongWeihan/taskcaptain&type=date#gh-light-mode-only)
