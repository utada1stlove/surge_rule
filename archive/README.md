# 存档文件

本目录存放已停用文件与改动前的版本快照，仅作追溯用。三条约定：

- 不再维护，内容不随顶层 Profile 更新；
- 不进入 config/private-profile-templates.json，`tools/check-profile-versions.py`
  会直接拦截指向 archive/ 的 manifest 引用；
- 不参与私有渲染，也不作为设备订阅 URL 的源文件。

已冻结但仍保留完整结构供查阅的配置放在 `legacy/`，它同样不进 manifest，但会继续
参与仓库的公开结构校验；`archive/` 只放旧快照和历史文件，见 [legacy 说明](../legacy/README.md)。

## 清单

| 文件 | 存档日期 | 说明 |
| --- | --- | --- |
| surgeion.conf | 2026-09-09 | 顶层 surgeion.conf 的改动前快照，取自 commit 9cbdd06。改动删除了排在 Twitter.list、Reddit.list 之前的 rules/social-sg.list 覆盖规则（该清单的 5 个域名已被两条上游规则完全覆盖，导致 Twitter、Reddit 两个组永不命中），同时把 Twitter、Reddit 的默认项设为 Singapore、Spotify 的默认项设为 United States，使默认出口与本快照保持一致。 |
| icons/paypal.png、icons/twitter.png | 2026-09-09 | 由 *-brands-solid-full.svg 直接渲染的灰度图标，单色无 fill、透明底，深色模式下几乎不可见；与在用的 Paypal.png、Twitter.png 仅首字母大小写不同，为避免误引用移出 assets/icons/services/。 |

## 与版本历史的关系

git 本身可以取回任何历史版本（git log --diff-filter=D、git show 提交:路径）。
本目录只保留"工作区需要留一份直接对照"的少数文件，不替代版本历史。
