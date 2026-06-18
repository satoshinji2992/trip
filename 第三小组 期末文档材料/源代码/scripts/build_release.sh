#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RELEASE_DIR="$ROOT_DIR/release"
PACKAGE_NAME="trip-runnable"
PACKAGE_DIR="$RELEASE_DIR/$PACKAGE_NAME"

echo "==> Cleaning old release"
rm -rf "$PACKAGE_DIR" "$RELEASE_DIR/$PACKAGE_NAME.zip"
mkdir -p "$PACKAGE_DIR"

echo "==> Copying backend"
rsync -a \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  --exclude ".env" \
  --exclude "whoosh_index/" \
  "$ROOT_DIR/backend/" "$PACKAGE_DIR/backend/"

echo "==> Copying frontend source"
rsync -a \
  --exclude "node_modules/" \
  --exclude "dist/" \
  --exclude ".vite/" \
  "$ROOT_DIR/frontend/" "$PACKAGE_DIR/frontend/"

echo "==> Copying docs and deploy config"
rsync -a "$ROOT_DIR/folder/" "$PACKAGE_DIR/folder/"
rsync -a "$ROOT_DIR/deploy/" "$PACKAGE_DIR/deploy/" 2>/dev/null || true
if [ -d "$ROOT_DIR/wan2.2_traval_fintuned" ]; then
  echo "==> Copying AIGC video server source"
  rsync -a \
    --exclude ".git/" \
    --exclude "__pycache__/" \
    --exclude "*.pyc" \
    --exclude "models/" \
    --exclude "checkpoints/" \
    --exclude "outputs/" \
    --exclude "logs/" \
    --exclude "datasets/" \
    "$ROOT_DIR/wan2.2_traval_fintuned/" "$PACKAGE_DIR/wan2.2_traval_fintuned/"
fi

cp "$ROOT_DIR/.gitignore" "$PACKAGE_DIR/.gitignore"
cp "$ROOT_DIR/数据结构课程设计自评表(2026).docx" "$PACKAGE_DIR/" 2>/dev/null || true

cat > "$PACKAGE_DIR/setup_and_start.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

choose_python() {
  if [ -n "${PYTHON_BIN:-}" ]; then
    echo "$PYTHON_BIN"
    return
  fi
  for candidate in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return
    fi
  done
  echo python3
}

PYTHON_BIN="$(choose_python)"

echo "==> Checking commands"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "缺少 python3，请先安装 Python 3.9+"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "缺少 npm，请先安装 Node.js 18+"; exit 1; }
echo "使用 Python: $("$PYTHON_BIN" --version 2>&1)"

echo "==> Preparing backend environment"
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  "$PYTHON_BIN" -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "已生成 backend/.env；如需修改视频生成服务器地址，请编辑 AIGC_BASE_URL。"
fi

if [ "${FORCE_INIT_DATA:-0}" = "1" ] || [ ! -f "trip.db" ]; then
  echo "==> Initializing demo database"
  python init_data.py
else
  echo "==> Existing database found: backend/trip.db"
  echo "    如需重建数据，请执行：FORCE_INIT_DATA=1 ./setup_and_start.sh"
fi

echo "==> Preparing frontend environment"
cd "$FRONTEND_DIR"
if [ -f package-lock.json ]; then
  npm install
else
  npm install
fi

cleanup() {
  echo
  echo "==> Stopping services"
  if [ -n "${BACKEND_PID:-}" ]; then kill "$BACKEND_PID" 2>/dev/null || true; fi
  if [ -n "${FRONTEND_PID:-}" ]; then kill "$FRONTEND_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

echo "==> Starting backend: http://localhost:5001"
cd "$BACKEND_DIR"
source venv/bin/activate
python run.py &
BACKEND_PID=$!

echo "==> Starting frontend: http://localhost:3000"
cd "$FRONTEND_DIR"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

cat <<'INFO'

系统正在启动：
- 前端：http://localhost:3000
- 后端：http://localhost:5001

保持这个终端不要关闭。按 Ctrl+C 可同时停止前后端。
INFO

wait "$BACKEND_PID" "$FRONTEND_PID"
EOF
chmod +x "$PACKAGE_DIR/setup_and_start.sh"

cat > "$PACKAGE_DIR/setup_and_start_nginx.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/run"
NGINX_PORT="${NGINX_PORT:-8080}"
BACKEND_INSTANCES="${BACKEND_INSTANCES:-3}"
BACKEND_BASE_PORT="${BACKEND_BASE_PORT:-5001}"
NGINX_CONF="$RUN_DIR/nginx.generated.conf"

choose_python() {
  if [ -n "${PYTHON_BIN:-}" ]; then
    echo "$PYTHON_BIN"
    return
  fi
  for candidate in python3.12 python3.11 python3.10 python3.9 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return
    fi
  done
  echo python3
}

PYTHON_BIN="$(choose_python)"

echo "==> Checking commands"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "缺少 python3，请先安装 Python 3.9+"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "缺少 npm，请先安装 Node.js 18+"; exit 1; }
command -v nginx >/dev/null 2>&1 || { echo "缺少 nginx，请先安装 Nginx。macOS 可用：brew install nginx"; exit 1; }
echo "使用 Python: $("$PYTHON_BIN" --version 2>&1)"

mkdir -p "$RUN_DIR"
if ! [[ "$BACKEND_INSTANCES" =~ ^[0-9]+$ ]] || [ "$BACKEND_INSTANCES" -lt 1 ]; then
  echo "BACKEND_INSTANCES 必须是大于等于 1 的整数"
  exit 1
fi
if ! [[ "$BACKEND_BASE_PORT" =~ ^[0-9]+$ ]]; then
  echo "BACKEND_BASE_PORT 必须是端口数字"
  exit 1
fi

echo "==> Preparing backend environment"
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  "$PYTHON_BIN" -m venv venv
fi
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "已生成 backend/.env；如需修改视频生成服务器地址，请编辑 AIGC_BASE_URL。"
fi

if [ "${FORCE_INIT_DATA:-0}" = "1" ] || [ ! -f "trip.db" ]; then
  echo "==> Initializing demo database"
  python init_data.py
else
  echo "==> Existing database found: backend/trip.db"
  echo "    如需重建数据，请执行：FORCE_INIT_DATA=1 ./setup_and_start_nginx.sh"
fi

echo "==> Building frontend static files"
cd "$FRONTEND_DIR"
npm install
npm run build

UPSTREAM_SERVERS=""
for ((i=0; i<BACKEND_INSTANCES; i++)); do
  port=$((BACKEND_BASE_PORT + i))
  UPSTREAM_SERVERS+="        server 127.0.0.1:$port;\n"
done

cat > "$NGINX_CONF" <<NGINX
worker_processes auto;
pid $RUN_DIR/nginx.pid;
error_log $RUN_DIR/nginx-error.log;

events {
    worker_connections 1024;
    multi_accept on;
}

http {
    default_type application/octet-stream;
    access_log $RUN_DIR/nginx-access.log;

    types {
        text/html html htm;
        text/css css;
        application/javascript js mjs;
        application/json json;
        image/png png;
        image/jpeg jpg jpeg;
        image/gif gif;
        image/svg+xml svg;
        image/x-icon ico;
        video/mp4 mp4;
        application/octet-stream wasm;
    }

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;

    upstream trip_backend {
        least_conn;
$(printf "%b" "$UPSTREAM_SERVERS")
    }

    server {
        listen $NGINX_PORT;
        server_name localhost 127.0.0.1 _;

        root $FRONTEND_DIR/dist;
        index index.html;

        client_max_body_size 200m;

        location /api/ {
            proxy_pass http://trip_backend;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_read_timeout 300s;
            proxy_send_timeout 300s;
        }

        location /uploads/ {
            proxy_pass http://trip_backend;
            proxy_http_version 1.1;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_read_timeout 300s;
        }

        location / {
            try_files \$uri \$uri/ /index.html;
        }
    }
}
NGINX

cleanup() {
  echo
  echo "==> Stopping services"
  nginx -c "$NGINX_CONF" -s stop >/dev/null 2>&1 || true
  for pid in ${GUNICORN_PIDS:-}; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

echo "==> Starting $BACKEND_INSTANCES Gunicorn backend instance(s)"
cd "$BACKEND_DIR"
source venv/bin/activate
GUNICORN_PIDS=""
for ((i=0; i<BACKEND_INSTANCES; i++)); do
  port=$((BACKEND_BASE_PORT + i))
  bind="127.0.0.1:$port"
  echo "    Gunicorn -> $bind"
  FLASK_ENV=production GUNICORN_BIND="$bind" gunicorn -c ../deploy/gunicorn.conf.py run:app &
  GUNICORN_PIDS+="$! "
done

sleep 1
echo "==> Testing Nginx config"
nginx -t -c "$NGINX_CONF"

cat <<INFO

Nginx + Gunicorn 部署已准备：
- 访问地址：http://localhost:$NGINX_PORT
- Nginx 反向代理：/api/ 和 /uploads/ -> $BACKEND_INSTANCES 个 Gunicorn 后端实例
- 后端实例端口：127.0.0.1:$BACKEND_BASE_PORT 起连续 $BACKEND_INSTANCES 个端口
- 前端静态目录：$FRONTEND_DIR/dist
- 生成配置：$NGINX_CONF

保持这个终端不要关闭。按 Ctrl+C 可同时停止 Nginx 和所有 Gunicorn 实例。
INFO

echo "==> Starting Nginx"
nginx -c "$NGINX_CONF" -g "daemon off;"
EOF
chmod +x "$PACKAGE_DIR/setup_and_start_nginx.sh"

cat > "$PACKAGE_DIR/启动说明.md" <<'EOF'
# 个性化旅游系统可运行代码说明

## 1. 推荐：Nginx + Gunicorn 部署启动

解压发布包后，在发布包根目录执行：

```bash
chmod +x setup_and_start_nginx.sh
./setup_and_start_nginx.sh
```

脚本会自动完成：

- 创建后端 Python 虚拟环境 `backend/venv`
- 安装后端依赖 `pip install -r requirements.txt`
- 如果没有 `.env`，自动从 `backend/.env.example` 复制生成
- 如果没有 `backend/trip.db`，自动运行 `python init_data.py` 初始化演示数据
- 执行 `npm install`
- 执行 `npm run build` 生成前端静态资源
- 启动 Gunicorn 后端多 worker
- 生成当前机器路径可用的 Nginx 配置
- 启动 Nginx，反向代理 `/api/` 和 `/uploads/`

默认访问地址：

```text
http://localhost:8080
```

默认端口使用 `8080`，避免普通用户启动 80 端口时需要管理员权限。需要改端口时：

```bash
NGINX_PORT=8081 ./setup_and_start_nginx.sh
```

默认会启动 3 个 Gunicorn 后端实例，端口为 `5001`、`5002`、`5003`，Nginx 使用 `least_conn` 在多个后端实例之间分发请求。需要调整实例数量时：

```bash
BACKEND_INSTANCES=4 BACKEND_BASE_PORT=5001 ./setup_and_start_nginx.sh
```

如需强制重建数据库：

```bash
FORCE_INIT_DATA=1 ./setup_and_start_nginx.sh
```

## 2. 开发模式：一键安装、初始化并启动

解压发布包后，在发布包根目录执行：

```bash
chmod +x setup_and_start.sh
./setup_and_start.sh
```

脚本会自动完成：

- 创建后端 Python 虚拟环境 `backend/venv`
- 安装后端依赖 `pip install -r requirements.txt`
- 如果没有 `.env`，自动从 `backend/.env.example` 复制生成
- 如果没有 `backend/trip.db`，自动运行 `python init_data.py` 初始化演示数据
- 执行 `npm install`
- 使用 Flask 开发服务器和 Vite 开发服务器同时启动后端和前端

默认访问地址：

```text
前端：http://localhost:3000
后端：http://localhost:5001
```

如果需要强制重建数据库：

```bash
FORCE_INIT_DATA=1 ./setup_and_start.sh
```

## 3. 手动后端启动

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

后端默认地址：

```text
http://localhost:5001
```

## 4. 手动前端启动

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：

```text
http://localhost:3000
```

如果 3000 被占用，Vite 会自动切换到 3001。

## 5. 数据库

系统自带 SQLite 数据库：

```text
backend/trip.db
```

可直接运行，不需要额外安装数据库服务器。

如果发布包中没有数据库，或者希望重新生成数据：

```bash
cd backend
python init_data.py
```

## 6. 手动 Nginx + Gunicorn 部署方式

可选使用：

```bash
cd backend
gunicorn -c ../deploy/gunicorn.conf.py run:app
```

再构建前端：

```bash
cd frontend
npm install
npm run build
```

Nginx 配置参考，发布包推荐直接使用 `setup_and_start_nginx.sh` 自动生成配置：

```text
deploy/nginx.trip.conf
```

## 7. AIGC 配置

如需使用旅游动画生成，请参考：

```text
backend/.env.example
```

复制为：

```bash
cp backend/.env.example backend/.env
```

然后修改 AIGC 服务地址。

发布包内包含 `wan2.2_traval_fintuned/` 视频生成服务器源码；模型权重、训练数据和输出目录默认不打进发布包，需要按该目录 README 单独配置。
EOF

echo "==> Building zip"
cd "$RELEASE_DIR"
zip -qr "$PACKAGE_NAME.zip" "$PACKAGE_NAME"

echo "==> Done"
echo "Release folder: $PACKAGE_DIR"
echo "Release zip:    $RELEASE_DIR/$PACKAGE_NAME.zip"
