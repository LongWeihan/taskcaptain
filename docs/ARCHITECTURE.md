# Architecture

## Overview

TaskCaptain is a lightweight local orchestration layer for task workflows involving three actors:

- **User**
- **Agent**
- **Codex**

The design goal is not just “run a coding agent”, but to make the control flow inspectable.

That is why the UI keeps three distinct surfaces:
- User ↔ Agent dialogue
- Agent ↔ Codex dialogue
- raw logs

---

## Design principles

### 1. Separate supervision from execution

The Agent is the supervisor.
Codex is the implementation executor.

### 2. Persist task state on disk

Each task gets isolated files on disk so the system remains debuggable and hackable.

### 3. Keep the stack light

The current app uses:
- Python stdlib HTTP server
- JSON files for state
- shell scripts for lifecycle
- subprocess execution for Codex calls

---

## Main runtime components

### `app/server.py`

This is the entire web app and supervisor implementation.

It handles:
- HTTP routes
- HTML rendering
- task creation
- profile creation
- self-test
- run / stop lifecycle
- state file I/O
- Codex subprocess orchestration

### `run.sh`

Starts the app in the background and writes logs to `logs/server.log`.

### `restart.sh`

Stops the existing server on the configured port and starts it again.

---

## Data model

### Task

A task stores:
- task metadata
- Agent config
- Codex config
- status
- self-test results
- dialogue state
- logs

### Agent Profile

A profile stores reusable Agent identity defaults:
- model
- thinking
- soul
- skills
- description

Products/tasks inherit from a profile and may override fields locally.
