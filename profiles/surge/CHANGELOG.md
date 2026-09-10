# profiles/surge changelog

渲染入口：`profiles/surge/surge.conf`，VPS 只渲染这一份，路径不随版本变化。已发布版本的
快照在 `profiles/surge/version 1/<version>.conf`。设备订阅 URL 由 manifest 的 `output`
决定，升级和回滚都不需要改设备端 URL。

## 1.0.2 (2026-09-10)

- 图标改回 PNG 交付：`Smart` 由 `policy/speed-slow-svgrepo-com.svg` → `policy/speed.png`，
  `Boom` 由 `policy/cloudflare-color.svg` → `policy/cloudflare-color.png`。1.0.1 记的「真机是否支持
  SVG」不确定性随之取消，`.svg` 退回可编辑源文件；`Proxy` 组沿用 1.0.1 的 `policy/Surge.png`。
- 换图：`Domestic` 由 Qure `policy/domestic.png` → `policy/china.png`，`HomeProxy` 由
  `policy/home.png` → `policy/home-wifi.png`（深蓝房形底 + 白色 Wi-Fi，明暗模式都读得清）。
  `profiles/simple/1.0.0.conf`、`legacy/`、`archive/` 仍用 `domestic.png` 与 `home.png`。
- 新增素材统一压到 144x144：`speed.png` 从 2500x2500 / 172KB 降到 8.9KB，`china.png` 3.0KB、
  `cloudflare-color.png` 3.0KB、`home-wifi.png` 4.9KB。`icon-url` 每次刷新都要重新下载，尺寸直接
  变成设备流量；144 是推荐尺寸而非硬限制，见 `assets/icons/policy/README.md`。
- 素材整理：SVG Repo 的 72x72 / 216x216 副本、三张未采用的单色线稿候选（打字机、报刊、行情屏）
  以及 `services/cloudflare-color.svg` 逐字节重复的副本移入 `legacy/icons/` 冻结，登记在
  `legacy/README.md`；`assets/icons/policy/` 只留每个在用图标的一档发布尺寸加可编辑 `.svg`。
- 版本链路修复（1.0.1 遗留）：`config/private-profile-templates.json` 的 `source` 与 `template_url`
  指向 `profiles/surge/surge.conf`；`tools/check-profile-versions.py` 与 `tools/lint_surge_profiles.py`
  改为接受「入口文件路径稳定 + `version N/` 快照」的布局——入口文件名不再要求等于 `@version`，
  快照必须 `@status: superseded` 且不进 manifest，3 版本上限按去重后的版本号计数，快照不再被
  `rglob` 误当成待渲染的 Profile。`tools/test-check-profile-versions.py` 补 5 个用例。VPS 拉模板
  404、设备停在 1.0.0 的问题到此解决。
- 快照状态：`version 1/` 下 1.0.0 / 1.0.1 / 1.0.2 三份 `@status` 改为 `superseded`，渲染入口
  `surge.conf` 是本家族唯一的 `active`。快照与入口文件只差这一行。
- 只动图标：策略组成员与候选顺序、`policy-regex-filter`、`[Rule]` 段与 1.0.1 相同，回滚只需把
  `version 1/1.0.1.conf` 复制回 `surge.conf` 并把 `@status` 写回 `active`。
- 未发布过：1.0.2 期间 manifest 一直指向已移走的 `profiles/surge/1.0.0.conf`，VPS 没有成功渲染过
  任何一份 1.0.1 之后的输出，所以图标尺寸与 `HomeProxy` 改动直接并入 1.0.2，不另起 1.0.3。
- 已知问题：`china.png` 是纯 `#000000` 中国地图剪影、透明底，在 Surge 深色列表里几乎不可见，
  与仓库曾因同样原因移进 `archive/icons/` 的两张 `*-brands-solid-full.svg` 单色图同一毛病。
  待办：给它上色（描边或改填充色），或 `Domestic` 组回退 Qure `domestic.png`。

## 1.0.1 (2026-09-10)

- 三个组换上专属图标（此前共用 `assets/icons/policy/proxy.png`）：`Proxy` → `policy/Surge.png`，
  `Smart` → `policy/speed-slow-svgrepo-com.svg`，`Boom` → `policy/cloudflare-color.svg`。
- 新增本地图标资源：`policy/Surge.png`（144x144）、`policy/cloudflare-color.svg`、
  `services/cloudflare-color.svg`、`policy/speed-slow-svgrepo-com.svg`，另存下三个尚未被 Profile
  引用的候选图标（`antique-characters-machine`、`bulletin-journal-magazine`、`dollar-finance-money-29`）。
- 只动图标：策略组成员与候选顺序、`policy-regex-filter`、`[Rule]` 段与 1.0.0 完全相同，
  回滚只需把 manifest 的 `source` 切回 1.0.0。
- 待真机确认：`Smart` 与 `Boom` 首次把 `icon-url` 指向 `.svg`，而 `assets/icons/services/README.md`
  记的既有约定是 Surge 官方只示例 `.png`、本仓库一律以 PNG 交付；必要时用 `rsvg-convert` 渲成
  144x144 PNG 再引用。
- 文件布局：活动文件由 `profiles/surge/1.0.0.conf` 改名为 `profiles/surge/surge.conf`，
  `1.0.0.conf` 与 `1.0.1.conf` 移入 `profiles/surge/version 1/`。`config/private-profile-templates.json`
  的 `source` 仍指向已移走的 `profiles/surge/1.0.0.conf`，`tools/check-profile-versions.py`、
  `tools/check-private-profile-templates.py` 与 VPS 模板拉取都会因此失败；设备端订阅名
  （manifest `output` = `surge.conf`）不变。上述断链与校验失败已在 1.0.2 修复。
- 头部 `@changed` 更新为 2026-09-10。

## 1.0.0 (2026-09-09)

- 基线版本：由仓库顶层 `surge.conf` 迁移为 `profiles/surge/1.0.0.conf`，规则与策略组行为不变。
- 修正图标 404：PayPal、Twitter 等组改用仓库本地资产。
- 解除 Twitter / Reddit 前置遮蔽：改为各自的带图标 `select` 组，默认项 HomeProxy，
  默认出口与改动前一致。
- 头部加入版本元数据（`@profile` / `@version` / `@status` / `@changed` / `@changelog`）。
