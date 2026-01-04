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
- Python 3.10+
- Node.js 16+

### 后端启动
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
> API: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

### 前端启动
```bash
# 学生端
cd frontend/Student && npm install && npm run dev
# 管理端
cd frontend/Admin && npm install && npm run dev
```
> Student: `http://localhost:5173` | Admin: `http://localhost:5174`

### Docker 一键部署
```bash
docker-compose up --build -d
```

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
├── backend/          # FastAPI 后端
│   ├── app/          # 应用代码
│   └── data/         # SQLite 数据库
├── frontend/         # Vue 3 前端
│   ├── Student/      # 学生端
│   ├── Admin/        # 管理端
│   └── Barista/      # 咖啡师端
├── docs/             # 项目文档
└── docker-compose.yml
```

---

*Happy Coding! ☕*
