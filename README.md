# ☕ 校园咖啡点单系统 (CoffeeOrder System)

欢迎使用 **校园咖啡点单系统**！这是一个专为校园环境打造的现代化咖啡点单平台，集成了学生下单、咖啡师接单制作以及管理员后台管理的全套功能。

## 🌟 功能概览

本系统分为三个独立的应用端，各司其职：

- **📱 学生端 (Student App)**
  - 浏览精美菜单，查看商品详情。
  - 在线下单支付，支持多种口味定制。
  - 实时查看订单状态（制作中、待取餐）。
  - 查看历史订单记录。

- **👨‍🍳 咖啡师端 (Barista App / KDS)**
  - 实时接收新订单通知。
  - 厨房显示系统 (KDS)：直观管理订单状态 (待处理 -> 制作中 -> 待取餐 -> 已完成)。
  - 高效的出餐流程管理。

- **💻 管理员后台 (Admin Dashboard)**
  - **商品管理**：上架/下架饮品，修改价格和描述。
  - **用户管理**：管理学生和员工账户。
  - **财务统计**：查看销售报表，分析营收数据。
  - **系统设置**：配置系统参数。

- **🔒 安全机制**
  - 完善的角色权限控制 (管理员、咖啡师、普通用户)。
  - 基于 JWT 的安全认证。

---

## 🛠️ 技术栈 (Tech Stack)

本项目采用前后端分离架构，技术选型如下：

### 后端 (Backend)
- **核心框架**: [FastAPI](https://fastapi.tiangolo.com/) (高性能 Python Web 框架)
- **数据库**: SQLite (轻量级，方便部署) + [SQLModel](https://sqlmodel.tiangolo.com/) (ORM)
- **数据库迁移**: [Alembic](https://alembic.sqlalchemy.org/)
- **认证授权**: JWT (JSON Web Tokens)

### 前端 (Frontend)
- **核心框架**: [Vue.js 3](https://vuejs.org/) (组合式 API)
- **构建工具**: [Vite](https://vitejs.dev/) (极速开发体验)
- **UI 样式**: TailwindCSS (部分应用)
- **架构**: 多应用独立工程结构 (Student, Admin, Barista 分离)

---

## 🚀 快速开始 (Getting Started)

请按照以下步骤在本地搭建开发环境。

### 📋 环境要求
- **Python**: 3.9 或更高版本
- **Node.js**: 16 或更高版本
- **包管理器**: npm, yarn 或 pnpm

### 1️⃣ 后端环境配置 (Backend)

1. **进入后端目录**：
   ```bash
   cd backend
   ```

2. **创建虚拟环境** (推荐，以免污染全局环境)：
   ```bash
   python -m venv .venv

   # Windows 用户激活:
   .venv\Scripts\activate

   # macOS / Linux 用户激活:
   source .venv/bin/activate
   ```

3. **安装依赖包**：
   ```bash
   pip install -r requirements.txt
   ```

4. **初始化数据库**：
   ```bash
   alembic upgrade head
   ```

5. **启动后端服务**：
   ```bash
   python main.py
   # 或者使用 uvicorn 命令:
   # uvicorn main:app --reload
   ```
   🎉 后端服务将运行在: `http://localhost:8000`
   📄 接口文档地址: `http://localhost:8000/docs`

### 2️⃣ 前端环境配置 (Frontend)

前端包含三个独立的项目，**需要分别启动**。

#### 🎓 启动学生端 (Student)
打开一个新的终端窗口：
```bash
cd frontend/Student
npm install
npm run dev
```
> 默认访问地址: `http://localhost:5173`

#### 👑 启动管理员端 (Admin)
打开一个新的终端窗口：
```bash
cd frontend/Admin
npm install
npm run dev
```
> 请查看终端输出的端口号 (通常是 `http://localhost:5174` 或类似)

#### ☕ 启动咖啡师端 (Barista)
打开一个新的终端窗口：
```bash
cd frontend/Barista
npm install
npm run dev
```
> 请查看终端输出的端口号

---

## 📚 更多文档

- [API 接口文档](docs/API.md)
- [产品手册](docs/product_manual.md)
- [技术架构说明](docs/technical_architecture.md)

---
*Happy Coding! ☕*
