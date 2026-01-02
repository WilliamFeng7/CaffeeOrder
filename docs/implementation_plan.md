# 项目实施计划与排期 (Implementation Plan)

本计划按开发逻辑顺序排列，旨在快速构建 MVP (Minimum Viable Product)。

## Phase 1: 基础设施与数据层 (Infrastructure & Data)
**目标**: 建立项目骨架，完成数据库模型设计。

- [ ] **Task 1.1: 项目初始化**
    - [ ] 确认 Python 环境 (3.10+)。
    - [ ] 安装依赖: `fastapi`, `uvicorn`, `sqlmodel`, `httpx` (API请求), `pydantic-settings`。
    - [ ] 建立目录结构: `app/models`, `app/api`, `app/core`, `static`。
- [ ] **Task 1.2: 数据库模型 (Models)**
    - [ ] 定义 `User` 表 (无余额)。
    - [ ] 定义 `MenuItem` 表。
    - [ ] 定义 `Order` 和 `OrderItem` 表。
    - [ ] 定义 `Transaction` 表 (含 `external_id`)。
    - [ ] 编写 `create_db.py` 脚本初始化 SQLite 数据库 (开启 WAL 模式)。

## Phase 2: 核心后端逻辑 (Backend Core)
**目标**: 完成鉴权、支付 Mock 和订单接口。

- [ ] **Task 2.1: 模拟外部 API (External Mock)**
    - [ ] 创建 `app/services/external_payment.py`。
    - [ ] 实现 `MockPaymentService`：模拟用户余额查询、扣款成功/失败、退款。
- [ ] **Task 2.2: 认证模块 (Auth)**
    - [ ] 实现 JWT Token 签发 (`/token`)。
    - [ ] 实现 `get_current_user` 依赖注入。
    - [ ] (Seed Data) 初始化测试用的学生账号和咖啡师账号。
- [ ] **Task 2.3: 菜单接口 (Menu)**
    - [ ] `GET /menu`: 获取可用菜单列表。
    - [ ] `POST /menu` (Admin): 上架新咖啡。
- [ ] **Task 2.4: 订单交易流 (Order Flow)**
    - [ ] `POST /orders`:
        1. 接收购物车数据。
        2. 调用 `MockPaymentService.deduct()`。
        3. 成功后写入 DB。
        4. 失败则返回 400。
    - [ ] `POST /orders/{id}/refund` (Barista): 退款逻辑。

## Phase 3: 管理端与轮询 (Admin & Polling)
**目标**: 让咖啡师能看到订单。

- [ ] **Task 3.1: 订单查询接口**
    - [ ] `GET /orders/sync`: 支持 `?since_ts=xxx` 参数，返回增量数据。
    - [ ] `PATCH /orders/{id}/status`: 修改状态 (Making -> Ready -> Completed)。

## Phase 4: 前端开发 (Frontend - Vue3)
**目标**: 简单的 iPad 交互界面。

- [ ] **Task 4.1: 学生端 UI**
    - [ ] 登录页。
    - [ ] 菜单列表 (大图)。
    - [ ] 购物车与结算页。
    - [ ] 订单状态追踪页。
- [ ] **Task 4.2: 咖啡师看板 UI**
    - [ ] 实现 `setInterval` 每秒轮询 `/orders/sync`。
    - [ ] 订单卡片列表展示。
    - [ ] 制作完成/退款交互按钮。

## Phase 5: 测试与交付 (Testing & Delivery)
**目标**: 确保系统稳定。

- [ ] **Task 5.1: 集成测试**
    - [ ] 编写 test case 模拟 10 人并发下单，验证 `Mock` 扣款准确性。
    - [ ] 验证 SQLite WAL 模式下无锁死现象。
- [ ] **Task 5.2: 部署准备**
    - [ ] 编写 `Dockerfile`。
    - [ ] 准备 `start.sh` 启动脚本。

---

## 建议排期 (Estimated Timeline)
*   **Day 1**: Phase 1 & 2 (Mock API, Models, Auth) - *后端核心跑通*
*   **Day 2**: Phase 2 & 3 (Order Logic, Polling API) - *业务逻辑闭环*
*   **Day 3**: Phase 4 (Student Frontend) - *学生能点单*
*   **Day 4**: Phase 4 (Barista Frontend) & Phase 5 - *整体联调*
