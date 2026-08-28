# Sub-Store + GitHub 规则：单链接使用方案

## 目标

在 iPhone Surge 中只保存一个 Sub-Store Surge 输出链接：

```text
Sub-Store 节点订阅
        +
GitHub 公开 Rule Set
        ↓
Sub-Store 输出的 Surge Profile
        ↓
iPhone Surge 一个链接
```

你的节点订阅 URL 是私有凭据，本仓库不读取、不保存、不提交它。

## 最简单的第一步

先直接在 Surge iPhone 中添加现有的 Sub-Store Surge 输出链接，确认：

1. Profile 可以加载；
2. 节点出现在策略组中；
3. Surge 可以启动；
4. 请求列表能够显示流量；
5. 至少一个代理目标可以正常连接。

Sub-Store 官方项目支持 Surge 作为输出平台，并支持 SS、AnyTLS、Hysteria 2 等输入节点类型。[Sub-Store README](https://github.com/sub-store-org/Sub-Store)

## 接入本仓库规则

在 Sub-Store 中为 Surge 输出配置或自定义模板时，将 [规则注入片段](../../templates/substore/surge-rule-section.conf) 放入生成 Profile 的 `[Rule]` 区域。

片段引用三个公开地址：

```ini
RULE-SET,https://raw.githubusercontent.com/utada1stlove/surge_rule/main/rules/direct.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/utada1stlove/surge_rule/main/rules/reject.list,REJECT
RULE-SET,https://raw.githubusercontent.com/utada1stlove/surge_rule/main/rules/proxy.list,Proxy
FINAL,DIRECT
```

如果 Sub-Store 生成的策略组不叫 `Proxy`，需要把最后一个 `Proxy` 替换成实际的策略组名称。不要把节点密码或订阅 URL 写入这份公开片段。

当前配置会加载 `reject.list` 的保守基础集，并主动加载 [blackmatrix7 Advertising](https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Advertising/Advertising_All_No_Resolve.list) 外部清单。大型清单可能造成误杀；如果某个 App 异常，可先移除模板中的该行，保留本仓库自己的基础集。

## 一次配置后的日常流程

```text
修改 GitHub rules/*.list
        ↓
提交并推送
        ↓
Surge 更新 Sub-Store 输出 Profile
        ↓
Surge 更新远程 Rule Set
        ↓
检查请求列表
```

节点更新和规则更新是两条链路，但用户在 Surge 中只需要维护一个 Sub-Store Profile 链接。

## 重要限制

目前不能仅凭一个公开 GitHub 文件自动读取你的私有订阅并生成完整 Profile。Sub-Store 中仍需要保存订阅源，并绑定自定义模板或处理脚本。公开仓库提供的是规则内容和注入片段，不是节点聚合服务。

如果当前 Sub-Store 输出已经包含完整 `[Rule]`，直接添加本仓库片段可能造成重复规则。应先查看输出中的 `[Rule]`，再替换或追加，尤其要确保 `FINAL` 只在最后出现。

## 安全检查

- 不把订阅 URL 提交到 GitHub；
- 不把 Sub-Store 配置截图公开；
- 不使用带真实节点信息的 Profile 作为公开示例；
- 修改规则后先检查 Raw 文件内容；
- 更新后在 Surge 请求列表中确认实际命中。

Sub-Store 项目还专门提醒其模块后端域名和 CORS 配置存在数据暴露风险；使用模块时应限制来源，不要随意启用任意来源访问。[Sub-Store 配置说明](https://github.com/sub-store-org/Sub-Store/blob/master/config/README.md)
