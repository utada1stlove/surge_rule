# 流量统计

## 原生 API

hy2 的 Traffic Stats API 提供：

- `GET /online`：用户到在线客户端实例数的映射；
- `GET /traffic`：用户到 `tx`/`rx` 字节数的映射；
- `POST /kick`：按用户 ID 踢出客户端，不对外公开。

当前 API 只监听 `127.0.0.1:19999`。通过 SSH 隧道查询示例：

```bash
ssh -N -L 19999:127.0.0.1:19999 eb
curl -H 'Authorization: API_SECRET' http://127.0.0.1:19999/online
curl -H 'Authorization: API_SECRET' http://127.0.0.1:19999/traffic
```

`tx` 和 `rx` 的单位是 bytes：`tx` 代表客户端上传，`rx` 代表客户端下载。`/online` 的数值代表客户端实例/设备数。

## 持久化统计

原生 `/traffic` 计数保存在 hy2 进程内存中，重启后会归零。两台服务器已安装独立的 systemd timer：

```text
hy2-stats-collector.timer
  └─ 每 60 秒运行 hy2-stats-collector.service
```

采集器读取本机 `/traffic`，计算与上次采样的增量，累计保存到：

```text
/var/www/html/hy2-stats/traffic-total.json
```

网页读取 `/hy2-stats-api/traffic-total`，因此 hy2 重启不会清空网页累计值。采集器检测到计数器回零时，会把当前值作为新一段增量。正常情况下最多有约 60 秒延迟，突然断电可能丢失最后一个采样周期。

## 单位换算

网页使用十进制单位：

```text
1 KB = 1,000 bytes
1 MB = 1,000,000 bytes
1 GB = 1,000,000,000 bytes
```

例如 `345,454,394` bytes 约为 `345.45 MB`，不是 `345 GB`。如果直接访问 API JSON，看到原始 bytes 是正常的；格式化只发生在统计网页中。

## 资源占用

采集器不是常驻高负载进程，每分钟只执行一次短暂 HTTP 请求和一次小 JSON 原子写入，CPU、内存和磁盘开销都很低。累计文件应保持为公开统计数据，不要在其中写入密码或 API Secret。
