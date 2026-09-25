# ☕ 校园咖啡点单系统 (CoffeeOrder System)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/Vue-3.4+-green?logo=vue.js" alt="Vue">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-teal?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

专为校园环境打造的现代化咖啡点单平台，支持学生下单、咖啡师 KDS 接单、管理员后台管理。

---

## 🌟 功能概览

| 端 | 功能 |
|----|------|
| **📱 学生端** | 菜单浏览、在线下单、订单追踪、历史查询 |
| **☕ 咖啡师端** | KDS 接单、状态流转、库存管理 |
| **💻 管理端** | 用户/商品/财务管理、数据分析 |

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite + Tailwind CSS + Pinia |
| **后端** | FastAPI + SQLModel + SQLite (WAL) |
| **认证** | JWT + bcrypt + 渐进式锁定 |
| **部署** | Docker Compose |

---

## 🚀 快速开始

### 环境要求
- Python 3.10+（`run-local.sh` 用 [uv](https://docs.astral.sh/uv/) 创建 3.12 虚拟环境）
- Node.js 16+

### 推荐：一键本地启动

```bash
./run-local.sh            # 后端 + 三个前端（后台运行，日志写到仓库根目录 *.log）
./run-local.sh backend    # 只起后端
./stop-local.sh           # 全部停止
```

> 该脚本会自动准备 `apps/backend/.venv`、补齐 `requirements.txt` 缺失的
> `greenlet` / 固定 `bcrypt==4.0.1`，并把 `data/coffee.db` 播种为
> `apps/backend/coffee.db`。

### 手动启动（等价步骤）

```bash
# 后端
cd apps/backend
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -r requirements.txt greenlet "bcrypt==4.0.1"
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 前端（npm workspace，依赖装在仓库根目录）
npm install
npm run dev:student     # 学生端
npm run dev:admin       # 管理端
npm run dev:barista     # 咖啡师端
```

> **端口**（与 `run-local.sh` 一致）
>
> | 服务 | 地址 |
> |------|------|
> | 后端 API | http://localhost:8000 （文档 `/docs`）|
> | 学生端 | http://localhost:5173 |
> | 管理端 | http://localhost:8080 |
> | 咖啡师端 (KDS) | http://localhost:8081 |
>
> 三个前端通过 Vite 代理把 `/api/v1` 与 `/static` 转发到 `127.0.0.1:8000`，
> 所以本地无需配置跨域或绝对图片地址。

### 跑测试

```bash
cd apps/backend
uv pip install --python .venv/bin/python pytest pytest-asyncio
.venv/bin/python -m pytest tests -q
```

> 注意：`pytest` 不在 `requirements.txt` 里（运行时依赖与测试依赖混在一起），
> 需要先按上面单独安装一次。

### Docker 一键部署
```bash
docker-compose up --build -d          # 开发编排
docker-compose -f docker-compose.prod.yml up -d --build   # 生产编排
```

> 生产编排现在要求从环境注入密钥：先 `export SECRET_KEY=*** 再执行上面的命令
> （`docker-compose.prod.yml` 里已不再提交明文密钥，缺失时会直接报错而不是用默认值）。

---

## 📚 文档

- [API 接口文档](docs/API.md) - 完整接口参考
- [技术架构](docs/technical_architecture.md) - 系统设计与 ER 图
- [产品手册](docs/product_manual.md) - 操作指南
- [实施计划](docs/implementation_plan.md) - 项目进度

---

## 🔐 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| Admin | `admin` | `89129885` |
| Student | `student` | `89129885` |
| Barista | `barista` | `89129885` |

> ⚠️ 生产环境请立即修改默认密码！

---

## 📁 项目结构

```
CoffeeOrder/
├── apps/
│   ├── backend/            # FastAPI 后端
│   │   ├── app/
│   │   │   ├── api/endpoints/   # 薄路由层：只做参数解析与响应整形
│   │   │   ├── services/        # 领域层：订单/金额/菜单缓存等业务规则
│   │   │   ├── core/            # 配置、安全、限流、时区
│   │   │   └── models.py / schemas.py
│   │   ├── static/              # /static 静态资源（商品图等）
│   │   └── tests/
│   └── frontend/
│       ├── Student/        # 学生端 (Vue 3 + Vite)
│       ├── Admin/          # 管理端
│       └── Barista/        # 咖啡师端 KDS
├── packages/shared/        # 三端共享：api-client / auth / toast / motion
├── data/                   # 种子数据库
├── run-local.sh            # 本地一键启动
└── docker-compose.yml
```

### 分层约定

路由 (`endpoints/*.py`) 不再直接实现业务规则。金额变动、订单状态机、退款与
菜单缓存都在 `app/services/` 里，这样多条路由共享同一份约束（历史上
`/orders` 与 `/admin/orders` 各自实现了一遍退款逻辑，导致其中一条漏掉了角色校验）。

---

*Happy Coding! ☕*
