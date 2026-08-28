# Surge Agent Skill 与 surge-cli 官方资料核查

资料核查日期：2026-08-28
证据范围：Surge 官方发布说明、官方手册和官方博客。
本文件不是对本地 Surge 环境的实测报告。

## 已确认的官方事实

### Agent Skill 的定位

Surge Mac 6.5.0（2026-04-15）发布说明写明，Surge Mac 支持 AI agent skill operations，并将 `surge-cli` 的操作能力通过内置说明暴露给支持 Skills 的 Agent。官方建议从以下目录安装 Skill，并使用符号链接保持其随 App 更新：

```text
/Applications/Surge.app/Contents/Resources/Skills/
```

来源：[Surge Mac Release Notes](https://nssurge.com/support/mac/release-notes)。

### `surge-cli` 与远程实例

官方 CLI 手册将 `surge-cli` 描述为 Surge Mac 提供的命令行控制工具，并列出 `--remote/-r <host:port>` 远程连接参数。远程连接要求目标实例配置 `external-controller-access`；密码可通过安全提示、`SURGE_CLI_PASSWORD` 或标准输入提供。

来源：[Surge Mac CLI](https://manual.nssurge.com/tools/cli.html)。

### 能力与版本边界

- Agent Skill：Surge Mac 6.5.0+；
- 扩展管理和诊断命令：官方 CLI 手册标注为 Mac 6.8.0+；
- `rule match`、`rule explain`、临时规则、DNS trace、GeoIP、`vmnet` 等路由与网络诊断命令：官方 CLI 手册标注为 Mac 6.9.0+；
- CLI 文档说明这些命令可以通过 `--remote` 操作兼容的 Surge iOS 5.21.0 和 Surge tvOS 5.21.0 实例。

因此，不能把 6.8.0 和 6.9.0 的全部命令合并成一个版本能力集合。

### 平台限制

官方手册将 `surge-cli` 描述为随 Surge Mac 提供的工具，并给出 macOS App Bundle 路径；Surge iOS 的产品说明则将其描述为 Network Extension VPN。现有官方资料没有给出 Arch Linux 原生 `surge-cli` 安装包或 Linux 支持说明。

来源：[Surge Manual Introduction](https://manual.nssurge.com/)、[How Surge Works](https://manual.nssurge.com/getting-started/how-surge-works.html)。

## 事实、推断与待实测项

| 类型 | 结论 |
|---|---|
| 官方事实 | Skill 随 Surge Mac App Bundle 提供；`surge-cli` 支持远程实例；远程访问需要 Controller 权限配置。 |
| 合理推断 | Arch Linux 上的 Codex 可以作为 Agent，但不能据此推断 Arch 上存在官方原生 CLI。 |
| 待实测 | 从 Arch Linux 直接执行由 macOS 提供的 CLI 是否可行；二进制兼容性、网络连通性和认证行为都需单独验证。 |
| 待实测 | iPhone Surge 的 Controller 地址、端口、访问控制和版本组合是否适合具体家庭网络。 |
| 决策 | 首篇文章只介绍受支持的架构和验证方法，不承诺未经测试的 Linux 端落地方案。 |

## 写作中应避免的表述

- “Surge 官方推出了 Surge Agent”：不准确；
- “6.8.0 已包含所有 Rule Match / DNS trace 能力”：版本边界不准确；
- “Arch Linux 可以直接安装官方 surge-cli”：当前官方资料不足以支持；
- “开放 Controller 端口即可远程控制”：缺少认证和暴露面安全条件。

## 参考来源

- [Surge Mac Release Notes](https://nssurge.com/support/mac/release-notes)
- [Surge Mac CLI Manual](https://manual.nssurge.com/tools/cli.html)
- [Surge CLI Updates](https://nssurge.com/blog/)
- [Surge Manual Introduction](https://manual.nssurge.com/)
- [HTTP API](https://manual.nssurge.com/tools/http-api.html)
