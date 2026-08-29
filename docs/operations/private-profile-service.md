# VPS 私有 Surge Profile 服务

## 数据边界

GitHub 只保存带占位符的公开模板。VPS 本地保存真实 Sub-Store 链接，并将模板渲染为只能通过随机 HTTPS 路径访问的托管 Profile。真实订阅 URL 不进入 GitHub、systemd unit 或 Nginx 配置。

仓库中的 `deploy/install-private-profile-service.sh` 用于安装或更新 VPS 服务。它保留已经生成的随机路径和秘密文件，并在修改 Nginx 前保存可恢复副本。

## 更新链路

```text
GitHub 模板 + VPS 私密订阅源
              ↓
       下载、注入和检查
              ↓
       原子切换 current
              ↓
       Nginx 私有 HTTPS URL
              ↓
             Surge
```

`surge-profile-render.timer` 每 15 分钟运行一次。立即更新使用：

```bash
surge-profilectl update
```

立即更新请求会给 GitHub URL 加入一次性查询参数，减少 Raw CDN 缓存造成的延迟。定时任务与手动命令共用文件锁，不会同时发布两批配置。

下载、Sub-Store 输出检查、占位符替换或 Profile 检查失败时，不切换 `current`，Surge 继续读取上一份成功生成的配置。通过控制命令切换订阅时，如果生成失败，秘密文件也会自动恢复原值。

## 切换 Sub-Store 链接

所有 Profile 默认共用一个链接：

```bash
surge-profilectl set-default
```

为某个 Profile 单独设置链接：

```bash
surge-profilectl set main
surge-profilectl set simple
```

删除单独设置、恢复使用默认链接：

```bash
surge-profilectl clear main
```

命令使用隐藏输入，不把 URL 回显到终端。真实链接存放在 `/etc/surge-profile/secrets.json`，权限必须是 `0600`。

## 状态和输出 URL

```bash
ssh eb surge-profilectl status
ssh eb surge-profilectl urls
```

`status` 只显示订阅是否已配置，不显示真实地址。`urls` 显示应添加到 Surge 的私有托管 Profile URL。

## 日常速查

```bash
# 立即更新 GitHub 模板
ssh eb surge-profilectl update

# 更换所有 Profile 默认使用的订阅，输入内容不会回显
ssh -t eb surge-profilectl set-default

# 为单独 Profile 设置或清除订阅覆盖
ssh -t eb surge-profilectl set main
ssh -t eb surge-profilectl set simple
ssh eb surge-profilectl clear main
ssh eb surge-profilectl clear simple

# 检查 timer 和最近一次服务日志
ssh eb systemctl list-timers surge-profile-render.timer --no-pager
ssh eb journalctl -u surge-profile-render.service -n 20 --no-pager
```

重新安装 Surge Profile 时，先运行 `ssh eb surge-profilectl urls`。选择：

- `surge-main.conf`：Boom（含 `TX`）、HomeProxy、Singapore、HongKong、TaiWan、CTM、Bilibili、US 等多策略组；
- `surge-simple.conf`：只有 `DIRECT / Proxy / REJECT`，在一个 `Proxy` 组中切换订阅节点。

私有 URL 包含随机路径，相当于访问凭据。不要放入 GitHub、公开截图或第三方文档。

## 增加 Profile

在 `config/private-profile-templates.json` 中增加一项，并确保模板各包含一次：

```text
__SUBSTORE_URL__
__MANAGED_CONFIG_URL__
```

推送 GitHub 后运行 `surge-profilectl update`，新配置即可加入下一次原子 release。若它需要独立订阅，再运行 `surge-profilectl set PROFILE_ID`。
