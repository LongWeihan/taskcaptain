</div>

![TaskCaptain hero](./hero2.png)

<div align="center">
<em>Claw vibes. Codex codes. You sleep.</em>


<a href="https://openclaw.ai/" target="_blank"><img src="./openclaw_logo.png" alt="LongWeihan/taskcaptain | OpenClaw" height="60"/></a>
  
[![GitHub Stars](https://img.shields.io/github/stars/LongWeihan/taskcaptain?style=flat-square&color=DAA520)](https://github.com/LongWeihan/taskcaptain/stargazers)
[![GitHub Watchers](https://img.shields.io/github/watchers/LongWeihan/taskcaptain?style=flat-square)](https://github.com/LongWeihan/taskcaptain/watchers)
[![GitHub Forks](https://img.shields.io/github/forks/LongWeihan/taskcaptain?style=flat-square)](https://github.com/LongWeihan/taskcaptain/network)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/LongWeihan/taskcaptain)

![MIT License](https://img.shields.io/badge/License-MIT-111827?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![macOS Linux](https://img.shields.io/badge/macOS%20%7C%20Linux-Supported-1F2937?style=flat-square)

[中文](./README.md) · [User Guide](./docs/USER_GUIDE.md) · [Deployment](./docs/DEPLOYMENT.md)


</div>

---

## ⚡ Project Overview

**TaskCaptain** is a supervised execution platform powered by OpenClaw. It refactors the subject of "vibe coding": instead of humans manually nudging a chat box, an intelligent agent continuously plans, executes, reviews, and advances tasks within a real workspace. Humans only need to set the goal once. By decoupling user control, Agent supervision, implementation executors, and raw logs into a visible execution chain, TaskCaptain transforms tasks into an autonomous driving experience—**you no longer need to "vibe code"; OpenClaw commands everything autonomously.**

> **You only need to:** Describe what you want to deliver and adjust the direction with natural language at any time.
> **TaskCaptain returns:** A sustainable, supervised execution chain and a complete record of planning, execution, review, and log evidence.

### Our Vision

TaskCaptain aims to push AI coding from "chat-based generation" to "supervised execution." By explicitly defining the boundaries between humans, Supervisor Agents, and Implementation Executors, we overcome the limitations of traditional coding agents in terms of controllability, visibility, and reliability:

* **For Engineering Practice**: We are a developer's local command center, ensuring long-running tasks, process reviews, failure post-mortems, and mid-task changes happen in a transparent closed loop.
* **For the Future of Agents**: We represent an early paradigm of Agent Software Engineering, where agents no longer just answer questions but take real responsibility for software production under human command.

---

## 📸 Screenshots

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

---

## 🏭 Demo Projects

### 1. Local Inventory Procurement Console

**One prompt:**

```text
Build a local inventory procurement management console. Make the UI beautiful. Figure out the rest yourself.

```

<div align="center">
<img src="./交付产品演示.gif" width="800" alt="Project Demo Animation" />
</div>

### 2. Optimizing Softmax Performance

**One prompt:**

```text
Research current SOTA Softmax optimization versions, design a version that outperforms them, run it yourself, and provide a comparison. My PC: 7950x + 128GB + 4060ti 16GB.

```

<div align="center">

#### Median Speedup after `N` Aggregation (Candidate vs. Torch)

| Scenario | N=128 | 256 | 512 | 1024 | 2048 | 4096 |
| --- | --- | --- | --- | --- | --- | --- |
| `fp16 / none` | 0.38x | 0.55x | 0.27x | 1.41x | **2.87x** | 1.02x |
| `bf16 / none` | 0.39x | 0.55x | 0.48x | 1.40x | **2.39x** | 1.03x |
| `fp16 / pad` | 0.78x | 1.13x | 2.00x | 3.07x | **3.72x** | 2.40x |
| `bf16 / pad` | 0.80x | 1.18x | 2.00x | 3.04x | **3.38x** | 2.44x |

</div>

### 3. A-Share Trading Strategy & Backtesting

**One prompt:**

```text
Design an expert-level A-share trading strategy and perform backtesting on real historical data. The annualized return should be high and stable enough for me to actually make money.

```

<div align="center">

<img width="500" height="500" alt="equity" src="https://github.com/user-attachments/assets/93bb2318-cd19-4634-87f6-9b315a3e9ebe" />

#### Strategy vs. Benchmark Performance (2017-2024)

| Dimension | Metric | This Strategy (Expert) | CSI 300 Benchmark |
| --- | --- | --- | --- |
| **Capital** | Initial Investment | 1,000,000 CNY | 1,000,000 CNY |
|  | Final Balance | 2,334,288 CNY | 1,177,331 CNY |
|  | Total Profit | +1,334,288 CNY | +177,331 CNY |
| **Returns** | Annualized Return | 11.63% | 2.14% |
| **Risk** | Max Drawdown | -21.08% | -45.60% |
| **Efficiency** | Sharpe Ratio | 0.79 | 0.11 |

</div>

> **One-click Forum setup with Email Registration**, **llama2.c optimizations**, and more examples are coming soon...

---

## Project Architecture
<div align="center">
<img width="600" height="600" alt="image" src="https://github.com/user-attachments/assets/ef0802d9-46ec-44fb-b293-595c0fc2bd2f" />
</div>

---

## Core Capabilities

### Continuous Advancement, Not One-shot Answers

TaskCaptain processes tasks as a continuous execution flow rather than ending after one round of suggestions.

### Clear Separation of Duties

* **Agent**: Responsible for understanding goals, planning steps, supervising progress, and organizing new requirements.
* **Codex**: Responsible for implementing within the work directory, generating deliverables, and returning execution results.

### Full Visibility & Easy Troubleshooting

The interface maintains three types of data:

* **User ↔ Agent** Control Dialogue
* **Agent ↔ Codex** Execution Dialogue
* **Raw Logs**
This makes it clear why a task continues, fails, or gets stuck.

### Local-First Architecture

Each task has its own:

* Configuration, State, Logs, Agent Profile, and Codex Session.
Status is persisted to disk, making it easy to inspect, backup, migrate, or manually fix.

---

## Quick Start

### 1. Clone the Repo

```bash
git clone https://github.com/LongWeihan/taskcaptain.git
cd taskcaptain

```

### 2. Launch

```bash
chmod +x run.sh restart.sh
./run.sh

```

Default URL: `http://127.0.0.1:8765`

### 3. Optional: Load Local Environment

```bash
cp .env.example .env
# Edit .env as needed
./run.sh

```

---

## Configuration

TaskCaptain uses environment variables for configuration:

* `PRODUCTS_UI_PORT`: Default `8765`
* `PRODUCTS_UI_DEFAULT_OPENAI_BASE_URL`: API endpoint
* `ACPX_BIN`: Path to the `acpx` binary

---

## Directory Structure

```text
taskcaptain/
├── app/             # Server logic
├── data/            # Profiles, products, and state
├── docs/            # Detailed documentation
├── logs/            # Runtime logs
├── runs/            # Active execution sessions
├── workspace/       # Default task output directory
├── run.sh           # Start script
└── restart.sh       # Restart script

```

---

## License

Distributed under the [MIT License](https://www.google.com/search?q=./LICENSE).

## 📄 Acknowledgments

**TaskCaptain is strategically supported and incubated by the Ramen Group!** We sincerely thank Ramen for their technical support!

## 📈 Stats


<a href="https://star-history.com/#LongWeihan/taskcaptain&type=date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=LongWeihan/taskcaptain&type=date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=LongWeihan/taskcaptain&type=date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=LongWeihan/taskcaptain&type=date" />
 </picture>
</a>
