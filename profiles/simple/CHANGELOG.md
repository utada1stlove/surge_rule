# profiles/simple changelog

版本文件：`profiles/simple/<version>.conf`。设备订阅 URL 由 manifest 的 `output`
决定，版本升级不需要改设备端 URL。

## 1.0.0 (2026-09-09)

- 基线版本：由仓库顶层 `surge-simple.example.conf` 迁移为 `profiles/simple/1.0.0.conf`。
- 保持 DIRECT / Proxy / REJECT 三种最终结果，保留 Domestic / Apple / Others 手调组。
- 头部加入版本元数据（`@profile` / `@version` / `@status` / `@changed` / `@changelog`）。
