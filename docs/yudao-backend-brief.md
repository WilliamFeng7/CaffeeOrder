# OTIA Café：yudao 后端与管理端开发说明

> 这份说明写给负责后端和管理端的 AI。动手前请先读完本文件、[GLOSSARY.md](../GLOSSARY.md) 和 [docs/adr/0001-yudao-java-backend.md](adr/0001-yudao-java-backend.md)。界面文字和返回给用户的提示，叫法一律以 GLOSSARY.md 为准。

## 1. 项目是什么

- 北京外国语大学附属杭州橄榄树学校的咖啡厅 OTIA Café。学生在午间（11:40–12:30）和放学后（15:30–17:00）买咖啡，每天约 100–200 单。现在是在柜台口头点单。
- 新流程：学生在钉钉里打开学生端，自动登录，点单后用学生卡余额付款。咖啡师照着收银台旁 iPad 上的咖啡师端，把订单录进咖啡厅自己的收银系统，再把收银单号回填进来；饮品做好后点"制作完成"。学生在学生端看到收银单号和进度。
- 现场口头点单照常存在，本系统看不到。
- 收银对接分直连模式和录单模式。收银系统现在没有接口，这次只做录单模式。

## 2. 分工

| 部分 | 负责 | 位置 |
| --- | --- | --- |
| 后端（yudao Java 后端 + 咖啡模块） | 你 | `apps/backend` |
| 管理端（yudao 前端） | 你 | `apps/admin` |
| 学生端 | Claude | `apps/frontend/Student` |
| 咖啡师端 | Claude | `apps/frontend/Barista` |
| 学生端和咖啡师端的共享代码 | Claude | `packages/shared` |

Claude 负责的三个目录不要改，那边有人在同时修改。双方靠第 7 节的接口约定对接。

## 3. 总体要求

- 按 yudao 的规矩写：包名、DO / Mapper / Service / Controller / VO 分层、`CommonResult`、`ErrorCode`、权限注解、SQL 脚本的放法都和 yudao 自带模块保持一致。
- 只保留用得上的东西：用不到的 yudao 模块、页面、菜单、数据表全部删掉，也不要写"以后可能用到"的代码。
- 稳定优先：涉及钱和订单状态的每一步都要防并发、防重复，关键逻辑写单元测试。
- 金额一律用"分"（整数）。时间按 Asia/Shanghai，"当天"指北京时间的自然日。

## 4. 开工前先清理旧代码

旧版本已经保存在 git 标签 `archive/go-version` 里，可以放心删除。

1. 先把 `apps/backend/static/menu/` 和 `apps/backend/static/default.png` 搬到新后端（见 6.8）。`apps/backend/static/barista/` 是旧的构建产物，不要搬。
2. 删除 `apps/backend`（Go 后端）和 `apps/frontend/Admin`（旧管理端）。
3. 删除只给 Go 版用的部署文件：`deploy/`、`docker-compose.prod.yml`、`DEPLOYMENT.md`。`docker-compose.yml` 改成本地开发用的 MySQL + Redis。
4. 清理所有引用旧代码的地方：根目录 `package.json` 里的 `dev:admin`、`run-local.sh`、`stop-local.sh`、`README.md`、`docs/image-credits.md`（图片路径），并在 `.gitignore` 里加上 Java / Maven 和 pnpm 的忽略项。
5. 生产部署以后再定，这次不做。演示站（150.158.121.81:5001）上跑的是已经部署好的 Go 版，删代码不影响它。

## 5. yudao 底座

- **后端**：用 ruoyi-vue-pro 的 `master-jdk17` 分支（JDK 17+、Spring Boot 3）单体版，放进 `apps/backend`。只保留 `yudao-dependencies`、`yudao-framework`（只留用得上的 starter）、`yudao-server`、`yudao-module-system`、`yudao-module-infra`，再新增 `yudao-module-cafe`。其余模块（mall、pay、member、bpm、crm、erp、iot、ai、mp、report 等）连目录一起删除。
- **学生账号**：不启用 member 模块。学生存在 cafe 模块自己的学生表里，登录后用 yudao 的 OAuth2 令牌机制签发 MEMBER 类型的令牌（`/app-api/**` 本来就按 MEMBER 用户鉴权）。如果确实绕不开 member 模块，就启用它、隐藏用不到的菜单，并在 `docs/adr/` 里新增一条记录说明原因。
- **开关**：关闭多租户（后端 `yudao.tenant.enable: false`，前端同步关闭），关闭登录验证码，关闭 yudao 的演示模式。
- **数据库**：MySQL 8 + Redis。本地用根目录的 `docker-compose.yml` 启动。
- **管理端**：用 yudao-ui-admin-vue3（Vue 3 + Element Plus），版本和后端对应，放进 `apps/admin`。这个目录不在根目录 npm workspace 的范围内，用它自己的包管理器。删掉用不到的页面、路由、接口文件和菜单数据，站点标题改成"OTIA Café 管理后台"。
- **端口**：后端 48080（yudao 默认），管理端开发服务器 8080。学生端 5173、咖啡师端 8081 保持不变，它们的代理由 Claude 来改。

## 6. 咖啡模块的业务规则

### 6.1 学生和登录

- 学生在钉钉里打开学生端，前端通过钉钉 JSAPI（`dd.getAuthCode`）拿到免登授权码，交给后端。后端用学校提供的 AppKey / AppSecret 取 access_token，用授权码换钉钉 userid，再查用户详情，从中读出学号，按学号找到或新建学生记录，最后签发令牌。参考钉钉开放平台"企业内部应用免登"：`gettoken`、`topapi/v2/user/getuserinfo`、`topapi/v2/user/get`。动手时以钉钉当前文档为准。
- 学号存在钉钉用户详情的哪个字段，做成配置，默认 `job_number`（工号）。如果学校的学生在钉钉家校通讯录里，取学号的接口不同，到时按学校实际情况调整。
- 学生记录只存学号、姓名、钉钉 userid、首次登录时间和最近登录时间。
- 学生令牌的有效期设长一些（比如 7 天）。过期后学生端会重新走一遍钉钉免登，所以不需要刷新令牌的接口。
- 开发用的"学号直登"接口只在配置 `cafe.auth.dev-login-enabled=true` 时存在，默认关闭，生产环境绝不能打开。
- 没有密码，没有注册，也没有修改密码。

### 6.2 学生卡

- 定义接口 `StudentCardClient`，提供三个方法：查余额；扣款（用我们的订单号作幂等号）；退款（用同一个订单号）。
- 学生卡系统的真实接口文档还没拿到。现在只写一个 mock 实现，开发时用：在内存里给每个学号一个默认余额（比如 500 元），由 `cafe.card.mock-enabled` 打开。如果 mock 关着、又没有真实实现，后端启动时直接报错，避免生产环境用假账。不要预先写一个靠猜的 HTTP 客户端。
- 没有退单、也没有取消：学生下单即扣款，不能取消，咖啡师也没有退单功能。退款接口只用于 6.4 里的系统内部补偿。

### 6.3 菜单

- **分类**：编码（学生端按编码配图标）、中文名、英文名、排序。初始四个分类：`coffee` 现磨咖啡、`seasonal` 当季新品、`fruit` 鲜果茶、`bakery` 烘焙轻食。
- **商品**：中文名、英文名、中文描述和英文描述（都可以为空）、价格、分类、图片、是否店长推荐、上架 / 下架、是否售罄、排序。不记库存数量，东西卖完了由店长标"售罄"。
- **规格**：规格组（比如温度、糖度）有中文名、英文名和排序；组里的选项有中文名、英文名、加价和是否默认。一个商品可以挂几个规格组，每组只能选一个。菜单要和收银系统保持一致，店长以后会照着收银系统修改，所以叫法和价格都要能在管理端改。
- **初始数据**：见附录 A，照搬现在的菜单。

### 6.4 下单与付款

1. 先检查营业状态（见 6.5），不在营业时段就拒绝下单。
2. 校验每个商品在售、没有售罄，所选选项都属于这个商品的规格组，每组正好选一个。单价等于商品价加上选项加价，一律按服务端的价格算，不信任前端传来的价格。每单杯数有上限，做成配置，默认 10 杯。
3. 先保存订单，状态设为内部的"支付中"（学生和咖啡师都看不到），再用订单号调学生卡扣款。
4. 扣款成功，状态改为待录单。如果是余额不足这类明确的失败，状态改为内部的"支付失败"，并把原因返回给学生。如果超时或结果不明，就用同一个订单号调一次退款，再标记为支付失败，提示学生稍后查看余额。
5. 写一个定时任务：处理停在"支付中"超过几分钟的订单（比如服务中途重启），按第 4 步"结果不明"的办法处理。
6. 订单里保存商品快照：名称、图片、单价、数量、所选规格。规格既存结构化数据，也存一行文字，比如"冰 / 半糖"。

### 6.5 营业时段

- 店长在管理端维护三样东西：营业时段列表（默认每天 11:40–12:30 和 15:30–17:00）；营业开关（临时关店、周末和假期时用）；公告（可以为空，最多 120 字）。
- 能下单的条件：营业开关是打开的，并且当前时间落在某个营业时段内。

### 6.6 订单状态和咖啡师的操作

| 状态 | 含义 | 谁能看到 |
| --- | --- | --- |
| 支付中、支付失败 | 内部状态 | 只有管理端 |
| 待录单 | 已扣款，等咖啡师录单 | 学生端、咖啡师端、管理端 |
| 制作中 | 已回填收银单号 | 同上 |
| 制作完成 | 饮品已做好，可以取餐 | 同上 |

- **回填**：待录单 → 制作中，记录收银单号和回填时间。收银单号按原样保存为字符串：去掉首尾空格，不能为空，最长 20 个字符；当天的 App 订单里不能出现重复的收银单号。制作中的订单允许修改收银单号，用于输错后更正。
- **制作完成**：制作中 → 制作完成，记录完成时间。
- **撤回**：制作完成 → 制作中，清空完成时间，用于咖啡师点错的情况。只能撤回当天的订单。
- 每次改状态都用"当前状态等于预期状态"的条件更新，防止两台设备同时操作或重复点击造成错乱。条件不满足时提示"订单状态已变化，请刷新"。
- 记录三个时间：下单、回填、制作完成。等待时间的统计等上线两三周、有了数据以后再做，这次不做任何估算。
- 不设归档状态。不是当天的订单，就不再出现在咖啡师端，也不算进学生端的进行中订单。

### 6.7 排队单数

- 排队单数 = 当天处于待录单或制作中的 App 订单数。
- 每个进行中的订单附带"前面还有几单"：当天比它早下单、并且处于待录单或制作中的订单数。

### 6.8 图片

- 原有的商品图搬到新后端后，继续用原来的地址访问：大图是 `/static/menu/<名字>.jpg`，小图是 `/static/menu/<名字>-640.jpg`（学生端按这个规则取小图）。`/static/default.png` 也一样。
- 店长新上传的图片走 yudao 的文件服务。

## 7. 接口约定

学生端和咖啡师端按这一节对接。返回格式沿用 yudao 的 `{ code, data, msg }`：`code` 为 0 表示成功；失败时 `msg` 是直接给用户看的中文提示。字段名用驼峰，金额单位是分，时间沿用 yudao 默认的序列化方式（毫秒时间戳）。如果实现时必须改接口，改完同步更新这一节。

订单状态的取值：`10` 待录单，`20` 制作中，`30` 制作完成。内部状态的取值由你定，不会返回给学生端和咖啡师端。

### 7.1 学生端（前缀 `/app-api/cafe`，需要学生令牌，标"免登录"的除外）

| 方法和路径 | 说明 |
| --- | --- |
| `GET /auth/dingtalk-config` | 免登录。返回 `{ corpId }`，前端调钉钉 JSAPI 时要用 |
| `POST /auth/dingtalk-login` | 免登录。请求 `{ authCode }`，返回 `{ accessToken, expiresTime, studentNo, name }` |
| `POST /auth/dev-login` | 免登录，只在开发配置下存在。请求 `{ studentNo, name }`，返回同上 |
| `GET /student/me` | 返回 `{ studentNo, name, balance }`，`balance` 是学生卡余额 |
| `GET /menu` | 免登录。返回 `{ categories: Category[], items: MenuItem[] }`，只包含上架的商品，售罄的也返回 |
| `GET /shop/status` | 免登录。返回 `{ open, banner, businessHours: [{ start: "11:40", end: "12:30" }] }` |
| `POST /order/create` | 请求 `{ items: [{ itemId, quantity, optionIds: [] }] }`，返回 `Order` |
| `GET /order/page?pageNo=1&pageSize=20` | 返回 `{ list: Order[], total }`，新单在前，不含内部状态 |
| `GET /order/queue` | 返回 `{ waitingCount }`，即排队单数 |

```text
Category = { code, name, nameEn, sort }
MenuItem = { id, name, nameEn, description, descriptionEn, price, categoryCode, imageUrl,
             recommended, soldOut, sort,
             optionGroups: [{ id, name, nameEn,
                              options: [{ id, name, nameEn, priceDelta, isDefault }] }] }
Order    = { id, orderNo, status, posOrderNo, aheadCount, totalPrice,
             createTime, enteredTime, doneTime,
             items: [{ itemId, name, nameEn, imageUrl, unitPrice, quantity, optionsText,
                       options: [{ groupName, groupNameEn, name, nameEn }] }] }
```

- `posOrderNo` 是收银单号，回填前为 `null`。
- `aheadCount` 只对当天进行中的订单有值，其他情况为 `null`。

### 7.2 咖啡师端（前缀 `/admin-api`，用咖啡师账号登录）

| 方法和路径 | 说明 |
| --- | --- |
| `POST /system/auth/login` | yudao 自带，请求 `{ username, password }`，验证码已关闭 |
| `POST /system/auth/refresh-token?refreshToken=` | yudao 自带 |
| `POST /system/auth/logout` | yudao 自带 |
| `GET /cafe/barista/order/board` | 返回 `{ waiting: BaristaOrder[], making: BaristaOrder[], recentDone: BaristaOrder[] }`。前两组是当天的订单，按下单时间从早到晚排；`recentDone` 是当天最近制作完成的 10 单，新的在前 |
| `PUT /cafe/barista/order/enter` | 请求 `{ id, posOrderNo }`，回填收银单号，订单变为制作中；如果已经是制作中，就是更正收银单号 |
| `PUT /cafe/barista/order/done` | 请求 `{ id }`，订单变为制作完成 |
| `PUT /cafe/barista/order/undo-done` | 请求 `{ id }`，撤回制作完成 |

```text
BaristaOrder = { id, orderNo, status, posOrderNo, studentName, createTime, enteredTime, doneTime,
                 totalPrice, cupCount, items: [{ name, quantity, optionsText }] }
```

- 权限标识：`cafe:barista:query` 和 `cafe:barista:update`，分给咖啡师和店长两个角色。

## 8. 管理端页面

- **菜单管理**：分类；商品（上传图片、店长推荐、上架 / 下架、售罄、排序）；规格组和选项。
- **营业设置**：营业时段、营业开关、公告。
- **订单管理**：可以按日期、状态、学号或姓名、收银单号筛选；显示下单、回填、制作完成三个时间；显示筛选结果的总单数和总金额；能导出 Excel。内部状态（支付中、支付失败）在这里也能查到。
- **账号**：直接用 yudao 自带的用户和角色管理。角色有三个：
  - 学校管理员：上面所有页面，加上管理店长和咖啡师的账号；
  - 店长：菜单管理、营业设置、订单管理；
  - 咖啡师：只能调用 7.2 的接口，没有任何管理端菜单。
- 管理端只给学校管理员和店长用。咖啡师账号登录管理端时，看不到任何菜单即可。

## 9. 这次不做

- 直连模式（收银系统的接口）。
- 学生卡的真实接口（拿到文档后再接）。
- 退单、取消和退款功能（退款接口只用于内部补偿）。
- 等待时间估算、报表看板。
- 免登录演示模式。
- 生产部署。
- 对学生端、咖啡师端和 `packages/shared` 的任何改动。

## 10. 完成标准

- 用 `docker compose up -d` 启动 MySQL 和 Redis 后，照着 README 一条一条执行命令，就能把后端和管理端跑起来。
- 单元测试至少覆盖：价格计算；营业时段判断；扣款成功、明确失败、结果不明三种情况；状态流转和条件更新；当天收银单号去重。
- 打开学号直登和 mock 学生卡后，用 curl 或 Swagger 能走通以下流程：
  - 正常流程：登录 → 查菜单 → 下单（余额减少）→ 咖啡师端出现这一单 → 回填 → 学生订单显示收银单号和制作中 → 制作完成 → 学生看到制作完成；
  - 撤回制作完成；
  - 不在营业时段下单被拒绝；
  - 余额不足下单被拒绝，学生端和咖啡师端都看不到这一单。
- 管理端：店长能修改菜单和营业时段，能查订单、导出 Excel；咖啡师账号在管理端看不到任何菜单。
- 仓库里没有残留的 Go 代码、旧管理端，以及用不到的 yudao 模块和页面。
- README 写清楚本地怎么跑起来，以及需要学校提供的配置项（见附录 B）。

## 附录 A：初始菜单

| 分类 | 中文名 | 英文名 | 价格（元） | 图片 | 店长推荐 |
| --- | --- | --- | --- | --- | --- |
| coffee | 经典拿铁 | Caffe Latte | 15 | `/static/menu/latte.jpg` | 是 |
| coffee | 意式浓缩 | Espresso | 10 | `/static/menu/espresso.jpg` | 否 |
| coffee | 卡布奇诺 | Cappuccino | 16 | `/static/menu/cappuccino.jpg` | 否 |
| coffee | 焦糖玛奇朵 | Caramel Macchiato | 19 | `/static/menu/macchiato.jpg` | 是 |
| coffee | 澳白咖啡 | Flat White | 17 | `/static/menu/flatwhite.jpg` | 否 |
| seasonal | 生椰拿铁 | Iced Coconut Latte | 18 | `/static/menu/coconut-latte.jpg` | 是 |
| seasonal | 冷萃咖啡 | Cold Brew | 20 | `/static/menu/coldbrew.jpg` | 否 |
| fruit | 抹茶奶绿 | Matcha Milk Green Tea | 17 | `/static/menu/matcha.jpg` | 否 |
| fruit | 鲜果茶 | Citrus Fruit Tea | 15 | `/static/menu/fruit-tea.jpg` | 否 |
| bakery | 黄油可颂 | Butter Croissant | 12 | `/static/menu/croissant.jpg` | 否 |
| bakery | 巴斯克芝士蛋糕 | Basque Cheesecake | 22 | `/static/menu/cheesecake.jpg` | 是 |

饮品（coffee、seasonal、fruit 三类）挂两个规格组，烘焙类不挂：

- 温度：热（Hot，默认）、冰（Iced）；
- 糖度：无糖（No sugar）、半糖（Half sugar）、标准（Regular，默认）、多糖（Extra sugar）。

所有选项都不加价。等店长照着收银系统修改即可。

## 附录 B：配置项

| 配置 | 说明 | 默认值 |
| --- | --- | --- |
| `cafe.dingtalk.corp-id` | 学校钉钉的 corpId | 无，由学校提供 |
| `cafe.dingtalk.app-key`、`cafe.dingtalk.app-secret` | 钉钉 H5 微应用的凭证 | 无，由学校提供 |
| `cafe.dingtalk.student-no-field` | 学号在钉钉用户详情里的字段 | `job_number` |
| `cafe.auth.dev-login-enabled` | 开发用的学号直登 | `false` |
| `cafe.card.mock-enabled` | 学生卡使用 mock | `false`，开发配置里设为 `true` |
| `cafe.order.max-cups` | 每单杯数上限 | `10` |
