# Surge 文档总览

这套文档面向使用 Surge iPhone、希望把规则放到 GitHub 中长期维护的用户。目标不是提供一份“万能规则”，而是建立一套可理解、可审查、可回滚的配置体系。

## 推荐阅读路径

1. [iPhone 入门配置](getting-started/iphone-setup.md)：安装 Profile、启动 Surge、确认流量接管；
2. [规则与策略组](rules/profile-and-rules.md)：理解节点、策略组和规则之间的关系；
3. [GitHub 维护流程](operations/github-maintenance.md)：把公开规则拆分、发布和更新；
4. [Sub-Store 单链接方案](operations/substore-one-link.md)：把私有节点和公开规则合成一个 Surge 输出链接；
5. [私有 DoH 备用端点](operations/private-doh.md)：记录可手动启用的自建 DoH 地址与使用边界；
6. [安全与隐私](security.md)：确认哪些内容可以公开；
7. [排错手册](troubleshooting.md)：从状态、请求列表、DNS 和规则命中结果定位问题。
8. [Surge 外部资料知识库](knowledge-base/surge-resources.md)：归档待评估的社区资料、配置参考与图标集。

## 这套体系解决什么问题

```text
公开规则 ──┐
公开模板 ──┼──> GitHub 版本管理 ──> Surge iPhone 自动更新
个人节点 ──┘       （不公开凭据）
```

- 规则修改有历史记录；
- 可以只更新规则，不暴露节点信息；
- 可以通过 GitHub Issue 或提交记录解释变更原因；
- 出现问题时可以回滚到上一个提交；
- 同一套规则可以被多个 Profile 复用。

## 事实与假设

本文档基于 Surge 官方手册截至 2026-08-28 的内容。具体菜单名称、版本要求和可用协议可能随 Surge iOS 更新变化；涉及真实节点和远程 Controller 的部分，必须以本地版本实际显示为准。

官方资料：[Surge 手册](https://manual.nssurge.com/)、[Quick Start](https://manual.nssurge.com/getting-started/quick-start.html)、[Profile Format](https://manual.nssurge.com/profile/format.html)。

## 不包含的内容

- 不提供代理节点或订阅；
- 不公开任何第三方节点凭据；
- 不承诺 Arch Linux 原生运行官方 `surge-cli`；
- 不把第三方规则集未经审查地合并进主 Profile；
- 不建议将 Controller 端口暴露到公网。
