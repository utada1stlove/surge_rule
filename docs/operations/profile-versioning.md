# Profile 版本化

版本化的目标是：想法随时间演进，但配置、订阅 URL 和回滚路径保持稳定。真源是渲染入口
文件首部 `# @version:`；入口文件的路径由 manifest 的 `output` 决定，发布新版本时不变，
所以设备端和 VPS 都不需要跟着版本号改路径。

## 三条主线

| 家族 | 用途 | 目录 | manifest output |
| --- | --- | --- | --- |
| `surge` | 多策略组主配置 | `profiles/surge/` | `surge.conf` |
| `simple` | DIRECT / Proxy / REJECT 简洁配置 | `profiles/simple/` | `surge-simple.conf` |
| `home-wg` | WireGuard 回家 | `profiles/home-wg/` | `surge-home-wg.conf` |

`legacy/` 已冻结，不再进入 manifest、不再由私有服务输出；`archive/` 只保存旧版本
快照与历史文件，也不得进入 manifest。

## 版本规则

每个家族只有一个渲染入口，直接放在家族目录下，文件名与 manifest `output` 一致
（`profiles/surge/surge.conf`、`profiles/simple/surge-simple.conf`、
`profiles/home-wg/surge-home-wg.conf`），因此改版本号不会改渲染路径。版本快照放在
`profiles/<family>/version <major>/<semver>.conf`，三个家族都已按这个布局摆放。
两类文件头都必须写：

```ini
# @profile: <family>
# @version: <major>.<minor>.<patch>
# @status: active（入口）或 superseded（快照）
# @changed: YYYY-MM-DD
# @changelog: profiles/<family>/CHANGELOG.md
```

约束（由 `tools/check-profile-versions.py` 校验）：

- 入口文件是唯一的 `# @status: active`，且 `@version` 是本家族最高版本；入口文件名不
  要求等于 `@version`，但如果它本身长得像版本号（`1.0.0.conf`），两者必须相等；
- 快照文件名必须等于自己的 `@version`，`@status` 必须是 `superseded`，且不得被
  manifest 引用；
- 入口文件当前版本号必须有一份自己的快照，且这份快照与入口文件**只允许 `@status`
  一行不同**；其余快照记录各自历史内容，不参与比对；
- manifest 的 `source` 必须指向入口文件；
- `template_url` 的路径部分必须落到同一个 `source` 文件上：VPS 拉的是
  `template_url`，校验和 provenance 读的是 `source`，两者一旦分叉，设备会静默停在旧
  版本而校验全绿；
- 家族目录里只允许 `.conf` 与 `CHANGELOG.md`，子目录必须是 `version <major>`，且快照的
  major 必须与所在目录一致。这条是为了让任何误放的文件（比如一份没有 `.conf` 后缀的
  副本）无处藏身；
- 每个家族最多保留 3 个不同版本号（入口文件与快照去重后计数）；更旧的移入 `archive/`。

发布一次改动：

1. 改 `profiles/<family>/<output>`，升 `@version` 与 `@changed`；
2. 把它复制成 `profiles/<family>/version <major>/<new-version>.conf`，并把快照的
   `@status` 改成 `superseded`（快照与入口文件只允许这一行不同）；
3. 在 `profiles/<family>/CHANGELOG.md` 补一条；
4. 跑一遍下面的校验脚本。

patch（`1.0.0` → `1.0.1`）和 minor（`1.0.x` → `1.2.0`）走同一条流程，只是新版本号不同；
major（`1.x.y` → `2.0.0`）新建 `profiles/<family>-v2/` 家族目录，旧家族整体进入历史线，
manifest 的 `id` / `source` 切到新目录。

回滚只往前走（forward-only）：快照永远保持 `superseded`，不会被翻回 `active`，因为
校验要求 active 是本家族最高版本，而 `version <major>/` 里那份旧快照仍然计在版本集合内，
把 1.0.1 翻回 active 只会得到 `active version is not the highest version`。正确做法是把
目标快照的正文复制进 `profiles/<family>/<output>`，`@version` 写一个**新的**号
（例如回到 1.0.1 的内容就发布成 1.0.3），`@changed` 更新为当天，再按上面的发布流程补一份
`version <major>/<new-version>.conf` 快照和一条 changelog。设备订阅 URL（manifest
`output`）与 `source` 全程不变，VPS 下一次渲染即生效。

代价是回滚也占一个版本号：家族已经占满 3 个版本号时，先按「更旧的移入 `archive/`」腾位置。
surge 家族当前已有 1.0.0 / 1.0.1 / 1.0.2 三个版本，下一次回滚必须先归档 1.0.0。

## Manifest 字段

`config/private-profile-templates.json` 的每条记录：

- `source`：仓库内相对路径，版本校验和渲染 provenance 都以此为准；
- `template_url`：GitHub Raw 地址，VPS 渲染器从这里取模板，必须与 `source` 指向同一个文件；
- `output`：私有服务输出文件名，也是设备订阅 URL 的最后一段，升级/回滚时保持稳定。

VPS 渲染成功后在输出文件首部注入：

```ini
# @rendered-from: profiles/<family>/<output>
# @rendered-at: YYYY-MM-DDTHH:MM:SSZ
```

`@rendered-from` 取的就是 manifest 的 `source`（也就是入口文件），因此升级和回滚时这一行
都不会变；`tools/check-profile-versions.py` 会校验 `template_url` 与 `source` 指向同一个文件，
保证这一行说的就是 VPS 真正拉取的那份内容。

`release.json` 同时记录 `sources`，`surge-profilectl status --check` 会按它核对
每份输出的 profile/version 元数据。

## 校验

提交前运行：

```bash
python3 tools/check-profile-versions.py .
python3 tools/check-private-profile-templates.py .
python3 tools/lint_surge_profiles.py .
python3 tools/test-check-profile-versions.py
python3 tools/test-private-profile-renderer.py
```

`tools/lint_surge_profiles.py` 会连同一并 lint 家族子目录里的快照，但只有入口文件参与
manifest 覆盖检查。

## 设备端生效

托管 Profile 的 `interval=86400`，VPS 更新后 iPhone 仍可能等到 24 小时才自动拉取。
需要立即验证时，在 Surge 中手动触发一次 Profile 更新。
