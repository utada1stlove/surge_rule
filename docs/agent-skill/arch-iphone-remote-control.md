# 在 Arch Linux 上使用 Agent 辅助远程控制 iPhone Surge

> 状态：研究稿。资料截止 2026-08-28；Arch Linux 端的 CLI 可执行性和具体 iPhone 网络环境尚未在本仓库实测。

## 先说结论

Surge 官方提供的是 Agent Skill 和 `surge-cli`，不是一个独立的“Surge Agent”。推荐的工作链路是：

```text
Codex / Claude Code
        ↓ 读取 Skill 并生成操作
surge-cli
        ↓ --remote + Controller 认证
Surge iOS / tvOS
```

官方资料确认了 Skill、CLI 和远程控制能力，但没有确认 Arch Linux 原生运行 `surge-cli` 的安装方式。因此，Arch Linux 端应先被视为 Agent 工作站，不能直接宣传为官方支持的 Surge CLI 平台。

## 官方支持的部分

Surge Mac 6.5.0（2026-04-15）开始提供 Agent Skill。Skill 位于：

```text
/Applications/Surge.app/Contents/Resources/Skills/
```

官方建议使用符号链接安装，以便 Surge 更新后同步 Skill 内容。`surge-cli` 支持本地控制，也支持使用 `--remote/-r <host:port>` 连接远程 Surge 实例。目标实例需要配置 `external-controller-access`。

参考：[官方发布说明](https://nssurge.com/support/mac/release-notes)、[CLI 手册](https://manual.nssurge.com/tools/cli.html)。

## 版本边界

不要把所有新命令都归到同一个版本：

- Mac 6.5.0+：Agent Skill；
- Mac 6.8.0+：扩展管理与诊断命令；
- Mac 6.9.0+：`rule match`、`rule explain`、临时规则、DNS trace 等路由和网络诊断命令；
- 官方文档说明相关命令可远程操作兼容的 Surge iOS 5.21.0 / tvOS 5.21.0 实例。

## Arch Linux 场景的实际拆解

### 1. Agent 端

Codex 或 Claude Code 可以运行在 Arch Linux 上，并读取一个符合其 Skills 机制的 Surge Skill 文件。但“能够读取 Skill”只代表 Agent 知道如何组织调用，不代表系统已经拥有 `surge-cli` 可执行文件。

### 2. CLI 端

官方文档只给出了 Surge Mac App Bundle 中的 CLI 路径，没有提供 Linux 安装包说明。需要先确认 CLI 实际运行位置：

- 在拥有 Surge Mac 的 macOS 设备上运行 CLI，再通过 `--remote` 控制 iPhone；或
- 在 Arch Linux 上验证是否存在合法且兼容的 CLI 运行方式。

第二种路径在验证完成前，不应写成“安装即可使用”。

### 3. iPhone 端

iPhone Surge 需要启用远程 Controller 访问，并配置认证。具体地址、端口、密码和访问范围应按当前 Surge iOS 版本与本地网络环境设置，避免将 Controller 暴露到公网。

## 建议的验证顺序

1. 先在 Mac 上确认 `surge-cli --help` 和目标 Surge 版本；
2. 在 iPhone Surge 中确认远程 Controller 和访问控制配置；
3. 从同一局域网执行只读命令，例如状态、版本或摘要查询；
4. 再测试 `--raw` JSON 输出，确认 Agent 是否能稳定解析；
5. 最后才测试模式切换、策略组切换或临时规则等有副作用的命令；
6. 每次操作记录执行端、目标端、Surge 版本、命令和返回结果。

## 安全边界

- 不把 Controller 端口直接暴露到公网；
- 不把密码写进命令行参数、脚本仓库或聊天记录；
- Agent 默认先执行只读诊断，涉及模式、策略组、配置和规则的变更必须明确确认；
- 为远程访问设置最小网络范围，并在测试结束后关闭不需要的访问；
- 远程命令失败时，先区分网络不可达、认证失败、版本不兼容和命令不可用。

## 当前不能下的结论

本文不声称 Arch Linux 有官方 Surge CLI 安装包，也不声称任意 Codex 环境可以直接调用 iPhone Surge。完成这部分需要真实环境测试，并补充命令输出、版本信息和网络拓扑证据。
