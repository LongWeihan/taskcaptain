# Contributing

## Philosophy

Keep TaskCaptain:
- easy to read
- easy to modify
- easy to deploy locally

Prefer simple, explicit code over heavy abstractions.

## Development principles

- keep task state on disk and inspectable
- do not hide supervision flow
- preserve the separation between User ↔ Agent and Agent ↔ Codex
- avoid introducing unnecessary dependencies
- prefer portable paths over machine-specific paths

## Local checks

Before submitting changes, at minimum run:

```bash
python3 -m py_compile app/server.py
./restart.sh
```
