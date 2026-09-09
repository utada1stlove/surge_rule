# Profile 版本化

版本化的目标是：想法随时间演进，但配置、订阅 URL 和回滚路径保持稳定。真源是
`profiles/<family>/<version>.conf` 的文件名与首部 `# @version:`，两者必须相等。

## 三条主线

| 家族 | 用途 | 目录 | manifest output |
| --- | --- | --- | --- |
| `surge` | 多策略组主配置 | `profiles/surge/` | `surge.conf` |
| `simple` | DIRECT / Proxy / REJECT 简洁配置 | `profiles/simple/` | `surge-simple.conf` |
| `home-wg` | WireGuard 回家 | `profiles/home-wg/` | `surge-home-wg.conf` |

`legacy/` 已冻结，不再进入 manifest、不再由私有服务输出；`archive/` 只保存旧版本
快照与历史文件，也不得进入 manifest。

## 版本规则

文件名使用语义化版本 `<major>.<minor>.<patch>.conf`，文件头必须写：

```ini
# @profile: <family>
# @version: <major>.<minor>.<patch>
# @status: active
# @changed: YYYY-MM-DD
# @changelog: profiles/<family>/CHANGELOG.md
```

- patch（`v1.0.0` → `v1.0.1`）：原地修改同一个文件，更新 `@changed` 与 changelog；
- minor（`v1.0.x` → `v1.2.0`）：在同一家族目录新建 `<x.y.0>.conf`，旧文件标记
  `# @status: superseded`，manifest 切到新文件；
- major（`v1.x.y` → `v2.0.0`）：新建 `profiles/<family>-v2/` 目录，旧家族整体进入
  历史线，manifest 切到新目录；
- 每个家族最多保留 3 个版本；更旧的移入 `archive/`，不得被 manifest 引用。

旧版本保留在 `profiles/` 内时仍可用于快速回滚。回滚只改
`config/private-profile-templates.json` 中该家族的 `source` 一行，设备订阅 URL
（manifest `output`）不变。

## Manifest 字段

`config/private-profile-templates.json` 的每条记录：

- `source`：仓库内相对路径，版本校验和渲染 provenance 都以此为准；
- `template_url`：GitHub Raw 地址，VPS 渲染器从这里取模板；
- `output`：私有服务输出文件名，也是设备订阅 URL 的最后一段，升级/回滚时保持稳定。

VPS 渲染成功后在输出文件首部注入：

```ini
# @rendered-from: profiles/<family>/<version>.conf
# @rendered-at: YYYY-MM-DDTHH:MM:SSZ
```

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

## 设备端生效

托管 Profile 的 `interval=86400`，VPS 更新后 iPhone 仍可能等到 24 小时才自动拉取。
需要立即验证时，在 Surge 中手动触发一次 Profile 更新。
