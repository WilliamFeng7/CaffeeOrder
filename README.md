# OTIA Café

学校咖啡厅的 App 点单与录单系统。

- 学生端：钉钉免登或学号密码登录，浏览菜单、下单、学生卡付款、查看制作与取餐进度。
- 咖啡师端：按顺序录单，把现有收银系统的收银单号回填到 App 订单。
- 管理端：菜单、规格、营业设置、订单、统计、账号与角色。
- 后端：精简版 Yudao Java 单体，Spring Boot 3 / Java 17 / MySQL / Redis。

## 当前测试环境

| 服务 | 地址 |
| --- | --- |
| 学生端 | `http://150.158.121.81:5001` |
| 咖啡师端 | `http://150.158.121.81:5002` |
| 管理端 | `http://150.158.121.81:5003` |

这是 **dev + mock 学生卡** 测试环境。公开地址目前只有 HTTP，不能输入真实密码；学生卡余额会在后端容器重建后重置。正式使用前必须配置可信 HTTPS，并接入学校真实学生卡接口。完整检查项见 [安全说明](docs/security.md)。

## 本地运行

需要 JDK 17 或 21、Maven 3.9+、Node.js 20.19+、pnpm 10+ 和 Docker Compose。推荐 JDK 21，并确保 `mvn -v` 与 `JAVA_HOME` 指向同一版本。

首次启动前必须设置至少 8 位、同时包含字母和数字的管理员初始密码。数据库里不会保留公开默认密码：

```bash
export OTIA_ADMIN_INITIAL_PASSWORD='replace-with-8-plus-letters-and-digits'
export OTIA_STUDENT_INITIAL_NO='student'
export OTIA_STUDENT_INITIAL_NAME='测试学生'
export OTIA_STUDENT_INITIAL_PASSWORD='replace-with-8-plus-letters-and-digits'

docker compose up -d
docker compose ps

cd apps/backend
mvn clean package -DskipTests
java -jar yudao-server/target/yudao-server.jar --spring.profiles.active=dev
```

三个 `OTIA_STUDENT_INITIAL_*` 变量用于创建可选的一次性测试学生；不创建测试学生时可以留空。

启动前端：

```bash
npm install
npm run dev:student    # http://127.0.0.1:5173
npm run dev:barista    # http://127.0.0.1:8081
pnpm --dir apps/admin install --frozen-lockfile
pnpm --dir apps/admin dev   # http://127.0.0.1:8080
```

也可以运行 `./run-local.sh` 同时启动后端和管理端，用 `./stop-local.sh` 停止。脚本要求预先设置 `OTIA_ADMIN_INITIAL_PASSWORD`，日志写入 `.local-run/`。

## 配置

| 变量 | 说明 |
| --- | --- |
| `MYSQL_HOST` / `MYSQL_PORT` / `MYSQL_DATABASE` | 默认 `127.0.0.1` / `3306` / `otia_cafe` |
| `MYSQL_USER` / `MYSQL_PASSWORD` | 本地 Compose 默认 `otia` / `otia_local` |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | Redis 连接参数 |
| `OTIA_ADMIN_INITIAL_PASSWORD` | 首次管理员密码，至少 8 位且同时包含字母和数字，必填 |
| `OTIA_STUDENT_INITIAL_*` | 可选一次性测试学生账号 |
| `OTIA_DEV_LOGIN_SECRET` | 远程测试栈开发直登密钥，至少 32 个随机字符 |
| `YUDUO_WEB_CORS_ALLOWED_ORIGINS` | 允许访问 API 的三个前端来源，使用逗号分隔的完整 Origin |
| `DINGTALK_CORP_ID` | 学校钉钉企业 corpId |
| `DINGTALK_APP_KEY` / `DINGTALK_APP_SECRET` | 钉钉 H5 应用服务端凭证 |
| `DINGTALK_STUDENT_NO_FIELD` | 学号所在用户字段，默认 `job_number` |
| `cafe.card.mock-enabled` | 仅 `dev` 可开启；没有真实学生卡实现时生产启动失败 |
| `cafe.card.default-balance` | mock 初始余额，单位分 |
| `cafe.order.max-cups` | 每单杯数上限 |
| `cafe.order.payment-timeout-seconds` | 支付结果不确定时的补偿超时 |

跨域默认关闭，只接受同源代理请求。需要额外来源时显式配置 `yudao.web.cors.allowed-origins`，不要使用通配来源。

## 验证

```bash
# 后端全量测试
cd apps/backend
export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
mvn -v                         # 确认 Maven 也运行在 JDK 21
mvn clean verify

# 学生端
cd ../frontend/Student
npm run build
npm run test:checkout
npx vue-tsc --noEmit -p tsconfig.json

# 咖啡师端
cd ../Barista
npm run build

# 管理端
cd ../../admin
pnpm run build
pnpm run typecheck

# dev/mock 接口验收
cd ../..
python3 scripts/smoke-cafe.py

# 前端依赖漏洞审计
npm audit --omit=dev --registry=https://registry.npmjs.org
pnpm --dir apps/admin audit --prod --registry=https://registry.npmjs.org
```

`smoke-cafe.py` 会创建临时测试学生和员工、临时调整营业设置，并在结束时恢复配置。不要对真实营业环境运行。

## 目录

```text
apps/backend/              Java 后端、咖啡业务与 Flyway 迁移
apps/admin/                管理端（独立 pnpm 项目）
apps/frontend/Student/     学生端
apps/frontend/Barista/     咖啡师端
packages/shared/           三端共享请求、组件和样式
deploy/yudao-demo/         当前远程测试栈
scripts/smoke-cafe.py      接口验收
docs/                      架构、前端、安全与部署文档
promo/                     独立宣传页与宣传片工具
```

文档入口见 [docs/README.md](docs/README.md)。历史 Go 实现保存在 `archive/go-version` 标签。
