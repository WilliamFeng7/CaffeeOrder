# 实施细节文档 (Implementation Details)

## 1. 数据库模型设计 (Database Schema)
使用 `SQLModel` 定义表结构，自动兼容 Pydantic 和 SQLAlchemy。

### 1.1 核心表结构
*   **User (用户表)**
    *   `id`: int (PK)
    *   `username`: str (Unique, 学号)
    *   `hashed_password`: str
    *   `role`: str ("student", "barista", "admin")
    *   *(注意：余额字段已移除，实时查询)*
*   **MenuItem (菜单项)**
    *   `id`: int
    *   `name`: str
    *   `price`: int (单位：分)
    *   `category`: str
    *   `image_path`: str (e.g., "/static/latte.jpg")
    *   `is_active`: bool (是否上架)
*   **Order (订单表)**
    *   `id`: int
    *   `user_id`: int (FK)
    *   `status`: str ("created", "processing", "ready", "completed", "refunded")
    *   `total_amount`: int
    *   `pickup_code`: str (e.g., "A-101")
    *   `created_at`: datetime
    *   `updated_at`: datetime (用于增量轮询)
*   **OrderItem (订单明细)**
    *   `id`: int
    *   `order_id`: int
    *   `item_name`: str (快照，防止菜单改名后历史订单变动)
    *   `price_snap`: int (快照价格)
    *   `spec`: str (JSON存储, e.g. `{"temp": "hot", "sugar": "half"}`)
*   **Transaction (本地消费记录)**
    *   `id`: int
    *   `user_id`: int
    *   `external_transaction_id`: str (外部系统返回的流水号)
    *   `amount`: int (负数为消费，正数为退款)
    *   `type`: str ("order", "refund" - **无充值**)
    *   `created_at`: datetime

---

## 2. 核心模块实现 (Module Implementation)

### 2.1 认证模块 (Auth)
*   **算法**: 使用 `OAuth2 with Password Flow` + `JWT`。
*   **接口**:
    *   `POST /token`: 登录获取 Access Token。
    *   `POST /users/me/password`: 修改密码。
*   **安全**: 密码存储使用 `bcrypt` 哈希。

### 2.2 支付网关 (Payment Gateway)
*   **ExternalService 类**:
    *   `async def deduct_balance(student_id, amount) -> str`: 调用外部扣款，返回流水号。
    *   `async def refund(student_id, amount)`: 调用外部退款。
*   **开发环境 Mock**:
    *   设置环境变量 `ENV=DEV` 时，可以直接返回成功，不真实发起 HTTP 请求。
*   **关键代码逻辑**:
    ```python
    # 伪代码
    try:
        # 1. 外部扣款
        ext_id = await external_api.deduct(user.username, order_total)
    except InsufficientBalance:
        return Error("没钱了")
    
    # 2. 本地记账 (如果数据库挂了，需要人工对账或自动冲正退款)
    try:
        with Session(engine) as session:
            session.add(Order(..., external_id=ext_id))
            session.commit()
    except DBError:
        await external_api.refund(user.username, order_total) # 冲正
        return Error("系统故障，已自动退款")
    ```

### 2.3 订单轮询 (Order Polling)
*   **接口**: `GET /orders/sync?last_updated_ts=<timestamp>`
*   **实现逻辑**:
    *   咖啡师端本地维护一个 `last_sync_time`。
    *   每秒调用该接口，发送本地时间戳。
    *   后端查询: `SELECT * FROM order WHERE updated_at > last_updated_ts`。
    *   返回新增或状态变更的订单列表。
    *   若返回列表为空，前端不刷新渲染；否则更新列表并更新 `last_sync_time`。

### 2.4 静态资源 (Static implementation)
*   **方案**: 使用 `FastAPI.mount` 挂载本地 `/static` 目录。
*   **目录结构**:
    ```
    /static
      /images
        /menu_latte.jpg
        /menu_mocha.jpg
    ```
*   **前端访问**: `<img src="/static/images/menu_latte.jpg" />`。

---

## 3. 测试策略 (Testing Strategy)

### 3.1 单元测试 (Unit Testing)
*   **工具**: `pytest`
*   **重点覆盖**:
    *   **余额扣减逻辑**: 测试余额不足、余额刚好、余额充足三种情况。
    *   **价格计算**: 确保后端计算的总价 = 单价 * 数量，防止前端篡改金额。

### 3.2 接口集成测试 (Integration Testing)
*   **工具**: `FastAPI TestClient` (基于 `httpx`)
*   **测试场景**:
    1.  **完整下单流**: 登录 -> 获取Token -> 查询菜单 -> 提交订单 -> 验证余额减少 -> 验证订单生成。
    2.  **并发扣款模拟**:
        *   编写测试脚本，启动 10 个线程同时用同一个账号下单。
        *   **预期结果**: 只有前 N 个订单成功，直到余额不足，数据库中余额不应出现负数。

### 3.3 性能/负载测试 (Load Testing)
*   **工具**: `Locust`
*   **脚本**: 模拟 20 个用户/秒 的并发请求。
*   **验证指标**:
    *   API 平均响应时间 < 200ms。
    *   SQLite 是否出现 `database is locked` 错误 (验证 WAL 模式有效性)。

### 3.4 手动与兼容性测试 (Manual Testing)
*   **设备**: 实体 iPad + Chrome/Safari。
*   **关注点**:
    *   触控点击是否有 300ms 延迟。
    *   软键盘弹出是否遮挡输入框 (如修改密码页)。
