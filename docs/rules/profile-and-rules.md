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

当前 `surge-main.conf` 按 DAE 意图固定分配：广告/跟踪到 `REJECT`，Telegram 到 `Boom`，Google 与 Gemini 到 `TaiWan`，Meta（Facebook、Instagram、WhatsApp）到 `Singapore`，Twitter/Reddit 到 `Proxy`，金融分类清单（包括 HSBC、IBKR、uSMART、moomoo、富途、TradingView、Investing.com 等）以及专用 geosite 清单（WSJ、Economist、Bloomberg、Reuters）到 `Finance`，PayPal 到 `United States`，其余板块按既有固定策略映射。`surgeion.conf` 则将 Meta、Twitter、Reddit、PayPal 分别暴露为带图标的 `select` 策略组，便于手动切换出口。

`surge-main.conf` 与 `surgeion.conf` 中，Telegram 走 `Boom`，成人内容走 `Boom`（`surge-main.conf`）和 `Private`（`surgeion.conf`）。`surge.conf` 是从 `surgeion.conf` 派生的独立 Profile，差异之一是把这两类流量拆成自己的策略组：`Telegram.list` 交给 `Telegram`，`rules/nsfw.list` 与 `category-porn.list` 交给 `NSFW`。两个新组的候选项都不含 `Boom`，因此它们不再跟随 Boom/Hy2 节点池；`Telegram` 默认使用自动测速组 `Smart`，`NSFW` 默认使用 `Smart-US`（成人内容多为持续大流量，美国家宽池更稳定）。需要 TX/CFT 出口时可选 `Smart-TX-CFT`，确实要用 Boom 节点时仍可从 `Proxy` 组手动挑选。

`surge.conf` 另有几处绑定与上面两份 Profile 不同（记录日期 2026-09-09，按本地 `git diff` 与 `scripts/lint_surge_profiles.py` 复核）：Google 与 Gemini 不再走 `TaiWan` 外层组，改由独立的 `Google` 组接管（`Gemini.list`、`Google.list`、`rules/google-ai.list`）；Apple 非 CN 服务由 `apple_services.conf` 交给独立的 `Foreign-Apple` 组；加密货币从 `United States` 改到 `Finance`，Fox 从 `United States` 改到显式的 `Proxy` 规则。Twitter 与 Reddit 走各自带图标的 `select` 组，默认项是 `HomeProxy`；由于 `HomeProxy` 自身的默认项是 `Smart`，默认出口与改动前一致，家宽节点变成手选入口。该 Profile 因此不再引用 `rules/social-sg.list`：那份清单的五个域名全部包含在 `Twitter.list` 与 `Reddit.list` 内，只要它排在这两条规则之前，两个组就永不命中。`rules/us-services.list` 同步移除 `spotify.com`、`paypal.com`、`fox.com`，原因相同——它排在各自的业务规则集之前，`Spotify` 组形同虚设。

`TX` 是仅筛选节点名独立 `tx` 标签的策略组，并作为嵌套成员加入 `Boom`；无论是否存在 TX 节点，它都保留 `REJECT` 和 `DIRECT` 两个候选项。因此 Telegram、NSFW 等走 `Boom` 的流量可手动选择 TX，而不需要新增单独的流量规则。

`surge.conf` 的 `Telegram` 与 `NSFW` 组候选项里没有 `Boom`，因此上面的「走 `Boom` 时顺手选 TX」在那份配置里换成 `Smart-TX-CFT`（TX/CFT 自动测速）与 `TX`（手选 `tx` 标签节点，候选含 `REJECT`、`DIRECT`）。`surge.conf` 的 `NSFW` 默认项是 `Smart-US`，其余候选为 `Smart`、`Smart-TX-CFT`、`TX` 和各地区组；`Telegram` 默认项是 `Smart`。`surgeion.conf` 的 `Private` 是同类用途的手选组，默认项 `Smart`，候选里保留 `Boom`。

地区策略组会按节点名识别常见家宽运营商：`HKBN`、`HKT`、`PCCW`、`Netvigator`、`WTT`、`i-Cable`、`SmarTone`、`HGC`、`CMHK` → `HongKong`；`Hinet`、`Chunghwa`、`Seednet`、`Fetnet`、`FarEasTone`、`Taiwan Mobile`、`TWM Broadband` → `TaiWan Nodes`；`SoftBank`、`docomo`、`NTT`、`NURO`、`IIJ`、`BIGLOBE`、`plala`、`Rakuten`、`OCN` → `Japan`；`Singtel`、`StarHub`、`MyRepublic`、`ViewQwest`、`M1` → `Singapore`；`AT&T` / `ATT`、`Verizon`、`Comcast` / `Xfinity`、`Spectrum` / `Charter`、`Cox`、`Frontier`、`CenturyLink`、`Quantum Fiber`、`Optimum`、`T-Mobile` → `United States`。`TaiWan` 外层组默认选择 `TaiWan Nodes`，并提供 `Proxy` 作为手动备用；除 `surge.conf` 外，Google/Gemini 统一使用该外层组以保持出口一致，`surge.conf` 改用独立的 `Google` 组。这些运营商节点也会统一加入 `HomeProxy`，便于手动选择家宽出口。

这些是节点分类线索，不是路由规则；无法确定地区的节点仍保留在 `Proxy` 中供手动选择。为避免跨地区误匹配，未使用过短或可能跨地区的关键词，例如 `au`、`So-net`。

NSFW/成人内容单独维护在 `rules/nsfw.list`，其中包含从 DAE 展开的 Ehentai、PikPak、OneDrive、MissAV、JavDB、Jable 及显式成人站点。`hentaiverse.org` 是例外：因为 DAE 在成人规则之前已将它分到 `HongKong`，Surge 也保持该优先级。由于 DAE 把 `geosite:onedrive`、`geosite:pikpak` 归入大流量板块，这 17 条云盘域名同时写在 `rules/nsfw.list` 里，而该规则集在 `[Rule]` 中先于 blackmatrix7 的 OneDrive/PikPak 规则出现，因此需要显式处理，否则云盘流量会被成人板块抢先命中。`surge.conf` 与 `surgeion.conf` 在 `rules/nsfw.list` 之前引用 `rules/cloud-storage.list`（只写这 17 条 OneDrive/PikPak 匹配条件），把云盘流量交给 `Cloud`（`surge.conf` 中为 `Cloud Box`）；其余 34 条成人站点仍分别进入 `NSFW` 和 `Private`。`surge-main.conf` 没有 `Cloud` 组，沿用 DAE 的归类跟随 `Boom`。未命中的请求由当前 Profile 的 `FINAL,Proxy` 兜底，与 DAE 的 `fallback: proxy` 对齐。

`surge.conf` 的 `Cloud Box` 组覆盖 OneDrive、Google Drive、MEGA、PikPak 与 blackmatrix7 Dropbox 规则集中未被前置规则吸收的部分；`surgeion.conf` 的 `Cloud` 组同理。DAE 的 `geosite:dropbox` 归 `US`，本仓库由 `rules/us-services.list` 保留，因此两个 Profile 里 `dropbox.com` 等域名仍会先走到 `United States` 组，Dropbox 图标只代表该组用途，不代表实际出口。

大体量或维护成本高的板块优先引用成熟的公开 Surge Rule Set（当前采用 blackmatrix7 的 YouTube、Telegram、Google、Gemini、OpenAI、Anthropic、Claude、Bloomberg、ThomsonReuters、PayPal、Cryptocurrency、Twitter、Reddit、Spotify、GitHub、OneDrive、Dropbox、Twitch、Discord、Docker 和 Fox），本仓库的本地 `.list` 负责补充小范围规则和明确的私有分流意图。`category-porn` 没有合适的 BlackMatrix/Sukka 完整替代，因此使用 Workflow 生成的独立规则文件；该规则集在 `surge-main.conf` 分配给 `Boom`、在 `surgeion.conf` 分配给 `Private`、在 `surge.conf` 分配给 `NSFW`。外部规则文件只写匹配条件，不写策略名称；策略绑定统一留在主 Profile，便于以后替换策略组。

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
