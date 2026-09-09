# Legacy（冻结配置）

`legacy/` 保存已经退出版本线、不再由私有渲染服务输出的配置。文件仍留在仓库供查阅，
但行为不再演进，也不作为设备订阅 URL 的源文件。

## 约定

- 每份 `.conf` 带 `# @status: frozen` 和 `# @frozen-at`；
- 不进入 `config/private-profile-templates.json`，`tools/check-profile-versions.py`
  会拦截指向 `legacy/` 的 manifest 引用；
- 不参与 VPS 渲染，`surge-profilectl update` 不会再从这些文件生成输出；
- 继续被 `tools/lint_surge_profiles.py` 扫描，防止公开坏链、结构错误和疑似凭据；
- 只允许安全修复和坏链修复，不做行为变更；需要新行为时在 active 家族中新建版本。

## 清单

| 文件 | 冻结日期 | 说明 |
| --- | --- | --- |
| `profile.example.conf` | 2026-09-09 | 手写样板，无托管声明，只作阅读参考 |
| `surge-main.conf` | 2026-09-09 | 多策略组配置，之前对应私有服务的 `surge-main.conf` 输出 |
| `surgeion.conf` | 2026-09-09 | 多策略组 + 手动出口 `select` 配置，之前对应 `surgeion.conf` 输出 |

## 与 archive 的区别

- `legacy/`：仍然保留完整公开结构的冻结配置，继续参与公开结构校验；
- `archive/`：旧版本快照与历史文件，只作追溯，见 [archive 说明](../archive/README.md)。

版本契约与回滚流程见 [Profile 版本化](../docs/operations/profile-versioning.md)。
