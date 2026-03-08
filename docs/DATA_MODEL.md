# Data Model

## Task runtime layout

Each task lives under:

- `data/products/<task_id>/config.json`
- `data/products/<task_id>/state.json`
- `data/products/<task_id>/logs/`

Core ideas:
- one task = one isolated workspace configuration
- one task = one Codex session name
- the Agent acts as supervisor and writes structured progress entries
- Codex transcript and supervisor transcript are both persisted for UI rendering

## Main directories

- `data/products/` — live tasks
- `data/trash/` — deleted tasks moved here
- `data/claw-profiles/` — reusable Agent profiles (legacy dir name kept for compatibility)
- `logs/` — server logs
- `runs/` — reserved runtime area
- `workspace/` — default writable folder offered to users for task work

## Task config concepts

A task config contains:
- task id / name / goal
- workspace folder
- Agent settings
- Codex settings

## Task state concepts

A task state contains:
- status
- timestamps
- last run id
- last error
- self-test result block
- legacy conversation history
- structured `conversations.userClaw`
- structured `conversations.clawCodex`
- stop request flag

## Agent profile concepts

An Agent profile is stored as JSON under:

- `data/claw-profiles/<profile_id>.json`

It contains:
- id
- name
- description
- model
- thinking
- soul
- skills
- timestamps
