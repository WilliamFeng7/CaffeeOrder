# 免登录演示部署

访问 http://150.158.121.81:5001 会直接进入点菜页。浏览器自动获取独立访客会话，
余额为 ¥10,000 模拟金额；支持选品、购物车、下单、订单记录和取餐页。
关闭标签页后，新浏览器会话使用新访客账户。后台管理权限仍需正式账号登录。

部署时只复制当前菜单和商品图片，不复制本地账户、历史订单或环境密钥。
服务器演示库独立保存，后续部署不会覆盖已有演示订单。

```bash
bash deploy/demo/deploy.sh ubuntu@150.158.121.81
```

需要本机 Go、Node.js、Python 3、已安装的 npm 依赖，以及服务器 SSH 和 sudo 权限。
脚本编译 Linux amd64 二进制，使用 systemd 托管，无需服务器安装 Node 或 Go。

服务器目录：`/home/ubuntu/coffee-order-demo`。
运行配置：`demo.env`，权限为 600，JWT 密钥在服务器生成。
服务：`coffee-order-demo.service`，监听 `0.0.0.0:5001`，已配置开机启动和故障重启。

```bash
sudo systemctl status coffee-order-demo
sudo journalctl -u coffee-order-demo -n 50 --no-pager
sudo systemctl restart coffee-order-demo
```

恢复登录：将服务器 `demo.env` 中 `DEMO_MODE=true` 改为 `DEMO_MODE=false`，
然后重启服务。演示会话会失效；新演示库没有正式账号，需要创建账号后才能登录。
本地后端同样通过 `.env` 中的 `DEMO_MODE` 控制，修改后重启生效。

仅点菜端提供免登录模式，后台和咖啡师端仍保留原有鉴权。
