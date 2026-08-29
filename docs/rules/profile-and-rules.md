# Profile、策略组与规则

## 三层关系

```text
请求
  ↓
Rule：判断“这是什么流量”
  ↓
Policy Group：选择使用哪个策略
  ↓
Proxy / DIRECT / REJECT：决定如何连接
```

Rule 不负责定义节点，节点也不负责决定哪些域名使用它们。将这三层分开，配置才容易维护。

## 推荐的公开规则拆分

```text
rules/
  direct.list
  proxy.list
  reject.list
```

当前 `proxy.list` 已按以下分流板块添加注释和规则：

- 开发与代码托管；
- 开发依赖与容器；
- AI：OpenAI / Anthropic / 其他；
- AI：Google 系；
- 搜索与 Google 服务；
- 视频与流媒体；
- 通讯与社区；
- 社交平台。

当前主 Profile 已按 DAE 意图把主要板块映射到策略组：广告/跟踪到 `REJECT`，Telegram 到 `Boom`，Google/Gemini 到 `TaiWan`，其他 AI 与社交到 `Singapore`，YouTube 到 `CTM`，TikTok 到独立的 `TikTok` 策略组，Bilibili 到可手动选择 `REJECT / DIRECT / HongKong / TaiWan / CTM` 的 `Bilibili` 策略组，金融到 `HongKong`，支付/加密货币/Spotify 到 `US`，开发、云盘、Twitch、Discord 和 Docker 到 `Proxy`。其中 Google 系 AI 与其他 AI 是独立板块，不会因为都属于 AI 而混用策略。

地区策略组会按节点名识别常见家宽运营商：`HKBN`、`HKT`、`PCCW`、`Netvigator`、`WTT`、`i-Cable`、`SmarTone`、`HGC`、`CMHK` → `HongKong`；`Hinet`、`Chunghwa`、`Seednet`、`Fetnet`、`FarEasTone`、`Taiwan Mobile`、`TWM Broadband` → `TaiWan`；`SoftBank`、`docomo`、`NTT`、`NURO`、`IIJ`、`BIGLOBE`、`plala`、`Rakuten`、`OCN` → `Japan`；`Singtel`、`StarHub`、`MyRepublic`、`ViewQwest`、`M1` → `Singapore`；`AT&T` / `ATT`、`Verizon`、`Comcast` / `Xfinity`、`Spectrum` / `Charter`、`Cox`、`Frontier`、`CenturyLink`、`Quantum Fiber`、`Optimum`、`T-Mobile` → `United States`。`HomeProxy` 仍保留给手工命名的既有节点，但 Google/Gemini 现在使用 `TaiWan`。

这些是节点分类线索，不是路由规则；无法确定地区的节点仍保留在 `Proxy` 中供手动选择。为避免跨地区误匹配，未使用过短或可能跨地区的关键词，例如 `au`、`So-net`。

NSFW/成人内容单独维护在 `rules/nsfw.list`，其中包含从 DAE 展开的 Ehentai、PikPak、OneDrive、MissAV、JavDB、Jable 及显式成人站点。`hentaiverse.org` 是例外：因为 DAE 在成人规则之前已将它分到 `HongKong`，Surge 也保持该优先级。未命中的请求由当前 Profile 的 `FINAL,Proxy` 兜底，与 DAE 的 `fallback: proxy` 对齐。

大体量或维护成本高的板块优先引用成熟的公开 Surge Rule Set（当前采用 blackmatrix7 的 YouTube、Telegram、Google、Gemini、OpenAI、Anthropic、Claude、Bloomberg、ThomsonReuters、PayPal、Cryptocurrency、Twitter、Reddit、Spotify、GitHub、OneDrive、Dropbox、Twitch、Discord、Docker 和 Fox），本仓库的本地 `.list` 负责补充小范围规则和明确的私有分流意图。`category-porn` 没有合适的 BlackMatrix/Sukka 完整替代，因此使用 Workflow 生成的独立规则文件并实际分配给 `Boom`。外部规则文件只写匹配条件，不写策略名称；策略绑定统一留在主 Profile，便于以后替换策略组。

## 从 dae 配置迁移

本仓库的板块划分参考 `mt6000` 上现有 dae 配置中的实际意图：AI、金融、YouTube、Twitch、Telegram、社交、云盘和下载等。dae 的 `geosite`、`geoip`、`pname`、`sip`、`mac` 等匹配能力不能总是逐条等价转换成 Surge 规则，因此迁移时遵循三条原则：

- 能安全表达的公共域名，迁移为 `DOMAIN-SUFFIX`；
- 设备 IP、MAC、节点 IP、私有域名和订阅内容，保留在私有覆盖配置中；
- dae 的 `direct`、`proxy`、`block` 先映射为 Surge 的 `DIRECT`、`Proxy`、`REJECT`，更细的策略组暂时只写在注释中。

当前 `proxy.list` 的注释会标出未来策略，例如“未来策略：sg”“未来策略：tw”“未来策略：hk”或“未来策略：ctm”。这不是 Surge 当前已经存在的策略组名称，而是迁移标记。特别是 Google 系 AI 与其他 AI 已经分成两个独立区块。

每个外部 `RULE-SET` 文件只写匹配条件，不重复写策略名称：

```text
# rules/proxy.list
DOMAIN-SUFFIX,github.com
DOMAIN-SUFFIX,example.org
```

主 Profile 再指定策略：

```ini
[Rule]
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/direct.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/reject.list,REJECT
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy.list,Proxy
FINAL,DIRECT
```

Surge 支持从 URL 加载外部 Rule Set，并会进行缓存和定期更新。[Rule Sets](https://manual.nssurge.com/rules/ruleset.html)

## 规则顺序

规则顺序就是行为的一部分。建议按照以下思路排序：

1. 特别明确的例外；
2. 局域网和本地地址；
3. 拦截规则；
4. 代理规则；
5. 地区或网络环境规则；
6. `FINAL`。

不要在 `FINAL` 后继续放规则，因为它们不会再被执行。

## 规则命名和提交规范

规则文件中的注释应说明：

- 规则解决什么问题；
- 添加日期；
- 来源或验证方式；
- 是否可能影响其他域名。

提交信息建议使用：

```text
rules: add domain for service X
rules: remove obsolete endpoint Y
rules: fix rule order for app Z
```

## 规则集与完整 Profile 的区别

- `RULE-SET`：适合公开的域名/IP 列表；
- Managed Profile：适合由 URL 提供一整份 Profile；
- 本地 Profile：适合包含个人节点和私有设置的配置。

不要因为 GitHub 能公开访问，就把完整个人 Profile 直接公开。公开规则和私有节点应分离。
