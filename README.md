# Surge 规则与配置

这是一个用于学习和维护 Surge iPhone 规则、Profile 模板和脚本的公开仓库。

## 文档入口

- [三路简洁配置模板](surge-simple.example.conf)
- [文档总览](docs/README.md)
- [iPhone 入门配置](docs/getting-started/iphone-setup.md)
- [规则与策略组](docs/rules/profile-and-rules.md)
- [GitHub 维护流程](docs/operations/github-maintenance.md)
- [Sub-Store 单链接方案](docs/operations/substore-one-link.md)
- [VPS 私有 Profile 服务](docs/operations/private-profile-service.md)
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
profile.example.conf       # 多策略组 Profile 模板
surge-simple.example.conf  # DIRECT / Proxy / REJECT 简洁模板
rules/
  direct.list           # 直连规则
  proxy.list            # 通用代理候选规则
  reject.list           # 拦截规则（保守留空）
```

## 简洁配置

如果不需要按地区或服务拆分策略组，使用 `surge-simple.example.conf`。它只有三种处理结果：

- 国内及明确直连规则使用 `DIRECT`；
- 广告及明确拦截规则使用 `REJECT`；
- 其余流量进入唯一的 `Proxy` 策略组。

`Proxy` 通过 `policy-path` 加载 Sub-Store 输出的多个节点，你可以在 Surge 中手动切换。使用前只需把模板中的示例订阅地址替换为自己的私有链接；不要把替换后的个人配置提交到公开仓库。

## 在 Surge 中使用规则

Sub-Store 负责生成和更新节点；这份仓库只负责公开规则。先在 Surge 中创建或导入主 Profile，再在 `[Rule]` 中引用 Raw 文件：

```ini
[Rule]
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/direct.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy.list,Proxy
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/reject.list,REJECT
FINAL,DIRECT
```

将 `USER/REPO` 替换为实际的 GitHub 用户名和仓库名。规则文件只声明匹配条件，不在每一行重复策略名称；策略由主 Profile 中的 `RULE-SET` 行指定。

## 使用方式

1. 在 Sub-Store 中生成 Surge 格式的节点订阅；
2. 复制 `profile.example.conf`，将 `policy-path` 替换为自己的 Sub-Store Surge 输出链接；
3. 在 Surge 中安装这份主 Profile；
4. 按需编辑 `rules/` 下的规则文件；
5. 在 Surge 中检查 Profile 和请求列表；
6. 提交 Git 后，Surge 会在更新 Rule Set 时获取新的规则；节点则按 `policy-path` 的更新周期刷新。

规则按 Surge 从上到下、首条匹配生效的逻辑组织；主 Profile 应保留 `FINAL` 规则。[Surge 规则文档](https://manual.nssurge.com/rules/overview.html)

## 设计原则

- 规则与个人节点分离；
- 每个规则文件只承担一种意图；
- 规则变更写清原因；
- 先小范围修改，再观察命中结果；
- 不把 GitHub 当作秘密存储。
