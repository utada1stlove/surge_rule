# Surge iPhone 入门配置

## Surge 是什么

Surge iPhone 通过 Network Extension 接管设备网络，再按照 Profile 中的规则决定每个请求是直连、代理还是拒绝。Profile 是一份文本配置，通常由 `[General]`、`[Proxy]`、`[Proxy Group]` 和 `[Rule]` 等部分组成。

Surge 不是代理节点提供商。你需要自己拥有可用的代理服务，或者使用可信服务商提供的订阅。

## 开始前准备

- 已购买并安装 Surge iPhone；
- 一个可用的代理节点或订阅；
- 明确哪些流量需要代理、哪些流量应该直连；
- 一个用于保存公开规则的 GitHub 仓库；
- 不准备把节点密码、订阅链接或私钥提交到公开仓库。

## 最小 Profile

下面的示例只用于理解结构。`proxy.example.com`、`username` 和 `password` 都是占位符，不能直接使用。

```ini
[General]
dns-server = system, 1.1.1.1

[Proxy]
MyProxy = https, proxy.example.com, 443, username, password

[Proxy Group]
Proxy = select, MyProxy, DIRECT

[Rule]
DOMAIN-SUFFIX,example.com,Proxy
GEOIP,CN,DIRECT
FINAL,DIRECT
```

Surge 按 `[Rule]` 从上到下匹配，第一条匹配的规则决定策略；没有匹配的请求由 `FINAL` 处理。[Rules Overview](https://manual.nssurge.com/rules/overview.html)

## 字段怎么理解

### `[General]`

全局设置，例如 DNS、日志级别、网络接管行为。刚开始只需要保留必要设置，不要一次启用 MITM、脚本和大量实验参数。

### `[Proxy]`

定义代理策略。每个策略至少需要名称、协议、服务器和端口；某些协议还需要用户名、密码、密钥或其他参数。[Policies Overview](https://manual.nssurge.com/policies/overview.html)

### `[Proxy Group]`

给多个策略建立一个稳定名称。规则引用 `Proxy` 这个组后，你可以在 App 中切换节点，而不用修改每一条规则。

常见组类型：

- `select`：手动选择；
- `url-test`：按测试结果选择；
- `fallback`：按顺序使用可用策略；
- `load-balance`：在多个策略间分配请求。

### `[Rule]`

把匹配条件映射到策略。例如：

```ini
[Rule]
DOMAIN-SUFFIX,github.com,Proxy
DOMAIN-SUFFIX,internal.example,DIRECT
IP-CIDR,192.168.0.0/16,DIRECT
FINAL,DIRECT
```

规则类型很多，最常用的是 `DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-KEYWORD`、`IP-CIDR`、`GEOIP`、`RULE-SET` 和 `FINAL`。

## 第一次验证

1. 在 Surge 中导入或安装 Profile；
2. 检查 Profile 是否成功加载；
3. 启动 Surge 的网络接管；
4. 打开请求列表，确认请求被捕获；
5. 检查某个域名的匹配规则和最终策略；
6. 分别测试一个应代理、一个应直连的目标。

如果最小 Profile 可以工作，再逐步加入远程规则、DNS、自定义脚本和 MITM。
