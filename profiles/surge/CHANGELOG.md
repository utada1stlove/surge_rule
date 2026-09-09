# profiles/surge changelog

版本文件：`profiles/surge/<version>.conf`。设备订阅 URL 由 manifest 的 `output`
决定，版本升级不需要改设备端 URL。

## 1.0.0 (2026-09-09)

- 基线版本：由仓库顶层 `surge.conf` 迁移为 `profiles/surge/1.0.0.conf`，规则与策略组行为不变。
- 修正图标 404：PayPal、Twitter 等组改用仓库本地资产。
- 解除 Twitter / Reddit 前置遮蔽：改为各自的带图标 `select` 组，默认项 HomeProxy，
  默认出口与改动前一致。
- 头部加入版本元数据（`@profile` / `@version` / `@status` / `@changed` / `@changelog`）。
