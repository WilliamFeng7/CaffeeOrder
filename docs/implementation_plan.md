# 项目实施计划与进度 (Project Implementation Plan)

本文档记录了项目的实施路线图及当前完成状态。

## 4.1 阶段目标与里程碑 (Milestones)

### Phase 1: 基础设施构建 (Infrastructure) - ✅ Completed
*   **目标**: 建立项目骨架，完成数据库模型设计。
*   **完成情况**:
    *   [x] FastAPI 后端脚手架搭建 (`backend/app`).
    *   [x] 数据库模型定义 (`User`, `Order`, `Product`, `Transaction`).
    *   [x] Docker 环境配置 (`Dockerfile`, `docker-compose.yml`).

### Phase 2: 核心后端逻辑 (Backend Core) - ✅ Completed
*   **目标**: 实现业务逻辑闭环，包括 Auth, 订单流, 支付 Mock。
*   **完成情况**:
    *   [x] **JWT 认证**: 实现登录 (`/token`) 与权限控制 (`get_current_active_user`).
    *   [x] **订单系统**: 实现原子化下单流程 (扣库存 -> 扣余额 -> 生成订单).
    *   [x] **支付网关**: 模拟了校内支付接口，支持余额扣减.
    *   [x] **接口文档**: Swagger UI (`/docs`) 自动生成.

### Phase 3: B端管理系统开发 (Admin Dashboard) - ✅ Completed
*   **目标**: 提供给咖啡师和管理员使用的 Web 端。
*   **核心功能实现**:
    *   [x] **Dashboard**: 实时轮询数据，实现漏斗图、趋势图、Top3 热销榜。
    *   [x] **Order Manager**: 订单列表筛选、状态流转、详情查看。
    *   [x] **Product CMS**: 商品 CRUD、图片上传、库存一键管理 (售罄/恢复)。
    *   [x] **User Finance**: 用户充值、余额管理、财务报表导出 CSV。

### Phase 4: C端学生应用开发 (Student App) - ✅ Completed
*   **目标**: 提供给学生使用的 iPad/Mobile 端。
*   **核心功能实现**:
    *   [x] **点单交互**: 响应式菜单布局，适配触摸屏。
    *   [x] **规格选择**: 支持 SKU 级别的规格定制。
    *   [x] **支付流程**: 集成余额校验与扣款反馈。

### Phase 5: 测试与交付 (Testing & Delivery) - 🔄 In Progress
*   **当前重点**:
    *   [ ] **并发测试**: 模拟课间 50 人并发下单，验证数据库 WAL 模式稳定性。
    *   [ ] **UI 细节优化**: 统一 Toast 提示样式，优化 Loading 动画体验。
    *   [ ] **生产环境部署**: 配置 Nginx Gzip 压缩，优化静态资源加载速度。

---

## 4.2 历史实施记录 (Change Log)

*   **2026-01-02**: 
    *   完成 Admin 端 **财务分析 (FinanceView)** 模块，支持流水导出。
    *   优化 **Dashboard** 实时性，增加库存预警功能。
    *   重构文档结构，输出《技术产品白皮书》。
*   **2026-01-01**: 
    *   完成基础下单流程联调。
    *   初始化 Docker 容器化部署方案。

---

## 4.3 后续规划 (Future Roadmap)

*   **v1.1**: 引入 WebSocket 替换轮询，进一步降低服务器负载。
*   **v1.2**: 增加 "限时秒杀" 活动功能。
*   **v1.3**: 对接学校真实一卡通支付接口 (需等待学校信息中心 API 开放)。
