# 从 dae 分流迁移到 Surge

## 迁移目标

mt6000 上的 dae 配置采用“先保护基础流量，再按业务分类”的顺序：

```text
环路保护
  → 局域网 / 私有地址
  → 设备和节点例外
  → 业务板块
  → QUIC / 广告处理
  → CN / GFW / fallback 兜底
```

Surge 的公开规则仓库目前只保留三种总策略：`DIRECT`、`Proxy`、`REJECT`。原 dae 中的 `hk`、`sg`、`us`、`stream`、`ctm`、`boom`、`udp` 等组，先作为注释中的未来策略标记，不直接写入不存在的 Surge 策略组。

## 当前迁移表

| dae 意图 | Surge 当前落点 | 未来拆分 |
|---|---|---|
| 局域网、私有地址、组播 | `direct.list` → `DIRECT` | 保持直连 |
| 节点服务器 IP 例外 | 私有覆盖文件 | 保持直连 |
| OpenAI / Anthropic / 其他 AI | `proxy.list` → `Proxy` | `sg` 或 AI 组 |
| Google AI / Gemini | `proxy.list` → `Proxy` | `tw` 或 Google AI 组 |
| 金融服务 | `proxy.list` → `Proxy` | `hk` |
| YouTube | `proxy.list` → `Proxy` | `ctm` |
| Twitch | `proxy.list` → `Proxy` | `stream` |
| Telegram | `proxy.list` → `Proxy` | `boom` |
| Twitter / Reddit | `proxy.list` → `Proxy` | `sg` |
| Spotify / PayPal / Fox | `proxy.list` → `Proxy` | `us` |
| 中国服务、Steam 内容 | `direct.list` → `DIRECT` | 保持直连 |
| 广告与跟踪 | `reject.list` 暂留空 | 独立清单后再启用 |

## 暂不迁移的 dae 规则

以下规则涉及个人环境或 Surge 没有直接等价表达的能力，不能直接公开复制：

- 订阅 URL 和具体节点筛选条件；
- 节点服务器 IP；
- 家庭设备 IP、MAC 地址和设备注释；
- 个人域名、内网服务和自建 API；
- dae 的 `must_direct`、进程名、网卡、源 IP、UDP 端口等底层路由规则；
- `geosite:gfw`、`geosite:cn` 等数据集的完整内容。

Google 系分流需要特别注意规则覆盖：dae 中的 Google AI 规则排在通用兜底之前，并排除了 `google-cn` 和 YouTube。Surge 这里先使用更具体的 Google AI 域名作为独立区块；如果以后增加宽泛的 `google.com` 规则，必须继续保持 Google AI 区块在前，或者直接拆成独立 Rule Set。

这些内容如果确实需要，应放进本地私有覆盖层，并单独验证，不放入公开 GitHub 规则仓库。

## 未来拆分方式

当 Surge 中准备好多个策略组后，可以把当前带注释的区块拆成：

```text
rules/
  proxy/
    ai.list
    finance.list
    video.list
    social.list
    messaging.list
    download.list
```

再在主 Profile 中分别引用：

```ini
[Rule]
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy/ai.list,AI
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy/video.list,Stream
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy/social.list,US
```

在完成拆分前，保持单一 `Proxy` 组更容易测试和回滚。
