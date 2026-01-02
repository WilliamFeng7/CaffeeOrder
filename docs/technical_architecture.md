# 系统架构与技术参考手册 (System Architecture & Technical Reference)

本文档对应项目的技术层设计，包含架构概览、技术选型、数据库设计、核心模块实现细节及部署指南。

## 1. 架构设计文档 (Architecture Design)

### 1.1 架构总览
系统采用 B/S (Browser/Server) 架构，遵循前后端分离原则。

*   **表现层 (Presentation Layer)**:
    *   **学生端 (Mobile Web)**: 运行于 iPad/手机浏览器，极简触控交互，Vue 3 构建。
    *   **管理端 (Admin Dashboard)**: 运行于 PC/iPad 宽屏，集成了 **KDS (厨房显示系统)** 与 **CMS (内容管理系统)**，Vue 3 构建。
*   **网关层 (Proxy Layer)**:
    *   **Nginx**: Docker 容器内的反向代理，负责静态资源托管 (Frontend `dist`) 和 API 转发 (`/api` -> Backend)。
*   **业务层 (Business Layer)**:
    *   **FastAPI**: Python 异步后端，处理 Auth, Order, Payment 等核心逻辑。
    *   **Uvicorn**: 高性能 ASGI 服务器。
*   **数据层 (Data Layer)**:
    *   **SQLite**: 单文件数据库 (`coffee.db`)，开启 `PRAGMA journal_mode=WAL` 以支持高并发。

### 1.2 部署架构图
```mermaid
graph TD
    Client_Student[学生端 iPad] -->|HTTPS| Nginx
    Client_Admin[咖啡师 Admin] -->|HTTPS| Nginx
    Nginx -->|/assets| StaticFiles[静态资源]
    Nginx -->|/api| Server[FastAPI Container]
    Server -->|SQL| DB[(SQLite + WAL)]
    Server -->|HTTP| ExternalAPI[学校支付网关 (Mock)]
```

---

## 2. 技术选型文档 (Tech Stack)

| 模块 | 技术栈 | 详细说明 |
| :--- | :--- | :--- |
| **前端架构** | **Vue 3 + Vite** | 采用 Composition API `<script setup>` 风格，Vite 实现毫秒级热更。 |
| **UI 框架** | **Tailwind CSS** | 原子化 CSS，配合自定义动画 (`animate-fade-in`, `animate-scale-in`) 实现流畅交互。 |
| **状态管理** | **Pinia** | 轻量级状态管理，用于 `Toast` 全局通知、`Auth` 用户会话维持。 |
| **数据可视化** | **Chart.js** | 用于 Admin Dashboard 的销售趋势图和饼图绘制。 |
| **后端框架** | **Python 3.10+ FastAPI** | 原生支持 `async/await`，处理轮询请求性能极佳；自动生成 OpenAPI 文档。 |
| **ORM** | **SQLModel** | 结合 Pydantic 与 SQLAlchemy，简化数据库定义与校验。 |
| **数据库** | **SQLite** | 零配置，便于交付与迁移。通过 WAL 模式解决锁机制瓶颈。 |
| **安全认证** | **JWT + BCrypt** | 无状态 Token 认证；密码强哈希存储；支持账户锁定策略。 |
| **容器化** | **Docker Compose** | 编排 `frontend` (Nginx) 和 `backend` (Python) 服务及 `volumes` 挂载。 |

---

## 3. 实施细节 (Implementation Details)

### 3.1 核心数据库设计 (Database Schema)
位于 `backend/app/models.py`。

#### A. Order (订单表)
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `order_no` | String | 唯一订单号 (如 202310240001) |
| `status` | Enum | `created` (待制作), `processing` (制作中), `ready` (待取), `completed` (完成), `refunded` (退款) |
| `pickup_code` | String | 取餐码 (如 A101) |
| `total_amount` | Int | 总金额 (单位：分) |
| `items` | Relation | 关联 `OrderItem` 表 |

#### B. OrderItem (订单明细 - 快照模式)
为防止后续修改菜单价格影响历史账单，下单时**必须**存入快照。
*   `price_snap`: 下单时的单价。
*   `item_name`: 下单时的商品名。
*   `spec`: JSON 存储的规格 (如 `{"sugar": "half", "temp": "hot"}`)。

#### C. Transaction (资金流水)
*   `type`: `order` (消费), `deposit` (充值), `refund` (退款)。
*   `balance_after`: 变动后的余额快照，用于财务核对。

### 3.2 关键业务逻辑

#### 1. 订单轮询 (Order Polling)
*   **前端**: `setInterval` 每 2 秒调用一次 `/api/dashboard/stats` 或 `/api/orders`。
*   **后端**: 计算增量数据。Dashboard 接口返回 `funnel` (各状态数量), `trend` (24h走势), `inventory_alerts` (库存告警)。
*   **优势**: 避免了 WebSocket 的连接维护成本，在局域网低延迟环境下体验接近实时。

#### 2. 乐观锁与并发控制
*   下单时，数据库事务中执行：`Check Inventory -> Deduct Inventory -> Create Order`。
*   虽然 SQLite 是单写模型，但在 WAL 模式下读写分离，足以应对校内 20单/分钟 的峰值。

---

## 4. Docker 部署指南 (Deployment)

### 4.1 目录结构映射
为了支持数据持久化和热更新，`docker-compose.yml` 进行了如下映射：

1.  **Backend Volume**: 
    *   `./backend:/app`: 代码实时映射。
    *   `./backend/data/coffee.db`: **关键**，数据库文件必须挂载到宿主机，防止容器重启数据丢失。
2.  **Frontend Volume**: 
    *   构建阶段生成的 `dist` 目录被复制到 Nginx 容器。

### 4.2 启动命令

**一键启动 (推荐)**
```bash
# 在项目根目录下执行
docker-compose up --build -d
```

**查看日志**
```bash
docker-compose logs -f backend
```

**停止服务**
```bash
docker-compose down
```

### 4.3 端口说明
*   **http://localhost**: 学生端/管理端入口 (Nginx 80端口)。
*   **http://localhost:8000/docs**: 后端 API Swagger 文档 (仅供开发调试)。
