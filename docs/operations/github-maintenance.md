# GitHub 规则维护流程

## 推荐仓库结构

```text
README.md
profiles/
  surge/
    surge.conf              # 渲染入口，路径稳定
    version 1/
      <version>.conf        # 已发布快照
  simple/
    surge-simple.conf       # 渲染入口，路径稳定
    version 1/
      <version>.conf        # 已发布快照
  home-wg/
    surge-home-wg.conf      # 渲染入口，路径稳定
    version 1/
      <version>.conf        # 已发布快照
legacy/
  ...
  icons/
archive/
  ...
rules/
  direct.list
  proxy.list
  reject.list
scripts/
modules/
tools/
docs/
  ...
```

公开仓库只保存通用规则和模板。进入版本线的主配置放在 `profiles/<family>/`，渲染入口
以 manifest `output` 命名（`profiles/surge/surge.conf`），版本号写在文件头
`# @version`；`version <major>/<version>.conf` 里的快照仍要求文件名与 `@version` 一致。
完整规则见 [Profile 版本化](profile-versioning.md)。
`legacy/` 保存已冻结的完整配置和不再引用的图标素材（`legacy/icons/`），只修坏链与安全问题，
不再由私有服务输出；
`archive/` 保存旧版本快照与历史文件，二者都不得作为
`config/private-profile-templates.json` 的 `source`。校验统一用仓库自带的
`tools/lint_surge_profiles.py`、`tools/check-profile-versions.py` 和
`tools/check-private-profile-templates.py`。个人 Profile 可以在本地保存，或者放在
私有仓库中。

## 发布前检查

每次提交前检查：

- 是否误提交订阅 URL；
- 是否出现密码、Token、私钥或 Controller 密钥；
- 每条规则是否有正确的逗号和字段；
- 外部 Rule Set 是否没有写策略名称；
- `FINAL` 是否只位于主 `[Rule]` 中；
- 是否记录了规则来源和变更原因；
- 是否先在测试 Profile 中验证。

## 在 iPhone 中引用

将 GitHub 仓库中的文件通过 Raw URL 引用：

```ini
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy.list,Proxy
```

修改流程：

```text
编辑本地文件
  ↓
提交 GitHub
  ↓
等待 Surge 更新缓存
  ↓
查看请求列表和规则命中
  ↓
确认或回滚
```

## 托管 Profile

如果希望 Surge 自动更新一整份 Profile，可以使用：

```ini
#!MANAGED-CONFIG https://raw.githubusercontent.com/USER/REPO/main/profile.conf interval=86400 strict=false
```

`interval` 是最短检查间隔，`strict=false` 表示远程更新失败时可以继续使用旧配置。[Managed Profile](https://manual.nssurge.com/profile/managed-profile.html)

对于大多数个人用户，建议先使用远程 `RULE-SET`，不要一开始就把包含个人节点的完整 Profile 公开。

托管 Profile 在设备上是只读的：Surge 不能修改托管规则，想手改要先复制一份配置，副本首行的托管声明会随之消失。详见 [托管 Profile 与手改副本](../knowledge-base/managed-profile-copy-edit.md)。

版本化与设备订阅 URL 的固定方式见 [Profile 版本化](profile-versioning.md)。

## 回滚

如果更新规则后出现异常：

1. 在 GitHub 查看最近一次提交；
2. 找出发生问题的规则文件；
3. 恢复上一版文件或提交一个反向修复；
4. 等待 Surge 拉取更新；
5. 用请求列表确认问题消失；
6. 再分析原始变更，而不是直接继续堆规则。

## 缓存和更新延迟

远程规则会被 Surge 缓存，提交 GitHub 后不一定立即生效。排错时应同时记录：提交时间、Surge 版本、规则 URL、实际生效时间和请求命中结果。

## 规则来源管理

外部规则集应记录来源和用途。未经审查的第三方规则不要直接并入主规则；先放在独立文件中测试，确认误杀率和维护状态后再决定是否长期使用。
