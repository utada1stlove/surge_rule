# Legacy（冻结配置）

`legacy/` 保存已经退出版本线、不再由私有渲染服务输出的配置，以及不再被任何 Profile
引用的图标素材（`legacy/icons/`）。文件仍留在仓库供查阅，但行为不再演进，也不作为
设备订阅 URL 或 `icon-url` 的源文件。

## 约定

- 每份 `.conf` 带 `# @status: frozen` 和 `# @frozen-at`；
- 不进入 `config/private-profile-templates.json`，`tools/check-profile-versions.py`
  会拦截指向 `legacy/` 的 manifest 引用；
- 不参与 VPS 渲染，`surge-profilectl update` 不会再从这些文件生成输出；
- 继续被 `tools/lint_surge_profiles.py` 扫描，防止公开坏链、结构错误和疑似凭据；
- 只允许安全修复和坏链修复，不做行为变更；需要新行为时在 active 家族中新建版本。

`legacy/icons/` 的约定：

- 只放冻结的图片与 SVG 源文件，不放 `.conf`，因此不参与配置结构校验；
- 每个条目在下表登记冻结日期与原因，原文件名保持不变，需要复用时按原路径取回；
- 与 `archive/icons/` 的区别：`archive/` 放仓库自己渲染出错、已经废弃的产物，
  `legacy/icons/` 放图形本身没问题、只是当前版本没有采用的素材（多余尺寸副本、候选图标）。

## 清单

| 文件 | 冻结日期 | 说明 |
| --- | --- | --- |
| `profile.example.conf` | 2026-09-09 | 手写样板，无托管声明，只作阅读参考 |
| `surge-main.conf` | 2026-09-09 | 多策略组配置，之前对应私有服务的 `surge-main.conf` 输出 |
| `surgeion.conf` | 2026-09-09 | 多策略组 + 手动出口 `select` 配置，之前对应 `surgeion.conf` 输出 |

## 冻结图标素材

| 文件 | 冻结日期 | 说明 |
| --- | --- | --- |
| `antique-characters-machine*`（`.svg` + 72/144/216 PNG） | 2026-09-10 | SVG Repo 候选图标，根节点 `fill="#000000"` 单色线稿，深色模式下几乎不可见，未采用 |
| `bulletin-journal-magazine*`（`.svg` + 72/144/216 PNG） | 2026-09-10 | 同上，报刊图形单色线稿，未采用；`Finance` 组沿用 `services/reuters.png` |
| `dollar-finance-money*`（`.svg` + 72/144/216 PNG） | 2026-09-10 | 同上，行情屏单色细线稿，小尺寸下线条过细，未采用 |
| `china-1-svgrepo-com.png`、`china-1-svgrepo-com@3x.png` | 2026-09-10 | `policy/china.png` 的 72x72 与 216x216 副本；发布尺寸统一 144x144，源 SVG 留在 `assets/icons/policy/` |
| `speed-slow-svgrepo-com.png`、`speed-slow-svgrepo-com@3x.png` | 2026-09-10 | `policy/speed.png` 的 72x72 与 216x216 副本，理由同上 |
| `home-wifi-svgrepo-com.png`、`home-wifi-svgrepo-com@3x.png` | 2026-09-10 | `policy/home-wifi.png` 的 72x72 与 216x216 副本，理由同上 |
| `cloudflare-color@3x.png` | 2026-09-10 | `policy/cloudflare-color.png` 的 216x216 副本，理由同上 |
| `cloudflare-color.svg` | 2026-09-10 | 原 `assets/icons/services/cloudflare-color.svg`，与 `assets/icons/policy/cloudflare-color.svg` 逐字节相同，去重后保留 policy 一份 |

## 与 archive 的区别

- `legacy/`：仍然保留完整公开结构的冻结配置，继续参与公开结构校验；
- `archive/`：旧版本快照与历史文件，只作追溯，见 [archive 说明](../archive/README.md)。

版本契约与回滚流程见 [Profile 版本化](../docs/operations/profile-versioning.md)。
