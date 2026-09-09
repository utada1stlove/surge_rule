# profiles/home-wg changelog

版本文件：`profiles/home-wg/<version>.conf`。设备订阅 URL 由 manifest 的 `output`
决定，版本升级不需要改设备端 URL。

## 1.0.0 (2026-09-09)

- 基线版本：由仓库顶层 `surge-home-wg.example.conf` 迁移为 `profiles/home-wg/1.0.0.conf`。
- 保留 WireGuard 回家链路；`__WG_*__` 占位符只由私有渲染服务在 secrets.json 中注入。
- 头部加入版本元数据（`@profile` / `@version` / `@status` / `@changed` / `@changelog`）。
