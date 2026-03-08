# Deployment

This document focuses on practical deployment and fast setup for TaskCaptain.

## 1. Local development / local use

### Requirements

- Linux / WSL2 recommended
- Python 3.10+
- `bash`
- `ss`
- `acpx` on PATH or `ACPX_BIN` set explicitly

### Start

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git
cd taskcaptain
chmod +x run.sh restart.sh
./run.sh
```

Open:

```text
http://127.0.0.1:8765
```

---

## 2. Portable configuration

You can configure startup through environment variables.

### Example

```bash
export ACPX_BIN=/absolute/path/to/acpx
export PRODUCTS_UI_DEFAULT_OPENAI_BASE_URL=http://127.0.0.1:8317/v1
export PRODUCTS_UI_PORT=8765
export PRODUCTS_UI_DEFAULT_PRODUCT_FOLDER="$PWD/workspace"
./run.sh
```

### Using `.env`

```bash
cp .env.example .env
set -a
source .env
set +a
./run.sh
```

---

## 3. Recommended quick-start commands for users

### Basic

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git && cd taskcaptain && chmod +x run.sh restart.sh && ./run.sh
```

### Basic with acpx path

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git
cd taskcaptain
export ACPX_BIN=/absolute/path/to/acpx
./run.sh
```

### Basic with custom port

```bash
git clone https://github.com/YOUR_NAME/taskcaptain.git
cd taskcaptain
export PRODUCTS_UI_PORT=8877
./run.sh
```

---

## 4. Running behind a reverse proxy

For non-local usage, put it behind something like:
- Nginx
- Caddy
- Traefik

At minimum, add:
- authentication
- HTTPS
- IP restrictions if possible

The built-in server is a simple Python stdlib server and is intended primarily for trusted environments.
