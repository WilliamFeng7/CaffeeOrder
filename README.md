# ☕ 校园咖啡点单系统 (CoffeeOrder System)

<p align="center">
  <img src="https://img.shields.io/badge/Go-1.26+-00ADD8?logo=go" alt="Go">
  <img src="https://img.shields.io/badge/Vue-3.4+-green?logo=vue.js" alt="Vue">
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
| **后端** | Go（标准库 net/http）+ SQLite (WAL，纯 Go 驱动 modernc.org/sqlite) |
| **认证** | JWT + bcrypt + 渐进式锁定 |
| **部署** | Docker Compose |

---

## 🚀 快速开始

### 环境要求
- Go 1.26+（macOS：`brew install go`）
- Node.js 16+

### 推荐：一键本地启动

```bash
./run-local.sh            # 后端 + 三个前端（后台运行，日志写到仓库根目录 *.log）
./run-local.sh backend    # 只起后端
./stop-local.sh           # 全部停止
```

> 该脚本会编译 Go 后端（`apps/backend/bin/server`），并在没有数据库时把
> `data/coffee.db` 播种为 `apps/backend/coffee.db`；缺失的表会在后端启动时自动创建。

### 手动启动（等价步骤）

```bash
# 后端（国内网络建议 export GOPROXY=https://goproxy.cn,direct）
cd apps/backend
go run ./cmd/server -addr 127.0.0.1:8000
# 新库创建第一个管理员（密码从提示或 COFFEE_PASSWORD 读取）
go run ./cmd/createuser -username admin -name 店长 -role admin

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
> | 后端 API | http://localhost:8000/api/v1 |
> | 学生端 | http://localhost:5173 |
> | 管理端 | http://localhost:8080 |
> | 咖啡师端 (KDS) | http://localhost:8081 |
>
> 三个前端通过 Vite 代理把 `/api/v1` 与 `/static` 转发到 `127.0.0.1:8000`，
> 所以本地无需配置跨域或绝对图片地址。

### 跑测试

```bash
cd apps/backend
go test ./...            # 含并发下单 / 重复退款等测试
go test -race ./...      # 竞态检测
```

### Docker 一键部署
```bash
docker-compose up --build -d          # 开发编排
docker-compose -f docker-compose.prod.yml up -d --build   # 生产编排
```

> 生产编排现在要求从环境注入密钥：先 `export SECRET_KEY=*** 再执行上面的命令
> （`docker-compose.prod.yml` 里已不再提交明文密钥，缺失时会直接报错而不是用默认值）。

---

## 📚 文档

- [免登录演示部署](deploy/demo/README.md) - 点菜端访客演示与 Ubuntu 5001 端口部署
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
│   ├── backend/            # Go 后端
│   │   ├── cmd/server/          # HTTP 服务入口
│   │   ├── cmd/createuser/      # 创建账号 / 重置密码
│   │   ├── internal/api/        # 路由、鉴权、请求校验与响应格式
│   │   ├── internal/orders/     # 订单规则：库存、扣款、状态流转、退款
│   │   ├── internal/auth/       # bcrypt、密码策略、JWT、登录限流
│   │   ├── internal/store/      # SQLite 连接、表结构、时间与枚举约定
│   │   └── static/              # /static 静态资源（商品图、上传图片）
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

HTTP 层（`internal/api`）只负责解析请求和整形响应；金额、库存、订单状态机和退款
都在 `internal/orders` 里。所有会改钱或库存的写操作都是带条件的 UPDATE（比如
`balance >= 金额`、`status = 旧状态`），用受影响行数判断成败，所以并发下单不会超卖，
同一订单也只会退款一次。接口路径、JSON 字段和错误格式与原 Python 后端保持一致，
三个前端无需改动。

---

*Happy Coding! ☕*
