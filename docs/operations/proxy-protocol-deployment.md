# 代理协议部署（Snell v5 / v6 与原生 AnyTLS）

数据日期：2026-10-24。依据：`deploy/manage-proxy-protocols.sh`（v1.0.0）、
`deploy/snell-userctl.sh`（v1.0.0）与 `deploy/snell-discover.sh` 的源码。
下文命令、路径、默认值均取自脚本常量与函数实现，未在真实 VPS 上重新执行验证；
实际部署时以脚本 `status` 与 `systemctl` 输出为准。

## 适用范围与边界

仓库内这套脚本只管理三种协议，且仅覆盖二进制与 systemd 单元：

| 协议 | 版本 | 部署方式 |
|---|---|---|
| Snell v5 | 5.0.1 | 按用户实例 |
| Snell v6 | 6.0.0-rc2 | 按用户实例（官方 RC 包） |
| 原生 AnyTLS | 0.0.13 | 单实例单密码 |

脚本自身声明的边界（`manage-proxy-protocols.sh` 帮助文本）：

- 只管理上述三者，不改动 sing-box、Nginx 或其他代理服务；
- **不配置防火墙**：脚本内没有任何 `ufw`/`nft`/`iptables` 调用，端口放通
  需要按主机现有防火墙策略自行完成；
- 仅支持 x86_64/amd64 与 systemd（`require_amd64`、`require_systemd`）；
- Snell 安装只落二进制与 unit 模板，不创建默认实例。

凭据边界：Snell 的 PSK 与 AnyTLS 的密码只写入服务器上 root 可读的配置文件，
本仓库不记录任何真实凭据。`--show-secrets` 只在需要把节点行复制到私有订阅源
时使用，并注意终端记录与 shell 历史。

## 文件与路径

| 组件 | 二进制 | 配置 | systemd 单元 |
|---|---|---|---|
| Snell v5 | `/usr/local/libexec/snell/v5/5.0.1/snell-server` | `/etc/snell-users/NAME.conf`（0600） | `snell-v5@NAME.service` |
| Snell v6 | `/usr/local/libexec/snell/v6/6.0.0-rc2/snell-server` | `/etc/snell-users/NAME.conf`（0600） | `snell-v6@NAME.service` |
| AnyTLS | `/usr/local/bin/anytls-server` | `/etc/anytls-native/env`（0600） | `anytls-native.service` |

变更前的备份统一落在 `/var/backups/proxy-protocols`（目录 0700，备份为
`tar.gz` 并做 `gzip -t` 校验）。Snell 用户操作的备份另存在
`/var/backups/snell-users`。

## 端口在哪里设置

这是两套模型最容易混淆的地方：**AnyTLS 在安装时给端口，Snell 在建用户时给端口。**

| 协议 | 设置时机 | 设置方式 | 默认值 |
|---|---|---|---|
| AnyTLS | 安装时 | `install anytls --port N`、环境变量 `ANYTLS_PORT`，或交互菜单的端口提示 | 50014 |
| Snell | 创建用户时（`add`） | `snell-userctl.sh add NAME --port N`，必填 | 无默认，必须显式给出 |

具体行为：

- AnyTLS 端口经校验（1–65535）后写入 unit 的 `ExecStart` 行；重装时旧 unit、
  二进制、env 会先整包备份。
- Snell 的 `install snell-v5|v6` 完全不涉及端口，只下载并校验二进制、写 unit
  模板；端口写在每个用户的 `NAME.conf` 里，形如 `listen = [::]:PORT`，并同时
  设置 `ipv6 = true`，即 IPv6/IPv4 双栈监听。
- 两个脚本都不检查端口是否已被其他进程占用，重复端口会在实例启动时失败，需自行
  预检。

## Snell：安装、建用户、迁移版本

三步模型：装二进制 → 建用户 → 取节点行。

```bash
sudo ./manage-proxy-protocols.sh install snell-v5
sudo ./snell-userctl.sh add alice --port 32003 --version 5
sudo ./snell-userctl.sh show alice --show-secrets
```

- `add` 内部会调用 `ensure_binary`：二进制缺失或 SHA256 不匹配时自动重新下载
  安装。因此 `install` 不是必需前置，但显式执行更便于确认版本来源。
- 每个用户独立配置、端口、PSK 与 systemd 实例；v5 与 v6 可同时给不同用户运行。
- PSK 未显式指定时自动生成 32 字节随机值，写入 0600 配置；不要把它粘进公开日志。

版本迁移用 `switch`，它只改配置里的 `# managed-version` 标记并切换 unit，
**端口与 PSK 保持不变**，客户端无需改配置：

```bash
sudo ./snell-userctl.sh switch alice --version 6
```

改端口没有专用命令。可行路径有两条，取舍不同：

1. `remove` + `add`：受备份保护，但 `remove` 会删除旧配置，`add` 重新生成
   新 PSK，客户端节点必须同步更新；
2. 手工编辑 `/etc/snell-users/NAME.conf` 的 `listen` 后重启对应 unit：不换
   PSK，但属于脚本外操作，不产生自动备份。

其他命令：`list`、`show NAME`、`remove NAME`。卸载 Snell 版本时，
`manage-proxy-protocols.sh uninstall snell-v5|snell-v6` 会拒绝删除仍被用户
占用的版本，需先把这些用户切走或删除。

## AnyTLS：安装、改端口、轮换密码

```bash
sudo ./manage-proxy-protocols.sh install anytls --port 50014
sudo ./manage-proxy-protocols.sh status
sudo ./manage-proxy-protocols.sh uninstall anytls          # 保留配置
sudo ./manage-proxy-protocols.sh uninstall anytls --purge  # 连密码与系统用户一起删
```

- 安装会创建系统用户 `anytls`、生成 `/etc/anytls-native/env`，并以加固参数
  运行 unit（`ProtectSystem=strict`、`MemoryDenyWriteExecute`、空
  `CapabilityBoundingSet` 等）。
- 改端口 = 用新 `--port` 重跑 `install`。注意 env 文件已存在时**不会重写**，
  所以换端口不换密码。
- 轮换密码：编辑 `/etc/anytls-native/env` 中的 `ANYTLS_PASSWORD`，再
  `systemctl restart anytls-native.service`。这是脚本外操作，不受自动备份保护。
- 证书是运行时动态自签，客户端节点必须带 `skip-cert-verify=true`、`reuse=false`；
  安装完成时脚本会直接打印可粘贴的节点行。

## 验证清单

按顺序确认，任一环节失败就停在该层：

1. `systemctl is-active snell-v5@NAME.service` / `anytls-native.service`；
2. `ss -lntp | grep <port>` 确认监听地址与端口符合预期；
3. `journalctl -u <unit> -n 50 --no-pager` 无启动错误；
4. 用私有订阅源里的节点行做一次客户端连通测试；
5. 回到 Sub-Store 或 Surge 确认节点出现在预期策略组。

`manage-proxy-protocols.sh status` 打印的 AnyTLS 端口直接从
`anytls-native.service` 的 `ExecStart` 解析；只有 unit 不存在时才回退到
`ANYTLS_PORT` 或默认值 50014，并在括号里标注来源（`from unit` 或
`expected, not installed`）。

## 回滚

- 目标已存在时，脚本在写入前把受影响的二进制、unit、配置打包到
  `/var/backups/proxy-protocols`（首次安装不会生成空备份）；回滚即解包覆盖
  对应路径后 `systemctl daemon-reload` 并重启 unit。
- AnyTLS 卸载默认保留 `/etc/anytls-native`，便于用同一密码重新安装。
- 不要在没有替换节点的情况下删除正在承载流量的实例。

## 已知缺口

1. 不管理防火墙：端口是否可达取决于主机既有策略，脚本不做校验也不做变更。
2. Snell 版本常量在两个脚本里各存一份：两者都要能独立运行，各自持有
   `SNELL_V5_VERSION` / `SNELL_V6_VERSION`。两个 unit 模板现在都由本文件内的常量
   经 `binary_path` 派生，不再硬编码版本路径；但跨文件仍无一致性校验，升级版本号
   必须同时改两处，否则写出的 unit 会指向不存在的路径。
3. AnyTLS 是单实例单密码：没有多用户、多端口能力，与 Snell 的按用户隔离不对等。
4. Snell 没有改端口命令，也没有端口冲突预检。
5. `snell-discover.sh` 用于盘点主机上已有的零散 Snell 部署，本文未展开其流程，
   需要接管存量节点时再单独确认。
