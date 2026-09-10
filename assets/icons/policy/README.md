# 策略组图标资源

获取日期：2026-09-02（Asia/Singapore）。这些 PNG 供 Surge `[Proxy Group]` 的 `icon-url` 调用，并由本仓库 Raw 地址提供。

自 2026-09-10 起本目录另存了若干 `.svg`。1.0.1 曾把 `icon-url` 直接指向 SVG，1.0.2 已改回 PNG 交付；
`.svg` 只留作可编辑源文件，理由同 `assets/icons/services/README.md`：Surge 官方文档只示例 `.png`。

渲染方式与尺寸约定同服务类图标（`rsvg-convert` + `magick` 去元数据）：新增图标一律以 **144x144** 发布。
144 是 Surge 的推荐尺寸和本仓库的既有约定，不是硬限制——下表里 `telegram.png`、`nsfw.png` 是 512x512，
`aws.png`、`cloud.png` 是 108x108，都在正常显示。真正要守的是：光栅 PNG、透明底、近正方形、体积小
（`icon-url` 每次刷新都要重新下载）。SVG Repo 导出的 1x/3x 副本（72x72、216x216）不留在本目录，
已移入 `../../../legacy/icons/`，见该目录 README。

| 文件 | 用途 | 上游来源 |
| --- | --- | --- |
| `proxy.png` | 代理入口与 Boom | [Qure Proxy](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Proxy.png) |
| `domestic.png` | 国内服务（`profiles/simple/surge-simple.conf`、`legacy/`、`archive/`；`profiles/surge` 1.0.2 起改用 `china.png`） | [Qure Domestic](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Domestic.png) |
| `apple.png` | Apple 服务 | [Qure Apple](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Apple.png) |
| `global.png` | 通用/亚太组 | [Qure Global](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Global.png) |
| `lock.png` | Private 组 | [Qure Lock](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Lock.png) |
| `telegram.png` | `profiles/surge/surge.conf` 的 Telegram 组 | 本地提供，512x512；上游来源未记录 |
| `nsfw.png` | `profiles/surge/surge.conf` 的 NSFW 组 | 本地提供，512x512；上游来源未记录 |
| `ai.png` | AI Suite | [Qure AI](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/AI.png) |
| `spotify.png` | Spotify | [Qure Spotify](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Spotify.png) |
| `tiktok.png` | TikTok | [Qure TikTok](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/TikTok.png) |
| `bilibili.png` | Bilibili | [Qure bilibili](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/bilibili.png) |
| `finance-daily.png` | Finance 组 | [Qure Daily](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Daily.png) |
| `finance.png` | 加密货币备用 | [Qure Cryptocurrency](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/Cryptocurrency.png) |
| `tencent.png` | TX 组 | [fmz200 Tencent](https://raw.githubusercontent.com/fmz200/wool_scripts/main/icons/apps/tencent.png) |
| `cloud.png` | Cloud 组 | [fmz200 Google Drive](https://raw.githubusercontent.com/fmz200/wool_scripts/main/icons/apps/GoogleDrive.png) |
| `twitch.png` | Twitch 组 | [fmz200 Twitch](https://raw.githubusercontent.com/fmz200/wool_scripts/main/icons/apps/twitch.png) |
| `youtube.png` | YouTube 组（`legacy/surgeion.conf`、`legacy/surge-main.conf`） | [Qure YouTube](https://raw.githubusercontent.com/Koolson/Qure/master/IconSet/Color/YouTube.png) |
| `home.png` | `HomeProxy` 组（`profiles/simple`、`legacy/` 与 `profiles/surge` 1.0.1 及更早快照）；`profiles/surge` 1.0.2 起改用 `home-wifi.png` | [fmz200 Apple Home](https://raw.githubusercontent.com/fmz200/wool_scripts/main/icons/apps/Apple_Home.png) |
| `Surge.png` | `profiles/surge/surge.conf` 的 `Proxy` 组（1.0.1 起） | 本地提供，144x144；上游来源未记录。注意首字母大写，Raw 地址区分大小写 |
| `cloudflare-color.svg` | `cloudflare-color.png` 的可编辑源文件（仅 1.0.1 快照直接引用过 SVG） | Cloudflare 双色品牌图（`#F38020` + `#FCAD32`，24x24 viewBox）；上游来源未记录 |
| `cloudflare-color.png` | `profiles/surge/surge.conf` 的 `Boom` 组（1.0.2 起） | 由同目录 `cloudflare-color.svg` 渲染，144x144，全彩双色、透明底 |
| `speed-slow-svgrepo-com.svg` | `speed.png` 的可编辑源文件（仅 1.0.1 快照直接引用过 SVG） | [SVG Repo](https://www.svgrepo.com/) 素材，800x800 viewBox |
| `speed.png` | `profiles/surge/surge.conf` 的 `Smart` 组（1.0.2 起） | 由 `speed-slow-svgrepo-com.svg` 渲染，144x144 / 8.9KB。图形是带 "FAST"/"SLOW" 文字的推杆，144 下文字勉强可读但已不是重点，识别靠蓝黄滑条 |
| `china-1-svgrepo-com.svg` | `china.png` 的可编辑源文件 | [SVG Repo](https://www.svgrepo.com/) 素材 |
| `china.png` | `profiles/surge/surge.conf` 的 `Domestic` 组（1.0.2 起） | 由 `china-1-svgrepo-com.svg` 渲染，144x144。**已知问题**：纯 `#000000` 中国地图剪影、透明底，深色模式下几乎不可见，与 `archive/icons/` 里那两张 `*-brands-solid-full.svg` 渲出的单色图同一毛病；要么上色（描边或改填充色），要么回退到 Qure `domestic.png` |
| `home-wifi-svgrepo-com.svg` | `home-wifi.png` 的可编辑源文件 | [SVG Repo](https://www.svgrepo.com/) 素材 |
| `home-wifi.png` | `profiles/surge/surge.conf` 的 `HomeProxy` 组（1.0.2 起） | 由 `home-wifi-svgrepo-com.svg` 渲染，144x144。深蓝圆角房形底 + 白色 Wi-Fi 图形，明暗两种模式都读得清；替换掉原先与其他 Profile 共用的 `home.png` |

以下 SVG Repo 候选图标已冻结在 `../../../legacy/icons/`，本目录不再保留：`antique-characters-machine*`
（打字机，单色线稿）、`bulletin-journal-magazine*`（报刊，单色线稿）、`dollar-finance-money*`（行情屏，
单色细线稿）。三张根节点都是 `fill="#000000"`，深色模式下几乎不可见，因此未采用；`Finance` 组继续用
`services/reuters.png`。

上游资源的许可和使用条款以各自项目为准；本仓库仅将其作为 Surge UI 图标使用。
