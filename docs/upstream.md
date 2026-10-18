# 上游来源与保留范围

当前实现与约束见 [架构说明](architecture.md)、[安全说明](security.md) 与 [ADR 0001](adr/0001-yudao-java-backend.md)。

- Java：[YunaiV/ruoyi-vue-pro](https://github.com/YunaiV/ruoyi-vue-pro/tree/master-jdk17)，`master-jdk17`，固定来源提交 `7c397bbfae3e768b26e3ee962c5aa7064e8d7c96`，版本 `2026.09-SNAPSHOT`。保留 MIT 许可证。
- 管理端：[yudaocode/yudao-ui-admin-vue3](https://github.com/yudaocode/yudao-ui-admin-vue3)，`master`，固定来源提交 `050bac1eccfbe7393a1568d614151cc99501b949`，同一 `2026.09` 版本线。保留 MIT 许可证。

保留 common、MyBatis、Redis、Web、Security、Excel、测试、数据权限与 IP starter，system 的用户/角色/RBAC/OAuth2 令牌及相关字典、部门岗位选择器、审计日志，infra 的配置、文件服务和异常日志。Redis 使用 Spring Data Redis/Lettuce，继续沿用芋道 JSON 缓存及令牌 DAO；订单并发通过数据库条件更新和唯一约束保障。文件服务仅保留数据库存储，未保留云存储、WebSocket、Quartz、消息队列、代码生成器。

关闭且移除了租户业务与租户数据表；DO 改用芋道 `BaseDO`。不引入 member 模块，cafe 学生通过 `OAuth2TokenService` 和专属 OAuth2 client 签发 MEMBER 令牌。管理端沿用芋道请求层、登录态、字典、权限指令、动态菜单、用户与角色页面，删除其余业务页面、演示页和第三方登录入口，精简导航框架并增加咖啡页面。

钉钉企业内部应用免登按学校约定使用以下官方接口，凭证与 token 不返回给前端：

- [获取企业内部应用 access_token](https://open.dingtalk.com/document/orgapp/obtain-the-access_token-of-an-internal-app)：`GET https://oapi.dingtalk.com/gettoken`。
- [通过免登码获取用户信息](https://open.dingtalk.com/document/development/obtain-the-userid-of-a-user-by-using-the-log-free)：`POST /topapi/v2/user/getuserinfo`。
- [查询用户详情](https://open.dingtalk.com/document/development/query-user-details)：`POST /topapi/v2/user/get`，默认读取 `job_number`。

官方站点的这些页面为动态文档；学校凭证、应用通讯录权限、真实学号字段和家校通讯录范围仍需学校现场确认。学生卡真实接口仍留在 `StudentCardClient` 边界，未编造 HTTP 协议。
