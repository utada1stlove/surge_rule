# 托管 Profile 与手改副本

记录日期：2026-09-09（Asia/Singapore）。来源：用户对 Surge iPhone 实际行为的确认，以及本仓库模板结构。

## 结论

Surge 不能修改托管规则。带 `#!MANAGED-CONFIG` 首行的 Profile 在设备上是只读的运行副本，Surge 会按 `interval` 从远端重新拉取并覆盖，App 内也没有可保存的编辑入口。

想要手改，就要复制托管规则：复制出来的副本会丢掉首行的托管声明，上面的代码就消失了，变成一份普通的本地 Profile，可以自由编辑，也不再被远端覆盖。

因此托管与手改是两条互斥的路径，不需要在下载前删掉首行——复制这个动作本身就完成了去托管。

## 两条复制路径

### 路径一：在 Surge 内复制（推荐）

1. 打开「配置与插件」，找到已安装的托管 Profile；
2. 进入该 Profile 的操作菜单，选择复制/另存为本地配置；
3. 打开副本确认首行 `#!MANAGED-CONFIG` 已不存在；
4. 编辑副本并切换使用，原托管 Profile 保留作为回滚基线。

### 路径二：从 GitHub 下载 Raw 后导入

本仓库为公开仓库，Rule Set 与 Profile 都是绝对 Raw 地址，可以直接下载：

```bash
curl -LO https://raw.githubusercontent.com/utada1stlove/surge_rule/main/profiles/surge/1.0.0.conf
```

浏览器打开 Raw 链接后，用 iPhone 的「共享 → 拷贝到文件」也可以拿到同一份文本。

从 GitHub Raw 下载的模板首行是占位符（`__MANAGED_CONFIG_URL__` 不是合法 URL），本身不构成可用的托管地址；从私有渲染服务安装的托管链接会注入真实地址，需要手改时走路径一复制，那一行就没了。

## 复制成手改版后仍需处理的位置

| 位置 | 是否要改 | 说明 |
| --- | --- | --- |
| 首行 `#!MANAGED-CONFIG` | 不用管 | 复制副本会去掉这一行；从 Raw 下载的模板里它只是占位符，不是可用托管地址 |
| `Proxy = select, policy-path="__SUBSTORE_URL__"` | 必须改 | 换成自己的 Sub-Store Surge 输出地址，或在 `[Proxy]` 段写死节点；否则没有可用出口，兜底规则只剩直连 |
| `[Proxy]` 段 | 可选 | 手改场景更倾向直接写节点，不依赖订阅 |
| `[Rule]` 与各 Rule Set URL | 不用改 | 全部是绝对 URL，指向 GitHub，导入后继续自动更新 |
| `icon-url` | 不用改 | 同样是绝对 URL |

手改之后 Profile 文本不再随 GitHub 自动更新：组结构、订阅地址和 `[Rule]` 段都由自己维护。指向本仓库的外部 Rule Set 仍会照常更新，这些文件只含匹配条件、不含策略名，所以改组名不会让它们失效。

## 什么时候不该用手改副本

- 规则的顺序、遮蔽、分组归属有问题：这属于源文件缺陷，副本只能止血，正确修复仍要回到仓库；
- 副本只用于临时验证某几条规则；验证完把结论提回仓库，避免副本和仓库长期分叉；
- 不需要副本的场景优先继续用托管 Profile；版本升级或回滚走
  `config/private-profile-templates.json` 的 `source`，不需要本地副本。

副本不影响的部分：外部 Rule Set 与图标一律是绝对 Raw 地址（本仓库全部 `RULE-SET` 引用均为 `https://`，无相对路径），下载后不会因为托管模式而解析失败。

## 相关文件

- [Surge 外部资料知识库](surge-resources.md)
- [GitHub 维护流程](../operations/github-maintenance.md)
- [私有 Profile 渲染服务](../operations/private-profile-service.md)
- 手改友好的样板：`legacy/profile.example.conf`（冻结样板，无托管声明）、
  `profiles/simple/1.0.0.conf`、`profiles/home-wg/1.0.0.conf`（本就为手填
  WireGuard 参数设计）
