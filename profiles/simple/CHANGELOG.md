# profiles/simple changelog

渲染入口：`profiles/simple/surge-simple.conf`，VPS 只渲染这一份，路径不随版本变化。已发布版本的
快照在 `profiles/simple/version 1/<version>.conf`。设备订阅 URL 由 manifest 的 `output`
（`surge-simple.conf`）决定，升级和回滚都不需要改设备端 URL。

## 1.0.2 (2026-09-26)

- 金融规则置于 `cn.list` 之前，并直接绑定既有 `Proxy`；不新增策略组。moomoo 与富途域名同时存在于 `geosite:cn`，原顺序会使其先命中 `DIRECT`。

## 1.0.1 (2026-09-21)

- 将 `Smart` 从 `url-test` 改为 `smart`，按节点类型和区域组合标签进行优先级排列。
- 补齐固定标签顺序下的国家基准、国家与特殊标签组合及特殊标签兜底乘法；未命中规则的节点使用 `1.0`。

## 布局调整 (2026-09-10，不升版本)

- 入口文件由 `profiles/simple/1.0.0.conf` 改名为 `profiles/simple/surge-simple.conf`，与 manifest
  的 `output` 对齐；`version 1/1.0.0.conf` 是同一内容的快照，只差 `@status` 一行。
- `config/private-profile-templates.json` 的 `source` 与 `template_url` 同步指向新路径。正文、
  `@version`、`@changed` 均未改，设备订阅 URL 也不变，所以不另起 1.0.1。

## 1.0.0 (2026-09-09)

- 基线版本：由仓库顶层 `surge-simple.example.conf` 迁移为 `profiles/simple/1.0.0.conf`。
- 保持 DIRECT / Proxy / REJECT 三种最终结果，保留 Domestic / Apple / Others 手调组。
- 头部加入版本元数据（`@profile` / `@version` / `@status` / `@changed` / `@changelog`）。
