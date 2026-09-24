# 外部规则 vendoring 与去重

本仓库新增三层：`rules/diy`（`rules/*.list`）、`rules/generated`（`geosite`）、`rules/vendor`（他人规则快照）。

## 同步
- 清单：`config/external-manifest.json`
- 脚本：`tools/sync-external.mjs --manifest config/external-manifest.json --output rules/vendor`
- 工作流：`.github/workflows/sync-external.yml` 每日 22:15 UTC 拉取并提交 `rules/vendor` 与 `reports/dedup.json`

产物每文件头部含 `# Vendored from <url>` 与 `# fetched-at`，不手改。

## 去重
- 脚本：`node tools/dedup.mjs .` 生成 `reports/dedup.json`
- 优先级 `diy > generated > vendor`，按 `profiles/surge/surge.conf` 的首匹配语义，被高优先级已覆盖的低优先级条目标为 `shadowed`，仅报告不自动删
- 单文件内重复由 `tools/lint_surge_profiles.py` 覆盖

## 使用
- Profile 仍可引用远端 `RULE-SET`，逐步切到 `rules/vendor/*.list` 的本地路径 `https://raw.githubusercontent.com/utada1stlove/surge_rule/main/rules/vendor/<name>.list`
- 大表（`category-ads-all`）不入库，避免仓库膨胀
