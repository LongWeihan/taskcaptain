# User Guide

This guide is written for end users who want to run TaskCaptain and use it without reading the code first.

## What the app does

TaskCaptain gives you a local web UI for managing work driven by two roles:

- **Agent**: the supervisor / planner / coordinator
- **Codex**: the implementation executor

The UI intentionally separates:
- **User ↔ Agent**
- **Agent ↔ Codex**
- **Logs**

That separation is the main point of the product.

---

## Start the app

From the repository root:

```bash
./run.sh
```

Then open:

```text
http://127.0.0.1:8765
```

If you need to restart:

```bash
./restart.sh
```

---

## Homepage overview

On the homepage you can:
- create a new task
- create a reusable Agent Profile
- browse existing Agent Profiles
- browse existing tasks
- bulk-delete non-running tasks

---

## Create an Agent Profile

An Agent Profile is a reusable default identity for the supervisory agent.

A profile includes:
- name
- description
- model
- thinking
- soul
- skills

Use profiles when you want a stable agent style across many tasks.

---

## Create a task

Fill in:
- **Task Name**
- **Goal**
- **Workspace Folder**
- **Agent Profile**
- optional Agent overrides
- Codex endpoint / API key / model / thinking
- Codex plan mode / max permission

### Important field meanings

#### Workspace Folder
This is the main writable area for Codex.

#### Agent Profile
This selects the reusable default identity for the Agent.

#### Agent overrides
If you fill these in, the task will override the selected profile for this one task.

#### Codex max permission
This enables the `approve-all` execution mode used by the current implementation.

---

## Run self-test

Before a real run, use **Run Self-Test**.

It checks:
- Agent config exists
- Agent endpoint is reachable
- workspace folder exists
- Codex session can be ensured
- Codex status can be queried
- a real prompt round-trip works

If self-test fails, fix configuration first.

---

## Task page layout

Each task page is split into several sections.

### 1. Configuration Details
Shows:
- task goal
- workspace folder
- effective Agent identity
- Codex configuration

### 2. User ↔ Agent Dialogue
Use this as the human control channel.

### 3. Agent ↔ Codex Dialogue
This is the supervision channel.

### 4. Self-Test Details
Per-check result table.

### 5. Logs
Raw logs remain visible for debugging.

---

## Save current Agent as reusable profile

If you tuned the current task’s Agent identity and want to reuse it later:

1. open the task page
2. use **Save current Agent as reusable profile**
3. give it a name
4. optionally give it a description

Now future tasks can reuse this Agent directly.

---

## Security note

TaskCaptain is designed for trusted local use.
It does not currently include:
- authentication
- user accounts
- permission separation inside the UI

Do not expose it directly to the public internet without adding a reverse proxy and authentication.
