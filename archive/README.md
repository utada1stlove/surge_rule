# 存档文件

本目录存放已停用文件与改动前的版本快照，仅作追溯用。三条约定：

- 不再维护，内容不随顶层 Profile 更新；
- 不参与校验：scripts/lint_surge_profiles.py 只扫描仓库顶层的 *.conf；
- 不得写入 config/private-profile-templates.json 的 template_url。私有 Profile
  渲染服务只从仓库顶层的 Raw 地址取模板，指向本目录会让对应 Profile 渲染失败。

## 清单

| 文件 | 存档日期 | 说明 |
| --- | --- | --- |
| surgeion.conf | 2026-09-09 | 顶层 surgeion.conf 的改动前快照，取自 commit 9cbdd06。改动删除了排在 Twitter.list、Reddit.list 之前的 rules/social-sg.list 覆盖规则（该清单的 5 个域名已被两条上游规则完全覆盖，导致 Twitter、Reddit 两个组永不命中），同时把 Twitter、Reddit 的默认项设为 Singapore、Spotify 的默认项设为 United States，使默认出口与本快照保持一致。 |
| icons/paypal.png、icons/twitter.png | 2026-09-09 | 由 *-brands-solid-full.svg 直接渲染的灰度图标，单色无 fill、透明底，深色模式下几乎不可见；与在用的 Paypal.png、Twitter.png 仅首字母大小写不同，为避免误引用移出 assets/icons/services/。 |

## 与版本历史的关系

git 本身可以取回任何历史版本（git log --diff-filter=D、git show 提交:路径）。
本目录只保留"工作区需要留一份直接对照"的少数文件，不替代版本历史。
