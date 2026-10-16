# 后端改用 yudao 的 Java 后端，咖啡业务做成其中一个模块

管理端要用 yudao 现成的后台页面，而这些页面的登录、权限、菜单都依赖 yudao 自己的 Java 后端，所以整个后端迁到 yudao：菜单、订单、录单、回填这些咖啡业务做成 yudao 里的一个模块，学生端（保留现有前端）和咖啡师端也连这一个后端。Go 后端（2026 年 9 月刚从 Python 重写）在 Java 后端开工时删除，最后一个 Go 版本保存在 git 标签 `archive/go-version`。

## Considered Options

- 只用 yudao 的前端，后端保留 Go：要在 Go 里重做 yudao 页面依赖的登录、权限、菜单等接口。
- yudao 后端管管理端、Go 后端管学生端：两个后端各存一份商品、订单和余额，要互相同步，账迟早对不上。
- 从零写一个新的 Java 后端，只借用 yudao 的页面：同样要重做 yudao 页面依赖的那些接口。
