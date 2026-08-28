# Surge 规则与配置

这是一个用于学习和维护 Surge iPhone 规则、Profile 模板和脚本的公开仓库。

## 文档入口

- [文档总览](docs/README.md)
- [iPhone 入门配置](docs/getting-started/iphone-setup.md)
- [规则与策略组](docs/rules/profile-and-rules.md)
- [GitHub 维护流程](docs/operations/github-maintenance.md)
- [Sub-Store 单链接方案](docs/operations/substore-one-link.md)
- [安全与隐私](docs/security.md)
- [排错手册](docs/troubleshooting.md)

## 公开与私有的边界

本仓库只存放可公开复用的内容：

- 规则文件；
- 不含真实凭据的 Profile 模板；
- 配置说明和变更记录；
- 不含个人密钥的脚本或模块。

以下内容不要提交到公开仓库：

- 节点订阅链接、节点密码和 Token；
- WireGuard 私钥、Snell PSK 及其他密钥；
- Surge Controller 密钥；
- MITM 私钥和证书；
- 个人内网地址、设备信息或日志。

## 目录

```text
profile.example.conf   # 主 Profile 模板，不含真实节点
rules/
  direct.list           # 直连规则
  proxy.list            # 通用代理候选规则
  reject.list           # 拦截规则（保守留空）
```

## 在 Surge 中使用规则

将仓库发布到 GitHub 后，可以在 Profile 中引用 Raw 文件：

```ini
[Rule]
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/direct.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy.list,Proxy
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/reject.list,REJECT
FINAL,DIRECT
```

将 `USER/REPO` 替换为实际的 GitHub 用户名和仓库名。规则文件只声明匹配条件，不在每一行重复策略名称；策略由主 Profile 中的 `RULE-SET` 行指定。

## 使用方式

1. 复制 `profile.example.conf`，填入自己的节点信息；
2. 按需编辑 `rules/` 下的规则文件；
3. 先使用 Surge 的 Profile 检查或请求列表验证变更；
4. 确认无误后提交 Git，并等待 Surge 更新远程规则。

规则按 Surge 从上到下、首条匹配生效的逻辑组织；主 Profile 应保留 `FINAL` 规则。[Surge 规则文档](https://manual.nssurge.com/rules/overview.html)

## 设计原则

- 规则与个人节点分离；
- 每个规则文件只承担一种意图；
- 规则变更写清原因；
- 先小范围修改，再观察命中结果；
- 不把 GitHub 当作秘密存储。
