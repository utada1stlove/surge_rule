# profiles/surge-loc changelog

渲染入口：`profiles/surge-loc/surge-loc.conf`，VPS 只渲染这一份，路径不随版本变化。已发布版本的快照在 `profiles/surge-loc/version 1/<version>.conf`。设备订阅 URL 由 manifest 的 `output` 决定，升级和回滚都不需要改设备端 URL。

## 1.0.2 (2026-09-25)

- `Pixiv` 组图标同步改用 `services/pixiv.png`

## 1.0.1 (2026-09-25)

- `vendor` 18 源去重后接入：远端下载后与 `diy` + `geosite`（`rules/generated`）对比，去除已在本地权威的 1259 条（`google` 615/ `fox` 240/ `paypal` 244 等），输出 `rules/vendor/*.deduped.list` 并由 `surge-loc` 引用

## 1.0.0 (2026-09-25)

- 平行于 `surge` 主线，18 个远端 Rule Set 已本地化至 `rules/vendor/*.list`（`facebook/instagram/whatsapp/spotify/github/telegram/twitch/discord/twitter/reddit/google/gemini/openai/anthropic/claude/paypal/fox/tiktok`），由 `sync-external` 每日同步
- 复用 `surge` 1.3.5 的策略组与 `Pixiv` 本地化，保持 `Smart` 优先与去重审计
