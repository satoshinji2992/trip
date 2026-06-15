# Nginx 多 Worker 部署说明

## 1. 部署目标

开发环境中可以直接使用 Flask 内置服务器和 Vite 开发服务器；生产或答辩讲解时，为了说明系统支持多用户并发，可以采用：

```text
浏览器 -> Nginx 多 worker -> Gunicorn 多 worker -> Flask 后端 -> SQLite
```

其中：

- Nginx 负责静态资源、反向代理、请求转发、上传大小限制。
- Gunicorn 负责启动多个后端 worker，提高并发处理能力。
- Flask 只负责业务接口和算法计算。

## 2. 前端构建

```bash
cd /Users/shenqi/Documents/code/trip/frontend
npm install
npm run build
```

构建产物位于：

```text
frontend/dist
```

Nginx 会直接托管这个目录。

## 3. 后端多 Worker 启动

```bash
cd /Users/shenqi/Documents/code/trip/backend
pip install -r requirements.txt
gunicorn -c ../deploy/gunicorn.conf.py run:app
```

默认监听：

```text
127.0.0.1:5001
```

默认 worker 数：

```text
CPU核数 * 2 + 1
```

也可以手动指定：

```bash
GUNICORN_WORKERS=4 GUNICORN_THREADS=2 gunicorn -c ../deploy/gunicorn.conf.py run:app
```

## 4. Nginx 启动

配置文件：

```text
deploy/nginx.trip.conf
```

本机测试可以使用：

```bash
nginx -c /Users/shenqi/Documents/code/trip/deploy/nginx.trip.conf
```

如果已有 Nginx，可把 `server` 部分合并到系统 Nginx 配置中，并把 `root` 改成实际的 `frontend/dist` 路径。

## 5. Nginx 配置重点

```nginx
worker_processes auto;

events {
    worker_connections 1024;
    multi_accept on;
}
```

含义：

- `worker_processes auto`：根据 CPU 自动开启多个 Nginx worker。
- `worker_connections 1024`：每个 worker 最多处理 1024 个连接。
- `multi_accept on`：worker 可以一次接受多个新连接。

后端 upstream：

```nginx
upstream trip_backend {
    least_conn;
    server 127.0.0.1:5001;
}
```

含义：

- Nginx 将 `/api/` 和 `/uploads/` 转发给 Gunicorn。
- `least_conn` 表示优先转发给连接数较少的后端实例。

## 6. 答辩讲法

可以这样说明：

> 系统开发阶段使用 Flask 和 Vite 方便调试；部署阶段使用 Nginx + Gunicorn。Nginx 开启多 worker 处理静态资源和请求转发，Gunicorn 启动多个 Flask worker 处理后端接口。这样可以同时支持多个用户访问，避免单进程 Flask 开发服务器成为瓶颈。路线规划、推荐排序等计算仍在后端服务层完成，Nginx 主要负责并发连接和反向代理。

## 7. 性能指标说明

| 指标 | 说明 |
| --- | --- |
| 并发连接 | Nginx worker 数 × worker_connections |
| 后端并发 | Gunicorn workers × threads |
| 静态资源性能 | 前端 dist 由 Nginx 直接返回，减少 Flask 压力 |
| 大文件上传 | `client_max_body_size 200m` 支持日记图片和视频结果 |
| 长耗时接口 | `proxy_read_timeout 300s` 支持 AIGC 视频生成等待 |

## 8. 注意事项

- SQLite 适合课程演示和轻量部署；如果真实上线并发写入明显增加，建议换成 PostgreSQL 或 MySQL。
- AIGC 视频生成耗时较长，生产环境可以进一步改成异步任务队列。
- 如果部署到服务器，需要把 `server_name` 改成实际域名，并配置 HTTPS。
