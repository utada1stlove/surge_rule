# DAE → Surge 迁移参考

## mt6000 当前意图

从 `/etc/dae/config.dae` 读取到的公开可迁移意图如下：

| DAE 区块 | 当前 Surge 文件 | 未来策略标记 |
|---|---|---|
| `direct`：局域网、私有地址、组播 | `rules/direct.list` | `DIRECT` |
| `direct`：中国服务和 Steam 内容 | `rules/direct.list` | `DIRECT` |
| AI：OpenAI / Anthropic | `rules/proxy.list` | `sg` |
| AI：Google / Gemini | `rules/proxy.list` | `tw` |
| Finance | `rules/proxy.list` | `hk` |
| YouTube | `rules/proxy.list` | `ctm` |
| Twitch | `rules/proxy.list` | `stream` |
| Telegram | `rules/proxy.list` | `boom` |
| Twitter / Reddit | `rules/proxy.list` | `sg` |
| Spotify / PayPal / Fox | `rules/proxy.list` | `us` |
| OneDrive / Dropbox / PikPak | `rules/proxy.list` | 待拆分 |
| Ads / tracking | `rules/reject.list` | 待审查 |

当前仓库只使用 `DIRECT`、`Proxy` 和 `REJECT` 三个公开策略。未来策略标记是注释，不是可以直接填入 `RULE-SET` 的策略名称。

## 顺序原则

迁移时保留以下优先级：

1. 环路保护和本地地址；
2. 私有设备、节点 IP 和自建服务例外；
3. 业务分类；
4. QUIC、广告或其他广泛匹配；
5. CN / GFW 兜底；
6. `FINAL`。

Google AI 必须在宽泛的 `google.com` 规则之前，未来拆组时才能保持 Google AI 与其他 Google 流量的区分。

## 不公开迁移

以下内容来自个人运行环境，不能复制到公开仓库：

- 订阅 URL、节点名称和筛选条件；
- 节点 IP 和自建服务域名；
- 家庭设备 IP、MAC 和设备注释；
- DAE 的 DNS 上游、网卡和本机进程规则；
- 真实密钥、密码和 Controller 配置。

这些内容只能在私有 Profile 或本地覆盖层中维护。
