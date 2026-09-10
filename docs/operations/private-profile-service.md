# VPS 私有 Surge Profile 服务

## 数据边界

GitHub 只保存带占位符的公开模板。VPS 本地保存真实 Sub-Store 链接，并将模板渲染为只能通过随机 HTTPS 路径访问的托管 Profile。真实订阅 URL 不进入 GitHub、systemd unit 或 Nginx 配置。

仓库中的 `deploy/install-private-profile-service.sh` 用于安装或更新 VPS 服务。它保留已经生成的随机路径和秘密文件，并在修改 Nginx 前保存可恢复副本。

`deploy/sync-private-profile-service.sh` 用于从仓库一次性同步渲染器、控制命令、
systemd unit、安装脚本到 VPS，执行安装、立即渲染、`status --check`，并比对远程
渲染器 sha256 与仓库副本是否一致，防止两台机器上的代码漂移。

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

每次成功 release 会在输出文件首部写入 `# @rendered-from` 与 `# @rendered-at`，
并把 `sources` 记入 `release.json`；`surge-profilectl status --check` 用这些
元数据核对每份输出对应的 profile/version。

## 切换 Sub-Store 链接

所有 Profile 默认共用一个链接：

```bash
surge-profilectl set-default
```

为某个 Profile 单独设置链接：

```bash
surge-profilectl set surge
surge-profilectl set simple
surge-profilectl set home-wg
```

删除单独设置、恢复使用默认链接：

```bash
surge-profilectl clear surge
surge-profilectl clear simple
surge-profilectl clear home-wg
```

命令使用隐藏输入，不把 URL 回显到终端。真实链接存放在 `/etc/surge-profile/secrets.json`，权限必须是 `0600`。

## 状态和输出 URL

```bash
ssh eb surge-profilectl status
ssh eb surge-profilectl status --check
ssh eb surge-profilectl urls
```

`status` 只显示订阅是否已配置，不显示真实地址；`--check` 在 release 过期或元数据
缺失时以非零退出。`urls` 显示应添加到 Surge 的私有托管 Profile URL。

## 日常速查

```bash
# 立即更新 GitHub 模板
ssh eb surge-profilectl update

# 更换所有 Profile 默认使用的订阅，输入内容不会回显
ssh -t eb surge-profilectl set-default

# 为单独 Profile 设置或清除订阅覆盖
ssh -t eb surge-profilectl set surge
ssh -t eb surge-profilectl set simple
ssh -t eb surge-profilectl set home-wg
ssh eb surge-profilectl clear surge
ssh eb surge-profilectl clear simple
ssh eb surge-profilectl clear home-wg

# 检查 timer 和最近一次服务日志
ssh eb systemctl list-timers surge-profile-render.timer --no-pager
ssh eb journalctl -u surge-profile-render.service -n 20 --no-pager
```

重新安装 Surge Profile 时，先运行 `ssh eb surge-profilectl urls`。选择：

- `surge.conf`（`profiles/surge/`）：多策略组主配置，额外提供不绑定 `Boom` 的
  `Telegram` 与 `NSFW` 独立策略组，以及 `Foreign-Apple`、`Google` 等独有组；
- `surge-simple.conf`（`profiles/simple/`）：只产生 `DIRECT / Proxy / REJECT` 三种
  最终结果，提供 `Domestic`（默认直连）、`Apple`（默认直连）和 `Others`（默认代理）
  三个可手动切换的策略组；
- `surge-home-wg.conf`（`profiles/home-wg/`）：WireGuard 回家，除拒绝和直连外全部
  交给家中 DAE 分流。

`legacy/`（`surge-main.conf`、`surgeion.conf`、`profile.example.conf`）已冻结，
不再由本服务输出，也不会出现在 `surge-profilectl urls`。

私有 URL 包含随机路径，相当于访问凭据。不要放入 GitHub、公开截图或第三方文档。

## 版本化与回滚

三条主线分别维护在 `profiles/surge/`、`profiles/simple/`、`profiles/home-wg/`。
每个家族只有一个渲染入口（文件名与 manifest `output` 一致，路径不随版本变化），历史版本
快照放在 `version <major>/` 里。设备订阅 URL 由 manifest `output` 固定，`source` 和
`template_url` 始终指向那个入口文件，所以升级和回滚都不用再改 manifest：改的是入口文件的
正文与 `# @version:`。回滚只往前走，恢复旧内容时发布成一个新版本号，快照不会翻回 `active`。
完整契约见 [Profile 版本化](profile-versioning.md)。

仓库到 VPS 的同步：

```bash
bash deploy/sync-private-profile-service.sh
```

脚本先推送代码并安装，再执行 `surge-profilectl update` 与 `status --check`。
同步失败或远程渲染器 sha256 与仓库不一致时脚本以非零退出，不静默放行。

## 增加 Profile

在 `config/private-profile-templates.json` 中增加一项，写清 `id`、`template_url`、
`output` 和 `source`，并确保模板各包含一次：

```text
__SUBSTORE_URL__
__MANAGED_CONFIG_URL__
```

推送前运行 `tools/check-profile-versions.py`、`tools/check-private-profile-templates.py`
和 `tools/lint_surge_profiles.py`。推送后运行 `bash deploy/sync-private-profile-service.sh`
或 `surge-profilectl update`，新配置即可加入下一次原子 release。若它需要独立订阅，
再运行 `surge-profilectl set PROFILE_ID`。
