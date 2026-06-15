# 个性化旅游系统

这是数据结构课程设计项目，包含旅游推荐、路线规划、场所查询、旅游日记、美食推荐，以及 AIGC 旅游动画生成。

## 仓库结构

```text
.
├── backend/                 # Flask 后端、SQLite 初始化脚本、核心算法
│   ├── app/
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── routes/          # REST API
│   │   ├── services/        # Dijkstra、Top-K、Trie、全文检索等算法
│   │   └── utils/
│   ├── init_data*.py        # 初始化 202 个景区/校园、道路图、设施、日记等数据
│   ├── real_map_data/       # 真实地图 GeoJSON/Overpass 导入说明
│   ├── run.py               # 后端启动入口
│   └── trip.db              # 本地演示数据库，源码仓库不再跟踪，发布包会包含
├── frontend/                # React + Vite + Ant Design 前端
│   └── src/
│       ├── pages/           # 页面组件
│       └── services/        # API 封装
├── wan2.2_traval_finetuned/                  # Wan 图生视频服务源码，用于 AIGC 旅游动画生成
├── deploy/                  # Gunicorn + Nginx 多 worker 部署配置
├── folder/                  # 课程设计文档、算法说明、部署说明
├── scripts/                 # 本地辅助脚本
└── release/                 # 可运行发布包输出目录，源码仓库不跟踪
```

## 本地启动

### 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

后端默认运行在：

```text
http://localhost:5001
```

### 前端

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

## AIGC 视频生成服务

`wan2.2/` 中放的是视频生成服务代码。主系统通过后端环境变量调用它：

```text
AIGC_BASE_URL=http://10.21.129.82:8000
AIGC_ENDPOINT=/generate
```

配置样例见：

```text
backend/.env.example
```

## 可运行发布包

生成发布包：

```bash
./scripts/build_release.sh
```

输出：

```text
release/trip-runnable/
release/trip-runnable.zip
```

发布包会包含演示数据库和上传文件；源码仓库中这些运行数据不再跟踪。

## Git 管理规则

源码仓库跟踪：

- 后端、前端、视频服务源码
- 初始化脚本
- 文档
- 部署配置
- 打包脚本

源码仓库不跟踪：

- `node_modules/`
- `__pycache__/`
- `frontend/dist/`
- `backend/trip.db`
- `backend/uploads/`
- `backend/whoosh_index/`
- `release/`
- Wan 模型权重、输出视频、示例音视频

如果需要提交可运行材料，请提交 `release/trip-runnable.zip` 到课程平台，而不是提交到 Git。
