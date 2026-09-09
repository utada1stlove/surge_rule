# 服务类图标资源

这些 PNG 供 Surge `[Proxy Group]` 的 `icon-url` 调用，由本仓库 Raw 地址提供。Surge 官方文档只给出 `.png` 示例，未声明 `icon-url` 支持 SVG，因此本目录一律以 **PNG 交付**；同名 `.svg` 仅作为可编辑源文件保留。

## 渲染方式

```bash
rsvg-convert -w 144 -h 144 <name>.svg -o <out>.png
magick <out>.png -depth 8 -strip -define png:exclude-chunk=all <out>.png
```

统一 144x144、8-bit RGBA、透明背景，与本目录既有图标一致。

## 文件说明

| 文件 | 用途 | 来源 |
| --- | --- | --- |
| `youtube.svg` / `youtube.png` | `surge.conf` YouTube 组 | 本地提供（红色圆角方块 + 白色播放键的应用图标样式）；PNG 由该 SVG 渲染 |
| `dropbox.svg` / `dropbox.tile.png` | `surge.conf` `Cloud Box` 组 | 本地提供（圆角方块 tile + 白色 Dropbox 开盒图形）。原 SVG 底色为 `#4D8DC9`，已改为品牌蓝 `#0061FF`；PNG 由修改后的 SVG 渲染 |
| `dropbox.png` | 其余 Profile（`surgeion.conf`）`Cloud` 组 | 仓库既有资源，官方蓝裸图形、透明底、144x144；未改动 |
| `dropbox-brands-solid-full.svg` | 未使用 | Font Awesome Free 7.3.1 单色 path，无 `fill`，渲染为黑色透明底，深色模式下几乎不可见，故未采用 |
| `line.svg` | 未使用 | 本地提供；当前 LINE 流量由 `rules/line.list` 归入 `Japan` 组，尚无独立策略组引用该图标 |
| `Paypal.png` | `surge.conf` `PayPal` 组 | 全彩品牌图，144x144 |
| `Twitter.png` | `surge.conf` `Twitter` 组 | 全彩品牌图，144x144 |
| `google.png` | `surge.conf` `Google` 组 | 由 `google-color.svg` 渲染，144x144 |
| `paypal.png`、`twitter.png` | 未使用 | 与上面两个文件仅首字母大小写不同，是 `*-brands-solid-full.svg` 的直接渲染：单色无 `fill`、灰度透明底，深色模式下几乎不可见。GitHub Raw 地址区分大小写，引用 `icon-url` 时务必用大写首字母的版本 |
| `house-solid-full.svg` | 未使用 | 仅保留为可编辑源文件；`HomeProxy` 组沿用 `assets/icons/policy/home.png`（同为房屋图形，全彩） |

其余 PNG（`reuters.png`、`whatsapp.png`、`reddit.png`、`chatgpt.png` 等）为仓库既有资源，上游来源未在仓库内记录。

图标许可与使用条款以各自品牌资源规范为准；本仓库仅将其作为 Surge UI 图标使用。
