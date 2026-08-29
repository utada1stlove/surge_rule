# Geosite 自动生成

本仓库保留一份由 Loyalsoldier 上游生成的 Surge Rule Set 副本。生成清单见
`config/geosite-manifest.json`，每个 geosite 单独输出到 `rules/generated/`，不合并不同集合。

当前生成文件主要用于审计、备用和未来切换。运行时继续优先使用 Sukka、BlackMatrix
等外部规则；但由于没有可直接替代的完整成人规则，`category-porn.list` 是例外，已在
Profile 中实际引用并分配给 `Boom`。

Apple 的普通服务使用 Sukka 的 `apple_services.conf` 并分配给 `US`，中国大陆专用
Apple 域名使用 `apple_cn.conf` 并优先分配给 `DIRECT`。

Workflow 每日下载 Loyalsoldier 的 `geosite.dat`，解析 domain/full/keyword/regexp 类型，转换为
Surge 的 `DOMAIN-SUFFIX`、`DOMAIN`、`DOMAIN-KEYWORD`、`DOMAIN-REGEX`，并对每个文件去重和排序。

不生成 `gfw`、`category-games@cn`，也不迁移 DAE 的 MAC、SIP、进程、网卡、端口、节点 IP
等私有或内核级规则。上游项目使用 GPL-3.0，本仓库保留来源链接，不修改上游内容。
