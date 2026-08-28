# Surge 内容地图

## 定位

本仓库用于沉淀 Surge 的配置实践、网络诊断与自动化内容，重点面向已经使用 Surge、希望理解规则行为并提升排错效率的进阶用户。

## 核心读者

- 使用 Surge iOS 或 Surge Mac、但对 Profile 和规则机制理解不完整的用户；
- 需要维护规则、策略组、DNS、脚本和模块的用户；
- 希望在 Arch Linux 等非 macOS 环境中，通过 Codex 或其他支持 Skills 的 Agent 辅助操作 Surge 的用户。

## 内容边界

### 纳入

1. Surge 的工作模型与 Profile 基础；
2. Rule、Policy、Policy Group、DNS、MITM、Rewrite 和 Scripting；
3. `surge-cli` 的查询、诊断、自动化和远程控制；
4. 官方 Agent Skill 的安装模型、能力边界和安全实践；
5. Arch Linux + iPhone Surge 的远程控制架构与实测限制；
6. 规则命中、DNS、策略选择、日志和临时规则排错。

### 暂不纳入

- 未经验证的 Linux 原生 Surge 客户端或 `surge-cli` 发行方案；
- 将 Agent Skill 包装成独立“Surge Agent”的宣传性说法；
- 代理节点分享、绕过授权或弱化 Controller 安全的内容；
- 只复述版本更新、但没有实际操作价值的新闻稿。

## 首批交付物

| 产物 | 目的 | 验收标准 |
|---|---|---|
| 本文件 | 固定内容定位和范围 | 主题边界清楚，能指导后续选题 |
| `reports/official-source-audit.md` | 保存一手资料、版本和证据边界 | 每个关键结论有官方来源或明确标为待验证 |
| `docs/agent-skill/arch-iphone-remote-control.md` | 形成首篇实战稿 | 不夸大 Linux 支持，包含架构、前置条件、安全和验证清单 |

## 后续栏目

1. 入门：从最小 Profile 理解 Surge；
2. 规则：规则优先级、策略组和 Rule Match；
3. DNS：解析链路、Fake IP 与诊断；
4. 自动化：脚本、CLI 和 Agent Skill；
5. 远程：Surge iOS / tvOS 控制与局域网安全；
6. 排错：从日志、规则解释和 DNS trace 定位问题。

## 编辑原则

- 标注资料截止日期和 Surge 版本；
- 将“官方事实”“本文翻译”“作者推断”“尚未实测”分开；
- 命令示例必须说明执行端和目标端；
- 涉及远程控制时，默认采用最小权限、局域网限制和密码不入命令历史的做法。
