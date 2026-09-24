# Surge 主配置 Smart 权重

本文档对应当前活动入口 [profiles/surge/surge.conf](surge.conf)，当前版本为 `1.3.2`；权重来源是该入口 `[Proxy Group]` 中 `Smart`、`Smart-Unlimited` 和 `Smart-US` 的实际 `policy-priority`。版本历史见 [CHANGELOG.md](CHANGELOG.md)，节点命名约定见 [docs/operations/surge-smart-node-naming.md](../../docs/operations/surge-smart-node-naming.md)。

## 首条匹配

Surge 的 `policy-priority` 按从左到右的首条匹配规则选择倍率，不会把多个规则的倍率自动相乘。因此配置中已经将区域与节点类型的组合预先写成最终权重；同一节点名应使用 `-`、`_`、空格、`=` 或方括号分隔标签。规则使用显式大小写字符类，不使用 `(?i)`、负向前瞻或非捕获组。

## Smart

| 权重 | 命中标签 | 说明 |
| ---: | --- | --- |
| `0.65` | `VOL`、HS 类节点 | 流量较贵的主力线路 |
| `0.85` | `TX`、`CTM-SS` | TX 优先线路 |
| `0.95` | 普通美国节点 | 不含 `HY2` 的美国节点 |
| `1.25` | `BOOM`、`AWS`、`CFT` | 大流量备用线路 |
| `1.35` | `HY2` | 其他 HY2 节点 |

区域组合会覆盖基础档位，例如 `CTM [TX]` 为 `2.125`，`HK [VOL]` 为 `1.625`，`Singapore [VOL]` 为 `0.325`。`TX` 组合优先于 VOL/HS 组合。

## Smart-Unlimited

| 权重 | 命中标签 | 说明 |
| ---: | --- | --- |
| `0.8` | `TX`、`CTM-SS` | 大流量 TX 主力 |
| `1.1` | `AWS`、`CFT` | AWS/CFT 中间档 |
| `1.4` | 日本 `HY2` | 日本 HY2 备用 |

组合示例：`CTM [TX]` 为 `2.0`，`Singapore [AWS]` 为 `0.55`，`TX-Singtel` 为 `0.4`。这些数值直接来自当前入口配置，不是对 `Smart` 权重的继承。

## Smart-US

该组通过 `policy-regex-filter` 只保留 `LAX` 节点，当前优先级为：

| 权重 | 命中标签 | 说明 |
| ---: | --- | --- |
| `0.7` | `EB`，不含 `HY2` | EB Snell |
| `1.0` | `EB` + `HY2` | EB HY2 |
| `1.1` | 普通美国节点，不含 `HY2` | 美国普通线路 |
| `1.3` | `CN2` + `HY2` | 电信优先线路 |
| `1.5` | `HY2` | 其他 HY2 |

示例：`LAX-EB` 为 `0.7`，`LAX [EB] [HY2]` 为 `1.0`，`LAX [CN2] [HY2]` 为 `1.3`，`LAX-Pro` 为 `1.1`。

## 维护边界

所有业务出口均直接提供完整的一级节点组候选；`Proxy` 仍保留为节点组聚合页，`All Nodes`
仅作为订阅入口和筛选组的内部来源，不直接作为业务出口选项。

本文档以 `1.3.2` 活动入口和同版本快照为准；新增节点标签时，先确认它是否能被现有正则命中，再同时更新入口、快照、CHANGELOG 和本说明。不要修改既有 Smart 算法来“简化”文档中的权重；组合规则必须继续放在对应通用规则之前。