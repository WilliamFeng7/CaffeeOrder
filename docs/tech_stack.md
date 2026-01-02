# 技术选型文档 (Technology Stack Selection)

## 1. 选型背景与目标
*   **用户规模**：校内约 500 人。
*   **并发压力**：高峰期（课间）预计 20 订单/分钟。虽然绝对并发量不高，但需要在极短时间内完成响应，且涉及资金扣减，对**数据一致性**要求高。
*   **平台特性**：
    *   **学生端**：个人 iPad 浏览器（触控交互为主）。
    *   **商户端**：iPad 或 PC 浏览器（实时监控列表）。

## 2. 前端 (Frontend)
### 核心框架: Vue 3 + Vite
*   **理由**：
    *   **轻量高效**：Vite 构建速度极快，适合快速迭代。
    *   **触控友好**：Vue 3 的响应式机制易于构建动态的交互界面（如购物车动画、状态实时刷新）。
    *   **组件化**：由于学生端和管理端UI风格可能不同，但逻辑复用（如API调用、类型定义），组件化开发易于维护。

### UI 样式: Modern CSS (Vanilla + Variables)
*   **理由**：便于深度定制“高端”、“流畅”的 UI 视觉效果，完美适配 iPad 屏幕比例。
*   **交互库**：可能引入 `Framer Motion` (若用 React) 或 Vue 的 `Transition` 做微动画。

## 3. 后端 (Backend)
### 核心框架: Python FastAPI
*   **理由**：
    *   **高性能**：基于 Starlette 和 Pydantic，原生支持异步 (Async/Await)，能轻松处理 WebSockets 和并发请求。
    *   **开发快**：自动生成 Swagger/OpenAPI 文档，便于前后端对接。
    *   **现有资源**：项目已初始化为 FastAPI。

### 实时通信: 客户端轮询 (Client Polling)
*   **机制**：**每秒增量轮询**。
*   **理由**：
    *   **实现简单**：无需维护复杂的 WebSocket 长连接状态，避免断线重连逻辑。
    *   **足够高效**：在 500 人/20 单的规模下，每秒一次的 HTTP 请求对局域网和服务器压力极小。
    *   **增量更新**：API 仅返回“上次查询时间之后”产生的新订单，减少数据传输量。

## 4. 数据库 (Database)
### 数据库: SQLite
*   **理由**：
    *   **轻量级**：单文件存储，备份和部署极其方便 (Copy & Paste)。
    *   **性能足够**：在开启 **WAL (Write-Ahead Logging)** 模式后，SQLite 能够很好地支撑每分钟几十单的并发写入，完全满足校内使用需求。

### ORM (对象关系映射): SQLModel / SQLAlchemy
*   **理由**：SQLModel 是 FastAPI 作者开发，结合了 Pydantic 和 SQLAlchemy 的优点，定义数据模型非常直观。

## 5. 部署与运维 (DevOps)
*   **容器化**: Docker & Docker Compose
    *   保证开发环境与部署环境一致。
*   **服务器**: 校内局域网服务器或云服务器（视学校网络策略而定）。

---

## 6. 总结配置表

| 模块 | 技术栈 | 说明 |
| :--- | :--- | :--- |
| **User Interface** | Vue 3, Vite, CCS3 | 适配 iPad 的响应式网页 |
| **API Server** | Python 3.10+, FastAPI | 异步高并发处理 |
| **Database** | SQLite (Dev) / PostgreSQL (Prod) | 保证资金与订单数据安全 |
| **Real-time** | WebSockets | 订单实时推送 |
| **Auth** | JWT (JSON Web Tokens) + Hashing | 无状态认证，安全性高 |
