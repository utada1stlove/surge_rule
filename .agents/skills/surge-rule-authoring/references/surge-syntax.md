# Surge 规则编写参考

## Profile 的基本关系

```text
[Proxy]       定义代理策略
[Proxy Group] 组织节点和选择逻辑
[Rule]        将匹配条件映射到策略
```

主 `[Rule]` 中的规则从上到下匹配，第一条命中生效；`FINAL` 应放在主规则的最后。

## 常用规则

```ini
DOMAIN,example.com,Proxy
DOMAIN-SUFFIX,example.com,Proxy
DOMAIN-KEYWORD,example,Proxy
IP-CIDR,192.168.0.0/16,DIRECT
GEOIP,CN,DIRECT
RULE-SET,https://example.com/rules.list,Proxy
FINAL,DIRECT
```

外部 Rule Set 文件不写策略列：

```text
DOMAIN-SUFFIX,example.com
IP-CIDR,192.168.0.0/16
```

## 公共规则仓库的推荐加载方式

```ini
[Rule]
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/direct.list,DIRECT
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/reject.list,REJECT
RULE-SET,https://raw.githubusercontent.com/USER/REPO/main/rules/proxy.list,Proxy
FINAL,DIRECT
```

## 规则顺序

建议顺序是：环路和局域网例外、明确的直连/拒绝例外、业务分类、宽泛规则、`FINAL`。如果两个业务分类目前使用同一个策略，顺序仍应按未来拆分后的策略意图设计。

## 不能直接假设的转换

- dae 的 `geosite:*` 不等于 Surge 的内置数据集；需要具体域名、可接受的外部 Rule Set 或明确标注未迁移；
- dae 的 `sip`、`mac`、`pname`、网卡和端口规则通常属于私有环境，不能放入公共域名规则；
- dae 的 `must_direct`、DNS 劫持和底层透明代理行为不能简单替换成 `DIRECT`；
- DAE 的节点筛选条件不是 Surge 的规则，应留在策略组或私有配置中；
- `REJECT` 规则需要单独验证误杀，不能为了“看起来完整”批量加入。
