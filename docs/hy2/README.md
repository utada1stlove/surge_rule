# Hysteria 2 运维文档

本文档记录本项目两台 VPS 上 Hysteria 2（以下简称 hy2）的部署结构、用户管理、流量统计、ACL、安全边界和故障排查方法。

## 当前状态

数据核对日期：2026-09-05。

| 主机别名 | hy2 版本 | 主监听 | TLS/SNI 域名 | 用户认证 | 统计页面 |
|---|---|---|---|---|---|
| `eb` | v2.12.0 | UDP `443` | 服务器证书中的域名 | `userpass` | <https://eb.latexme.de/hy2-stats/> |
| `cn2` | v2.12.0 | UDP `30000-30199`（端口跳跃） | 服务器证书中的域名 | `userpass` | <https://us.latexme.de/hy2-stats/> |

真实密码、API Secret、私钥和完整客户端链接不写入 Git。需要操作时通过服务器上的受限文件读取，不要复制到仓库、工单或聊天记录。

## 文档索引

- [架构与配置](architecture.md)：服务、端口、认证和请求路径；
- [用户与链接管理](users.md)：`userpass` 用户的新增、停用和客户端链接规则；
- [流量统计](monitoring.md)：原生 API、持久化采集器和单位换算；
- [ACL 与安全](acl-security.md)：拒绝中国大陆目标流量的规则和边界；
- [运维与排错](operations.md)：备份、校验、重启、回滚和常见故障。

## 官方资料

- [Full Server Config](https://hysteria.network/docs/advanced/Full-Server-Config/)
- [Traffic Stats API](https://hysteria.network/docs/advanced/Traffic-Stats-API/)
- [ACL](https://hysteria.network/docs/advanced/ACL/)
- [URI Scheme](https://hysteria.network/docs/developers/URI-Scheme/)

官方语法和行为以 Hysteria 官方文档及服务器实际版本为准。
