# CoffeeOrder 项目 Docker 部署指南

本文档详细解释了如何将本项目（FastAPI 后端 + Vue/Vite 前端）容器化，以及 Docker 运行的核心原理。

---

## 1. Docker 化的核心原理

Docker 的本质是**环境隔离**。在这本项目中，我们将应用拆分为两个主要容器，并使用 Docker Compose 进行编排：

### A. 后端容器 (Backend Service)
- **环境隔离**：后端运行在 `python:3.11-slim` 镜像中。这意味着无论你的电脑是 Mac、Windows 还是 Linux，容器内部的 Python 环境、插件版本（`requirements.txt`）都是完全一致的。
- **工作目录映射**：通过 Docker 的 `volumes` 功能，我们将本地的 `backend/` 文件夹映射到容器内的 `/app` 目录。
  - **原理**：这就像是一个“实时的同步镜像”。你在外面改了代码，容器内部会立刻看到变化（结合 Uvicorn 的 `--reload`，可以实现容器内的热更新）。
- **数据持久化 (SQLite)**：由于 SQLite 是一个文件数据库，如果容器销毁，数据会丢失。因此我们将数据库文件所在的文件夹挂载为 Volume，确保数据保存在宿主机硬盘上。

### B. 前端容器 (Frontend Service)
- **多阶段构建 (Multi-stage Build)**：
  1. **构建阶段**：使用 Node.js 镜像安装依赖并执行 `npm run build`，生成生产环境的静态文件（`dist/`）。
  2. **运行阶段**：丢弃沉重的 Node.js 环境，只将 `dist/` 文件夹拷贝到轻量级的 `Nginx` 镜像中。
- **反向代理**：Nginx 负责把前端页面“喂”给浏览器。

### C. 网络连接 (Networking)
- 在 Docker Compose 内部，容器之间可以通过**服务名**互相访问。
- 例如：前端代码如果需要在服务器端访问后端，可以使用 `http://backend:8000`。
- **注意**：由于我们的前端是 Vue（运行在用户浏览器里），所以前端代码请求后端 API 时，地址通常仍为 `http://localhost:8000`（或服务器的公网 IP）。

---

## 2. 文件夹与 Docker 的对应关系

| 本地文件夹/文件 | Docker 中的角色 | 说明 |
| :--- | :--- | :--- |
| `backend/Dockerfile` | **后端的说明书** | 定义了如何安装 Python 环境、依赖和启动命令。 |
| `frontend/Student/Dockerfile` | **前端的说明书** | 定义了如何打包 Vue 代码并将其放入 Nginx。 |
| `docker-compose.yml` | **指挥官** | 统一管理前后端容器，定义端口映射（如 `80:80`）和启动顺序。 |
| `backend/data/` | **持久化仓库** | 映射为 Volume，存放 SQLite 数据库文件。 |

---

## 3. 如何启动 (Startup Guide)

在安装好 Docker 和 Docker Compose 后，按照以下顺序操作：

### 第一步：检查 API 配置
确保前端项目中的 API 请求地址是动态的或者指向正确的后端地址。

### 第二步：一键启动
在项目根目录下运行：
```bash
docker-compose up --build
```
- `--build` 参数确保每次代码修改（对于没有挂载 Volume 的部分）都能重新生成镜像。
- `-d` 参数（可选）可以在后台运行（`docker-compose up -d`）。

### 第三步：访问系统
- **前端地址**: `http://localhost` (默认 80 端口)
- **后端文档 (Swagger)**: `http://localhost:8000/docs`

---

## 4. 停止与清理

- **停止容器**: `docker-compose stop`
- **停止并移除容器**: `docker-compose down`
- **查看运行日志**: `docker-compose logs -f`

---

## 5. 为什么这样做？ (The Benefits)
1. **一键运行**：新同事入职不需要安装 Python、Node、配置各种环境变量，只要有 Docker，一键就能跑起来。
2. **环境一致性**：彻底解决“在我电脑上能跑，在你那里不行”的问题。
3. **部署简单**：服务器部署时，只需要把代码拉下来跑一下 `docker-compose up` 即可。
