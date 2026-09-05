# ACL 与安全

## 拒绝中国大陆目标

两台服务器当前都有：

```yaml
acl:
  inline:
    - reject(geoip:cn)
```

规则按从上到下匹配。`geoip:cn` 匹配目标解析后的中国大陆 IP，命中后使用内置 `reject` outbound 拒绝连接；其他目标继续使用默认 outbound。该规则同时适用于 TCP 和 UDP。

## 规则边界

这不是“只允许境外域名”的绝对名单，而是基于 GeoIP 的目标 IP 判断：

- 中国网站使用境外 CDN 时可能仍可访问；
- 境外网站使用中国大陆 CDN 时可能被拒绝；
- GeoIP 数据库可能存在延迟或误判；
- 规则只处理经过 hy2 的代理请求，不限制 VPS 自身的 SSH、系统更新或其他本机进程；
- DNS 解析结果、IPv4/IPv6 选择和目标 CDN 会影响最终匹配。

hy2 会在需要时下载 GeoIP 数据库并缓存到工作目录；数据库通常在服务启动时加载，更新后需要重启 hy2 才会生效。

## 统计 API 暴露边界

Nginx 公开的统计页面只代理：

- `GET /hy2-stats-api/online`；
- `GET /hy2-stats-api/traffic`；
- `GET /hy2-stats-api/traffic-total`。

未知的 `/hy2-stats-api/` 路径返回 404，`/kick` 不会被代理。hy2 API Secret 保存在 `/etc/hy2-stats/collector.env`，权限为 `600`，不写入网页源码。

公开统计仍会暴露用户名、在线设备数和流量规模；这是有意的产品选择。如果以后需要隐藏这些信息，应给网页加认证或改为仅内网访问。

## 变更安全原则

- 不把密码、Secret、私钥或完整链接写入 Git；
- 不把 hy2 API 直接绑定到公网；
- 任何远程写入前先备份配置；
- 修改后先执行配置测试，再重启单个服务；
- 保留 SSH 管理路径和可回滚备份；
- 不把 `POST /kick`、配置文件或 systemd 管理接口公开给浏览器。
