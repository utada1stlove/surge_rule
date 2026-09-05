# 架构与配置

## 服务结构

两台 VPS 都运行一个 systemd 服务：

```text
hysteria-server.service
  └─ /usr/local/bin/hysteria server --config /etc/hysteria/config.yaml
```

配置文件路径固定为 `/etc/hysteria/config.yaml`。服务用户为 `hysteria`，配置中的 TLS 私钥仅由该服务读取。

Nginx 与 hy2 可以同时使用 TCP/UDP `443`：Nginx 处理 TCP HTTPS，hy2 处理 UDP QUIC。`cn2` 的 `30000-30199` 是 hy2 的端口跳跃范围，实际首端口由 hy2 监听并由端口跳跃规则转发。

## 配置骨架

下面是去除真实凭据后的结构示例：

```yaml
listen: :443
bandwidth:
  up: 1000 mbps
  down: 1000 mbps
tls:
  cert: /etc/hysteria/tls/fullchain.pem
  key: /etc/hysteria/tls/privkey.pem
auth:
  type: userpass
  userpass:
    user_a: password_a
    user_b: password_b
trafficStats:
  listen: 127.0.0.1:19999
  secret: replace_with_secret
acl:
  inline:
    - reject(geoip:cn)
masquerade:
  type: proxy
  proxy:
    url: https://www.bing.com
    rewriteHost: true
```

`cn2` 只将 `listen` 改为 `0.0.0.0:30000-30199`，其余结构相同。

## 请求路径

```text
客户端
  │ hysteria2:// 用户名:密码@主机:端口/?sni=...
  ▼
hy2 QUIC 服务
  ├─ auth.userpass：验证用户
  ├─ acl：按顺序匹配目标并决定 reject/direct
  └─ trafficStats：记录用户 ID 的流量与在线设备数
```

统计 API 绑定在本机 `127.0.0.1:19999`，Nginx 仅代理公开的只读接口。网页不包含 API Secret。

## 带宽含义

服务端 `bandwidth` 是 hy2 的 Brutal 速率上限，方向按客户端视角理解：服务端发送对应客户端接收。它不是 VPS 供应商账单，也不是跨用户总配额；实际总吞吐仍受 VPS、链路和拥塞影响。
