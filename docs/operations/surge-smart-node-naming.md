# Surge Smart 节点命名与权重对照

当前版本：`1.1.9`。

这份文档只记录“节点显示名”和 `policy-priority` 权重之间的对应关系。当前不做 Sub-Store 自动补协议标签，所以 Surge 只能根据节点名字里的关键词判断权重。

真实规则在 [profiles/surge/surge.conf](../../profiles/surge/surge.conf) 的 `[Proxy Group]` 段里，重点是这三行：

- `Smart`
- `Smart-Unlimited`（1.1.5 前叫 `Smart-TX-CFT`）
- `Smart-US`

## 通用命名规则

1. 关键词尽量独立出现，前后使用 `-`、`_`、空格、`=`、`[` 或 `]`。  
   例如 `TX-Singtel`、`LacusClyne [TX] [ss]` 稳，`TXSingtel` 可能不稳。
2. 匹配兼容大小写。`tx`、`TX`、`Tx` 都可以；实现使用显式大小写字符类，不在
   `policy-priority` 里写 `(?i)`、负向前瞻等复杂构造，否则 Surge 可能把整条策略组判为无效。
3. `HY2` 节点名字里必须带 `HY2`，否则 `Smart` 和 `Smart-US` 无法把它当成 HY2。
4. 美国组里 `EB`、`CN2` 必须写在名字里，否则无法区分联通/移动优先和电信优先。
5. `aws`、`cft` 是 AWS/CFT 大流量低权重分支，不要让主力 HS/VOL 节点误带这些词。
6. `[TX]` 标签会优先于 `[vol]`，因此 `CTM [TX] [ss]` 会先走 TX 基准，再应用 CTM 区域倍率。
7. 标签式命名使用方括号，例如 `CTM [vol] [ss]`、`HKBN [vol] [snell]`、`LacusClyne [TX] [ss]`。

## Smart：全体节点竞技场

| 档位 | 权重 | 命中关键词 | 说明 |
|---|---:|---|---|
| TX | `0.85` | `TX`、`CTM-SS` | 基础权重最高，优先于 VOL/HS |
| VOL/HS 主力 | `0.75` | `VOL`、`CTM`、`HK`、`JP`、`HKBN`、`SINGTEL`、`SINGAPORE`、`MISAKA`、`AKARI` | 适合流量贵的 HS/VOL 服务器 |
| HY2 | `1.35` | `HY2` | 排在美国普通节点和 AWS/CFT 前 |
| AWS/CFT/Boom | `1.25` | `BOOM`、`AWS`、`CFT` | 降低权重，适合备用或特定业务 |
| 美国普通/Snell | `0.95` | `US`、`USA`、`LAX`、`LOS ANGELES`、`美国`、`AT&T`、`VERIZON`、`COMCAST`、`XFINITY` 等，且不带 `HY2` | 美国 Snell 或普通美国节点备用 |

注意：`VOL/HS` 分支会排除 `TX`、`BOOM`、`AWS`、`CFT`、`HY2`、`CTM-SS`。  
所以 `TX-Misaka-Singapore` 会走 TX `0.85`，不会走 HS/VOL `0.75`。

## 区域倍率

`Smart` 和 `Smart-Unlimited` 会先确定基础权重，再乘以节点名中的区域倍率。
Surge 的 `policy-priority` 是首条匹配生效，所以配置里已经写好组合规则：

| 区域 | 倍率 | 命中关键词 |
|---|---:|---|
| CTM | `x2.5` | `CTM` |
| HK | `x2.5` | `HK`、`HKBN`、`HongKong`、`Hong Kong` |
| SG | `x0.5` | `SG`、`Singapore`、`Singtel` |

常用组合示例：

| 节点名 | 基础权重 | 最终权重 |
|---|---:|---:|
| `CTM [TX] [ss]` | `0.85` | `2.125` |
| `CTM [vol] [ss]` | `0.75` | `1.875` |
| `HK [vol] [snell]` | `0.75` | `1.875` |
| `Singapore [aws] [cft]` | `1.25` | `0.625` |
| `Singapore [vol] [ss]` | `0.75` | `0.375` |

在 `Smart-Unlimited` 里，`CTM [TX]` 为 `0.8 x 2.5 = 2.0`，
`Singapore [aws] [cft]` 为 `1.1 x 0.5 = 0.55`，`TX-Singtel` 为 `0.8 x 0.5 = 0.4`。

## Smart-Unlimited：流量不贵优先

| 档位 | 权重 | 命中关键词 | 说明 |
|---|---:|---|---|
| TX | `0.8` | `TX`、`CTM-SS` | TX 质量稳定、流量无限，优先 |
| AWS/CFT | `1.1` | `AWS`、`CFT` | 中间档 |
| 日本 HY2 | `1.4` | `JP`/`JAPAN`/`日本` + `HY2` | 最后档 |

适合这个组的节点名示例：

```text
TX-Singtel
TX-CTM-SS
CTM-SS
Singapore [aws] [cft]
JP [hy2]
```

## Smart-US：美国 IP，流量不贵优先

| 档位 | 权重 | 命中关键词 | 说明 |
|---|---:|---|---|
| EB Snell | `0.7` | `EB`，且不带 `HY2` | 联通/移动优先线路 |
| EB HY2 | `1.0` | `EB` + `HY2` | EB 线路里的 HY2 备用 |
| 其他美国节点 | `1.1` | `US`、`USA`、`LAX`、`LOS ANGELES`、`美国`、美国家宽关键词，且不带 `HY2` | 普通美国节点 |
| CN2 HY2 | `1.3` | `CN2` + `HY2` | 电信优先线路 |
| 其他 HY2 | `1.5` | `HY2` | 最低权重 |

适合这个组的节点名示例：

```text
LAX-EB
LAX-Pro
LAX [eb] [hy2]
LAX [cn2] [hy2]
```

## 推荐改名模板

如果你准备手工改节点名，可以按这个模板来：

```text
CTM [vol] [ss]
CTM [vol] [snell]
HKBN [vol] [ss]
HK [vol] [snell]
JP [vol] [snell]
SINGAPORE [vol] [snell]
Singapore [vol] [ss]
HongKong [vol] [ss]

LacusClyne [TX] [ss]
Aerith [TX] [ss]
Singtel [TX] [snell]
CTM-SS [TX] [ss]

Singapore [aws] [cft]

LAX [eb] [snell]
LAX [pro] [snell]
JP [hy2]
LAX [eb] [hy2]
LAX [cn2] [hy2]
```

## 不命中权重的节点

别人的中立节点，例如 `AnyTLS` 这类名字，如果不含上面的关键词，就不会命中特定权重分支。它们仍然可以参与普通测速，只是不加偏好也不歧视。

## 以后怎么维护

如果节点以后改名：

1. 先看这份文档确认关键词；
2. 去 Sub-Store 改节点显示名；
3. 如果新名字无法命中权重，再回来改 `profiles/surge/surge.conf` 里的 `policy-priority`；
4. 改 Profile 需要升版本并生成快照，见 [Profile 版本化](profile-versioning.md)。

`policy-priority` 的正则本身不能包含 `:`，也不要使用 `(?i)`、负向前瞻或非捕获组等复杂构造；
当前配置只使用普通字符类和 `|`，并用显式字符类处理大小写。
