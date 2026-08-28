# Sub-Store + GitHub 规则：单链接使用方案

## 目标

在 iPhone Surge 中由 Sub-Store 通过 `policy-path` 提供节点，由主 Profile 提供规则：

```text
Sub-Store 节点订阅 → Proxy Group.policy-path
GitHub 公开 Rule Set → Surge 主 Profile 的 [Rule]
```

你的节点订阅 URL 是私有凭据，本仓库不读取、不保存、不提交它。

## 最简单的第一步

先把现有的 Sub-Store Surge 输出链接填入主 Profile 的 `policy-path`，再在 Surge iPhone 中安装主 Profile，确认：

1. Profile 可以加载；
2. 节点出现在策略组中；
3. Surge 可以启动；
4. 请求列表能够显示流量；
5. 至少一个代理目标可以正常连接。

Sub-Store 官方项目支持 Surge 作为输出平台，并支持 SS、AnyTLS、Hysteria 2 等输入节点类型。[Sub-Store README](https://github.com/sub-store-org/Sub-Store)

## 接入本仓库规则

在 Surge 主 Profile 的 `[Rule]` 区域加入 [规则片段](../../templates/substore/surge-rule-section.conf)。当前片段不是 Sub-Store 的节点操作配置，也不是完整 Profile。

主 Profile 的策略组写法：

```ini
[Proxy Group]
Proxy = select, policy-path="你的 Sub-Store Surge 输出链接", update-interval=86400, DIRECT
```

官方说明中，`policy-path` 可以加载远程代理列表或包含 `[Proxy]` 的完整 Surge Profile，并会缓存和定期重新下载。[Policy Including](https://manual.nssurge.com/policy-groups/policy-including.html)

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
修改 GitHub rules/*.list        修改节点时更新 Sub-Store
        ↓                                  ↓
提交并推送规则                    刷新外部代理订阅
        └──────────────┬───────────────┘
                       ↓
                 检查请求列表
```

节点更新和规则更新是两条链路。主 Profile 需要长期保留；Sub-Store 链接通过 `policy-path` 提供节点来源。

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
