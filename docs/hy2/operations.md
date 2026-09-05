# 运维与排错

## 常用只读检查

```bash
ssh eb systemctl is-active hysteria-server.service
ssh eb ss -lunp | grep hysteria
ssh eb journalctl -u hysteria-server.service -n 50 --no-pager

ssh cn2 systemctl is-active hysteria-server.service
ssh cn2 ss -lunp | grep hysteria
ssh cn2 journalctl -u hysteria-server.service -n 50 --no-pager
```

统计采集器：

```bash
ssh eb systemctl status hy2-stats-collector.timer --no-pager
ssh eb systemctl status hy2-stats-collector.service --no-pager
ssh cn2 systemctl status hy2-stats-collector.timer --no-pager
```

## 配置变更流程

1. 确认目标主机、配置路径和预计影响；
2. 备份 `/etc/hysteria/config.yaml` 到服务器受限目录；
3. 只编辑所需字段；
4. 检查 YAML 结构和敏感字段权限；
5. 重启 `hysteria-server.service`；
6. 检查 `active (running)`、监听端口和最新日志；
7. 用客户端或 API 做功能验证。

Hysteria CLI 没有独立的“只解析 YAML 不监听端口”通用模式，实际验证通常以 systemd 重启后的启动日志和监听状态为准。不要在生产端口上启动第二个临时实例做测试。

## 回滚

发现服务启动失败或客户端全部无法连接时：

```bash
cp /root/<backup>/config.yaml /etc/hysteria/config.yaml
systemctl restart hysteria-server.service
systemctl is-active hysteria-server.service
```

实际备份文件名以服务器操作记录为准。回滚后仍需检查端口、ACL 和用户链接，不要删除工作配置或备份直到验证完成。

## 常见故障

### `traffic stats ... address already in use`

统计 API 端口被其他服务占用时，hy2 可能启动失败。先查占用者：

```bash
ss -lntp | grep 19999
```

不要停止不相关服务。选择空闲的本机端口，修改 `trafficStats.listen`、采集器环境文件和 Nginx 代理目标，然后按配置变更流程验证。

### 页面显示原始数字

直接访问 API 会返回 bytes，这是正常行为。应访问 `/hy2-stats/` 页面；如果页面缓存旧脚本，执行浏览器强制刷新。确认页面单位换算包含 `B, KB, MB, GB, TB`，不能跳过 `KB`。

### 统计重启后归零

确认 `hy2-stats-collector.timer` 为 `active`、采集器服务最近一次运行成功，并检查 `traffic-total.json` 的更新时间。原生 `/traffic` 归零不等于持久化累计值丢失。

### 中国大陆网站仍可访问

确认请求确实经过 hy2，检查目标最终解析 IP 和 GeoIP 数据库更新时间。`reject(geoip:cn)` 是 IP 地理归属规则，不是域名黑名单；境外 CDN、IPv6 和数据库误差都可能造成结果差异。

### 用户链接无法连接

检查用户名、URL 编码、SNI、端口和端口跳跃范围。切换到 `userpass` 后，旧的单密码 URI 不再适用。不要在排错日志中打印完整链接或密码。
