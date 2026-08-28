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

这些板块目前都会统一交给 `Proxy` 策略组。`reject.list` 已有一组保守的广告/测量域名，完整广告清单暂作为可选外部 Rule Set。以后可以将某个板块拆成独立的 `.list` 文件，再在主 Profile 中交给不同策略组。

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
