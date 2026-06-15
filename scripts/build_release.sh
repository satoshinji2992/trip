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

cp "$ROOT_DIR/.gitignore" "$PACKAGE_DIR/.gitignore"
cp "$ROOT_DIR/数据结构课程设计自评表(2026).docx" "$PACKAGE_DIR/" 2>/dev/null || true

cat > "$PACKAGE_DIR/启动说明.md" <<'EOF'
# 个性化旅游系统可运行代码说明

## 1. 后端启动

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

## 2. 前端启动

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

## 3. 数据库

系统自带 SQLite 数据库：

```text
backend/trip.db
```

可直接运行，不需要额外安装数据库服务器。

## 4. 生产部署方式

可选使用：

```bash
cd backend
gunicorn -c ../deploy/gunicorn.conf.py run:app
```

Nginx 配置参考：

```text
deploy/nginx.trip.conf
```

## 5. AIGC 配置

如需使用旅游动画生成，请参考：

```text
backend/.env.example
```

复制为：

```bash
cp backend/.env.example backend/.env
```

然后修改 AIGC 服务地址。
EOF

echo "==> Building zip"
cd "$RELEASE_DIR"
zip -qr "$PACKAGE_NAME.zip" "$PACKAGE_NAME"

echo "==> Done"
echo "Release folder: $PACKAGE_DIR"
echo "Release zip:    $RELEASE_DIR/$PACKAGE_NAME.zip"
