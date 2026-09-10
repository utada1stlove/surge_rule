# profiles/simple changelog

渲染入口：`profiles/simple/surge-simple.conf`，VPS 只渲染这一份，路径不随版本变化。已发布版本的
快照在 `profiles/simple/version 1/<version>.conf`。设备订阅 URL 由 manifest 的 `output`
（`surge-simple.conf`）决定，升级和回滚都不需要改设备端 URL。

## 布局调整 (2026-09-10，不升版本)

- 入口文件由 `profiles/simple/1.0.0.conf` 改名为 `profiles/simple/surge-simple.conf`，与 manifest
  的 `output` 对齐；`version 1/1.0.0.conf` 是同一内容的快照，只差 `@status` 一行。
- `config/private-profile-templates.json` 的 `source` 与 `template_url` 同步指向新路径。正文、
  `@version`、`@changed` 均未改，设备订阅 URL 也不变，所以不另起 1.0.1。

## 1.0.0 (2026-09-09)

- 基线版本：由仓库顶层 `surge-simple.example.conf` 迁移为 `profiles/simple/1.0.0.conf`。
- 保持 DIRECT / Proxy / REJECT 三种最终结果，保留 Domestic / Apple / Others 手调组。
- 头部加入版本元数据（`@profile` / `@version` / `@status` / `@changed` / `@changelog`）。
