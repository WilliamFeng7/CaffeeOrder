# 系统架构与技术参考手册 (System Architecture & Technical Reference)

本文档对应项目的技术层设计，包含架构概览、技术选型、数据库设计、核心模块实现细节及部署指南。

## 1. 架构设计文档 (Architecture Design)

### 1.1 架构总览
系统采用 B/S (Browser/Server) 架构，遵循前后端分离原则。

```mermaid
graph TB
    subgraph "客户端 (Client Layer)"
        Student[📱 学生端<br/>Vue 3 / Mobile]
        Barista[☕ 咖啡师端<br/>Vue 3 / Tablet]
        Admin[💻 管理端<br/>Vue 3 / Desktop]
    end
    
    subgraph "网关层 (Gateway Layer)"
        Nginx[🔀 Nginx<br/>反向代理 + 静态托管]
    end
    
    subgraph "业务层 (Business Layer)"
        FastAPI[⚡ FastAPI<br/>ASGI + Uvicorn]
        Auth[🔐 Auth Module]
        Order[📝 Order Module]
        Finance[💰 Finance Module]
    end
    
    subgraph "数据层 (Data Layer)"
        SQLite[(SQLite + WAL)]
    end
    
    Student --> Nginx
    Barista --> Nginx
    Admin --> Nginx
    Nginx -->|/api/*| FastAPI
    Nginx -->|/static/*| Static[静态资源]
    FastAPI --> Auth
    FastAPI --> Order
    FastAPI --> Finance
    Auth --> SQLite
    Order --> SQLite
    Finance --> SQLite
```

### 1.2 层级职责

| 层级 | 组件 | 职责 |
|-----|------|-----|
| **表现层** | Vue 3 Apps | UI 渲染、用户交互、API 调用 |
| **网关层** | Nginx | SSL 终结、路由分发、静态资源托管、GZIP 压缩 |
| **业务层** | FastAPI | 业务逻辑、认证授权、数据校验 |
| **数据层** | SQLite | 数据持久化、事务管理 |

---

## 2. 技术选型文档 (Tech Stack)

| 模块 | 技术栈 | 版本 | 选型理由 |
|-----|--------|-----|---------|
| **前端框架** | Vue 3 + Vite | 3.4+ | Composition API、毫秒级 HMR |
| **UI 样式** | Tailwind CSS | 3.x | 原子化 CSS、快速开发 |
| **状态管理** | Pinia | 2.x | 轻量、TypeScript 友好 |
| **图表库** | Chart.js | 4.x | 轻量、响应式 |
| **后端框架** | FastAPI | 0.100+ | 异步支持、自动 OpenAPI |
| **ORM** | SQLModel | 0.0.14+ | Pydantic + SQLAlchemy 融合 |
| **数据库** | SQLite | 3.x | 零配置、WAL 模式支持并发 |
| **认证** | JWT + bcrypt | - | 无状态、安全哈希 |
| **容器化** | Docker Compose | 2.x | 一键部署 |

---

## 3. 数据库设计 (Database Schema)

### 3.1 ER 关系图

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER ||--o{ TRANSACTION : has
    ORDER ||--|{ ORDER_ITEM : contains
    MENU_ITEM ||--o{ ORDER_ITEM : references
    
    USER {
        int id PK
        string username UK
        string uuid UK
        string password
        enum role
        int balance
        int failed_login_attempts
        datetime lockout_until
        datetime created_at
    }
    
    ORDER {
        int id PK
        int user_id FK
        string order_no UK
        enum status
        string pickup_code
        int total_amount
        datetime created_at
        datetime updated_at
    }
    
    ORDER_ITEM {
        int id PK
        int order_id FK
        int menu_item_id
        string item_name
        int price_snap
        string spec
        int quantity
    }
    
    MENU_ITEM {
        int id PK
        string name
        string name_cn
        int price
        string category
        int inventory_count
        bool is_active
    }
    
    TRANSACTION {
        int id PK
        int user_id FK
        int order_id
        string external_transaction_id UK
        int amount
        int balance_after
        string type
        datetime created_at
    }
```

### 3.2 核心表说明

#### User (用户表)
- **安全字段**: `failed_login_attempts`, `lockout_until` 实现渐进式锁定
- **余额**: 以"分"为单位存储，避免浮点精度问题
- **角色**: `student` | `barista` | `admin`

#### Order (订单表)
- **状态机**: `created` → `processing` → `ready` → `completed`
- **索引优化**: 复合索引 `(status, created_at)` 加速 KDS 查询
- **取餐码**: 每日重置的流水号

#### OrderItem (订单明细 - 快照模式)
- **价格快照**: `price_snap` 防止菜单变更影响历史账单
- **规格存储**: JSON 格式 `{"sugar": "half", "temp": "ice"}`

#### Transaction (资金流水)
- **类型**: `order` (消费)、`deposit` (充值)、`refund` (退款)
- **余额快照**: `balance_after` 便于财务核对

---

## 4. 核心业务流程 (Business Logic)

### 4.1 订单创建流程

```mermaid
sequenceDiagram
    participant S as Student App
    participant API as FastAPI
    participant DB as SQLite
    
    S->>API: POST /orders (items)
    API->>DB: BEGIN TRANSACTION
    
    rect rgb(240, 248, 255)
        Note over API,DB: 原子操作区域
        API->>DB: 1. 校验商品库存
        API->>DB: 2. 校验用户余额
        API->>DB: 3. 扣减库存
        API->>DB: 4. 扣减余额
        API->>DB: 5. 创建 Order
        API->>DB: 6. 创建 OrderItems
        API->>DB: 7. 创建 Transaction
    end
    
    API->>DB: COMMIT
    API-->>S: 201 Created (order_no, pickup_code)
```

### 4.2 认证与锁定流程

```mermaid
stateDiagram-v2
    [*] --> 检查IP限流
    检查IP限流 --> 查询用户: 通过
    检查IP限流 --> 返回429: 超限
    
    查询用户 --> 检查锁定状态: 用户存在
    查询用户 --> 返回400: 用户不存在
    
    检查锁定状态 --> 验证密码: 未锁定
    检查锁定状态 --> 返回403: 已锁定
    
    验证密码 --> 登录成功: 密码正确
    验证密码 --> 累计失败次数: 密码错误
    
    累计失败次数 --> 判断是否锁定
    判断是否锁定 --> 返回400: 未达阈值
    判断是否锁定 --> 设置锁定时间: 达到阈值
    设置锁定时间 --> 返回403
    
    登录成功 --> 重置失败计数
    重置失败计数 --> 返回Token
    返回Token --> [*]
```

### 4.3 订单状态流转

```mermaid
stateDiagram-v2
    [*] --> created: 下单成功
    created --> processing: 咖啡师开始制作
    created --> refunded: 用户取消
    processing --> ready: 制作完成
    ready --> completed: 用户取餐
    completed --> [*]
    refunded --> [*]
```

---

## 5. API 路由组织

```
/api/v1
├── /login
│   └── POST /access-token     # 登录
├── /users
│   ├── GET  /me               # 获取当前用户
│   ├── PUT  /me               # 更新个人信息
│   └── PUT  /me/password      # 修改密码
├── /menu
│   └── GET  /                 # 获取菜单
├── /orders
│   ├── POST /                 # 创建订单
│   ├── GET  /history          # 订单历史
│   ├── POST /{id}/cancel      # 取消订单
│   ├── POST /{id}/complete    # 完成订单
│   ├── GET  /sync             # KDS 增量同步
│   └── PUT  /{id}/status      # 更新状态
├── /admin
│   ├── GET  /stats            # Dashboard 数据
│   ├── CRUD /users            # 用户管理
│   ├── CRUD /products         # 商品管理
│   └── CRUD /orders           # 订单管理
├── /finance
│   ├── GET  /stats            # 财务概览
│   ├── GET  /chart            # 图表数据
│   └── GET  /transactions     # 交易流水
└── /settings
    ├── GET  /                 # 获取设置
    └── PUT  /{key}            # 更新设置
```

---

## 6. Docker 部署指南 (Deployment)

### 6.1 目录结构

```bash
CoffeeOrder/
├── backend/
│   ├── app/               # FastAPI 应用
│   ├── data/              # 数据目录 (挂载点)
│   │   └── coffee.db      # SQLite 数据库
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── Student/           # 学生端
│   ├── Admin/             # 管理端
│   └── Barista/           # 咖啡师端
├── docker-compose.yml
└── .env                   # 环境变量
```

### 6.2 环境变量 (.env)

```bash
# 安全配置 (生产环境必须修改!)
SECRET_KEY=your-super-secret-key-change-in-production

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./data/coffee.db

# Token 配置
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 6.3 常用命令

```bash
# 一键启动
docker-compose up --build -d

# 查看日志
docker-compose logs -f backend

# 进入容器
docker-compose exec backend bash

# 数据库迁移
docker-compose exec backend alembic upgrade head

# 停止服务
docker-compose down
```

### 6.4 端口映射

| 端口 | 服务 | 用途 |
|-----|------|-----|
| `80` | Nginx | 生产入口 |
| `8000` | FastAPI | API + Swagger (/docs) |
| `5173` | Vite (Dev) | Student 开发服务器 |
| `5174` | Vite (Dev) | Admin 开发服务器 |
| `5175` | Vite (Dev) | Barista 开发服务器 |

---

## 7. 性能优化策略

### 7.1 数据库优化
- **WAL 模式**: 读写分离，提升并发性能
- **复合索引**: `(status, created_at)` 加速 KDS 查询
- **连接池**: SQLAlchemy async 连接池

### 7.2 前端优化
- **轮询策略**: 2秒间隔，局域网低延迟
- **Vite 构建**: Tree-shaking + 代码分割
- **静态压缩**: Nginx GZIP

### 7.3 未来规划
- WebSocket 替代轮询 (v1.1)
- Redis 缓存热点数据 (v1.2)
- PostgreSQL 迁移 (生产规模化)
