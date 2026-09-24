# profiles/surge changelog

渲染入口：`profiles/surge/surge.conf`，VPS 只渲染这一份，路径不随版本变化。已发布版本的
快照在 `profiles/surge/version 1/<version>.conf`。设备订阅 URL 由 manifest 的 `output`
决定，升级和回滚都不需要改设备端 URL。

## 1.3.5 (2026-09-25)

- 将 18 个 `blackmatrix7` 远端 Rule Set 平行切换至本仓库 `rules/vendor/*.list` 本地快照（`facebook/instagram/whatsapp/spotify/github/telegram/twitch/discord/twitter/reddit/google/gemini/openai/anthropic/claude/paypal/fox/tiktok`），由 `sync-external` 每日同步，去重后在 `Meta/AI/Spotify` 等组中保持原有策略绑定与顺序。
- 保留 `Pixiv`（`rules/generated/pixiv.list`）与未迁移的远端兜底，完成本地三库平行版本。

## 1.3.4 (2026-09-25)

- 新增独立 `Pixiv` 策略组，默认选择 `Smart`，并保留各地区节点组供手动切换。
- 采用本仓库 `sync-geosite` Action 从 Loyalsoldier `geosite:pixiv` 生成的 Rule Set，并置于 `Meta` 与通用 `proxy.list` 之前，避免 Pixiv 请求被后续规则提前处理。

## 1.3.3 (2026-09-24)

- Kagi 策略组改用与本地 `search.svg` 配套的 144×144 PNG 图标，兼容 Surge 的 `icon-url` 图标加载。

## 1.3.2 (2026-09-24)

- 新增 Kagi 与 Orion Browser 域名规则及独立 `Kagi` 策略组，使用本地搜索图标。
- 修正 Kagi Rule Set 条目语法和图标 URL，并将其置于通用 `proxy.list` 前，避免被通用代理规则提前匹配。

## 1.3.1 (2026-09-24)

- 重排策略组为“服务分类 / 节点分类”两块，便于维护；策略组数量、名称、候选项和 Smart 权重保持不变。
- 修正 UnlimitedTurbo 注释，使其与当前 anytls 节点池定义一致。

## 1.2.3 (2026-09-21)

- 所有业务出口直接补齐 `Smart`、`Smart-Unlimited`、`Smart-US`、`HomeProxy`、`TX`、
  `UnlimitedTurbo` 及各地区节点组，避免只能通过 `Proxy` 间接进入节点组。

## 1.2.2 (2026-09-21)

- AI Suite 与 TikTok 增加 `Proxy` 候选，使这两个出口可以进入完整的节点组聚合层。

## 1.2.1 (2026-09-14)

- 新增 `All Nodes` 作为 Sub-Store 节点订阅入口；三个 `Smart`、TX、UnlimitedTurbo、HomeProxy
  及按地区筛选的策略组统一改为从该组取节点。
- `Proxy` 改为策略组聚合页，包含三个 `Smart`、HomeProxy、TX、UnlimitedTurbo，以及
  HongKong、CTM、TaiWan Nodes、Singapore、Japan、United States 等地区组，不再直接展开
  具体节点。
- `TaiWan Nodes` 作为台湾地区内层组加入 `Proxy`，避免外层 `TaiWan` 与 `Proxy` 互相引用。
- 归档 `1.1.8` 快照，为 `1.2.1` 腾出版本位。

## 1.1.10 (2026-09-14)

- 将 `Smart` 的 VOL/HS 基准权重从 `0.75` 下调到 `0.65`，让流量较贵的 VOL 节点更明显地优先于 TX。
- CTM/HK 的 VOL 权重更新为 `1.625`，SG 的 VOL 权重更新为 `0.325`；TX 和 `Smart-Unlimited` 不变。
- 归档 `1.1.7` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.10` 腾出版本位。

## 1.1.9 (2026-09-14)

- 将 `Smart` 和 `Smart-Unlimited` 的 CTM、HK 区域倍率统一提高到 `2.5`；SG 保持 `0.5`。
- CTM/HK 的 `Smart` 权重更新为 TX `2.125`、VOL `1.875`、HY2 `3.375`、AWS/CFT `3.125`。
- CTM/HK 的 `Smart-Unlimited` 权重更新为 TX `2.0`、AWS/CFT `2.75`。
- 归档 `1.1.6` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.9` 腾出版本位。

## 1.1.8 (2026-09-14)

- 为 `Smart` 和 `Smart-Unlimited` 增加区域倍率：`CTM` 乘以 `2.1`、`HK` 乘以 `1.8`、
  `SG` 乘以 `0.5`。
- Surge 的 `policy-priority` 只使用首条匹配规则，因此区域倍率已与 TX、VOL、AWS/CFT、
  HY2 等基础权重预先组合，不会覆盖或漏乘。
- 归档 `1.1.5` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.8` 腾出版本位。

## 1.1.7 (2026-09-14)

- 继续修复 Surge 对三个 Smart 组 `policy-priority` 报无效的问题：移除正则中的负向前瞻等复杂构造，
  改为只按当前节点标签中的 `TX`、`VOL`、`HY2`、`AWS`、`CFT`、`LAX`、`EB`、`CN2`
  使用普通字符类匹配。
- `Smart-Unlimited` 与 `Smart-US` 的 `policy-regex-filter` 同步收敛为简单正则，避免继续使用
  Surge 不接受的复杂组合表达式。
- 归档 `1.1.4` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.7` 腾出版本位。

## 1.1.6 (2026-09-14)

- 修复三个 Smart 组被 Surge 报 `policy-priority` 无效的问题：该字段按 `regex:factor`
  解析，正则内不能再出现 `:`；移除 `(?i)` 和 `(?:...)`，改用显式大小写字符类保持原有匹配效果。
- `tools/lint_surge_profiles.py` 增加活动入口文件的 `policy-priority` 结构校验，避免以后再次写入
  含冒号的正则构造。
- 归档 `1.1.3` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.6` 腾出版本位。

## 1.1.5 (2026-09-14)

- 策略组 `Smart-TX-CFT` 重命名为 `Smart-Unlimited`，与底层大流量池 `UnlimitedTurbo` 对齐；
  成员筛选与三档权重（TX `0.8` > AWS/CFT `1.1` > 日本 HY2 `1.4`）不变，所有引用该组的业务组
  同步改名。Surge 端会把它当成一个新组，旧的组内手动选择会被重置。
- 归档 `1.1.2` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.5` 腾出版本位。

## 1.1.4 (2026-09-14)

- 节点名分隔符扩展支持 `[` 和 `]`，允许 `CTM [vol] [ss]`、`LacusClyne [TX] [ss]` 这类标签式命名。
- `Smart`、`Smart-TX-CFT`、`Smart-US` 以及按名称筛选的地区组统一使用新的边界字符集。
- 归档 `1.1.1` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.4` 腾出版本位。

## 1.1.3 (2026-09-14)

- `Smart` 的 VOL/HS 权重分支增加 `vol` 名称匹配，后续可用英文节点名识别这类节点；不再建议
  为了权重把 `HS` 强行写进节点名。
- 暂缓 Sub-Store 自动补协议标签方案，当前只保留 Surge Profile 内的 `policy-priority` 权重。
- 归档 `1.0.2` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.3` 腾出版本位。

## 1.1.2 (2026-09-14)

- 修正 `Smart` 对 `TX-Misaka-Singapore` 的误判：旧版本会同时命中 HS（0.75）和 TX（0.85），
  可能把它按 HS 处理；新版本在 HS 分支前统一排除 TX / Boom / AWS / CFT / HY2 / CTM-SS。
- 归档 `1.0.1` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.2` 腾出版本位。

## 1.1.1 (2026-09-14)

- 策略组 `Boom` 重命名为 `UnlimitedTurbo`，并同步更新所有业务组与 AppleTV 规则引用。
- `UnlimitedTurbo` 的 `policy-regex-filter` 扩展为 `(?i)(boom|hy2|aws|cft)`，兼容旧 `boom`
  节点名以及 AWS/CFT 节点。
- 三个 Smart 组改为 Surge 原生 `smart` 并加入 `policy-priority`：`Smart` 按 HS > TX >
  美国 Snell > AWS/CFT > HY2；`Smart-TX-CFT` 按 TX > AWS/CFT > 日本 HY2；`Smart-US`
  按 EB Snell > EB HY2 > 其他美国节点 > CN2 HY2 > 其他 HY2。
- 归档 `1.0.0` 快照到 `archive/profiles/surge/version 1/`，为 `1.1.1` 腾出版本位。

## 校验加固 (2026-09-10，不升版本)

- 回滚语义定为「只往前走」：旧快照永远保持 `superseded`，想恢复旧内容就是把它复制进入口文件、
  再发布成一个新版本号。此前写的「把快照翻回 `active`」与「active 必须是本家族最高版本」这条
  规则互相矛盾，照做只会得到 `active version is not the highest version`。代价是回滚也占一个
  版本号：本家族已占着 1.0.0 / 1.0.1 / 1.0.2，下次回滚前得先把 1.0.0 移入 `archive/`。
- `tools/check-profile-versions.py` 补三类校验（三个家族同一套规则）：
  入口文件的当前版本必须有对应快照，且该快照与入口文件除 `@status` 一行外必须逐行相同
  （1.0.2 就踩过坑：快照留的是旧内容，两个校验脚本都照样绿）；manifest 的 `template_url`
  路径必须与 `source` 落到同一个文件、`source` 必须存在、`output` 不得重复；家族目录里除
  `.conf` 与 `CHANGELOG.md` 外不留其他文件，子目录必须叫 `version <major>` 且快照 major 与
  所在目录一致。
- `tools/test-check-profile-versions.py` 用例从 12 个增加到 22 个；当前仓库跑
  `python3 tools/check-profile-versions.py .` 为 0 error。

## 1.0.2 (2026-09-10)

- 图标改回 PNG 交付：`Smart` 由 `policy/speed-slow-svgrepo-com.svg` → `policy/speed.png`，
  `Boom` 由 `policy/cloudflare-color.svg` → `policy/cloudflare-color.png`。1.0.1 记的「真机是否支持
  SVG」不确定性随之取消，`.svg` 退回可编辑源文件；`Proxy` 组沿用 1.0.1 的 `policy/Surge.png`。
- 换图：`Domestic` 由 Qure `policy/domestic.png` → `policy/china.png`，`HomeProxy` 由
  `policy/home.png` → `policy/home-wifi.png`（深蓝房形底 + 白色 Wi-Fi，明暗模式都读得清）。
  `profiles/simple/surge-simple.conf`、`legacy/`、`archive/` 仍用 `domestic.png` 与 `home.png`。
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
  `version 1/1.0.1.conf` 的正文复制回 `surge.conf`，并按发布流程发布成新的版本号（1.0.3）；
  快照不会翻回 `active`，见 `docs/operations/profile-versioning.md`。
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
