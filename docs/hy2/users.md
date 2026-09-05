# 用户与链接管理

## 原生多用户

hy2 原生支持 `userpass`，用户名和密码以映射形式保存：

```yaml
auth:
  type: userpass
  userpass:
    lacusclyne: existing_password
    another_user: another_password
```

每个用户名会成为统计 API 中的客户端 ID。多个设备可以同时使用同一用户，但在线设备数会分别计数。

## 新增用户流程

1. 生成高熵随机密码，不使用姓名、域名或重复密码；
2. 在目标服务器备份 `/etc/hysteria/config.yaml`；
3. 只修改 `auth.userpass`，保留其他配置；
4. 重启 `hysteria-server.service`；
5. 检查服务状态、监听端口和启动日志；
6. 为用户生成新的 `hysteria2://` 链接；
7. 在客户端导入并验证 TCP/UDP 代理。

## 链接格式

官方 URI 格式为：

```text
hysteria2://username:password@hostname:port/?sni=hostname#display-name
```

用户名或密码含特殊字符时必须进行 URL 编码。端口跳跃范围可以写在端口位置，例如：

```text
hysteria2://username:password@example.invalid:30000-30199/?sni=example.invalid#cn2-user
```

不要把真实链接提交到 Git 或公开文档。旧的单密码链接在服务器切换到 `userpass` 后需要改成带用户名的新格式，即使密码本身没有变化。

## 停用或轮换

- 停用单个用户：从 `userpass` 映射中删除该用户，然后重启 hy2；
- 轮换单个密码：只替换该用户的密码，其他用户不受影响；
- 怀疑泄露：立即轮换，不要只依赖删除聊天记录；
- 轮换后重新生成客户端链接，并确认旧链接无法连接。

## 注意事项

- 用户名区分大小写，建议使用稳定的 ASCII 名称；
- 同一用户名共享给多台设备时，统计无法区分具体设备的流量；
- `online` 的数字是客户端实例/设备数，不是活动连接数；
- 用户认证成功不代表目标一定可访问，ACL 仍会继续处理目标地址。
