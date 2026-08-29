# 私有 DoH 备用端点

## 当前端点

数据日期：2026-08-30（Asia/Singapore）。以下端点已使用标准 DoH `GET` 查询
`example.com` 验证，返回 `HTTP 200` 与 `application/dns-message`。

| 位置 | DoH URL | 服务实现 |
|---|---|---|
| 美国 | `https://us.latexme.de:8443/dns-query` | 美国 DNS 服务 |
| misaka | `https://kixdns.latexme.de:8443/dns-query` | KixDNS 原生 DoH 监听 |

misaka 的原生 DoH 监听在 `8443`，并由 KixDNS 的证书同步单元在 ACME
证书更新后更新证书和重启 KixDNS。端点本身不含订阅、节点凭据或控制密钥，
可以记录在本仓库。

## 当前主 Profile 的决策

`surge-main.conf`、`profile.example.conf` 和 `surge-simple.example.conf`
故意**不**配置 `encrypted-dns-server`。日常解析继续使用各模板中现有的
传统 `dns-server` 列表。

这是当前使用决策，不表示 DoH 端点不可用。需要加密 DNS 时，建议创建单独的
手动 Profile 或本地覆盖，而不是直接修改日常主 Profile。

## 手动启用示例

在专用 Profile 的 `[General]` 中选择一个端点：

```ini
[General]
encrypted-dns-server = https://kixdns.latexme.de:8443/dns-query
```

美国端点则替换为：

```ini
encrypted-dns-server = https://us.latexme.de:8443/dns-query
```

同时配置多个 `encrypted-dns-server` 时，Surge 会并发查询这些服务器，
不是按书写顺序的故障切换。启用加密 DNS 后，传统 `dns-server` 主要用于
解析 DoH URL 的主机名与连通性探测，不是日常查询的顺序备用。

Surge 不能按当前手动选中的代理节点自动选择不同的 `encrypted-dns-server`。
如需让 DoH 请求本身遵循代理规则，可在专用 Profile 启用
`encrypted-dns-follow-outbound-mode = true`，并使用 `PROTOCOL,DOH` 规则；
这会影响该 Profile 的全部 DoH 请求。

语法与行为依据：[Surge General DNS 设置](https://manual.nssurge.com/profile/general.html)、
[DNS 并发查询说明](https://manual.nssurge.com/dns/overview.html) 和
[协议规则说明](https://manual.nssurge.com/rules/protocol-and-network.html)。
