# 安全与隐私

## 可以公开的内容

- 通用域名规则；
- 局域网地址规则；
- 不含凭据的 Profile 模板；
- 使用说明、变更记录和测试方法；
- 不包含个人数据的脚本。

## 不应公开的内容

- 订阅链接；
- 节点地址与密码的组合；
- UUID、PSK、Token 和 API Key；
- WireGuard 私钥；
- MITM 证书和私钥；
- Controller 密钥；
- 包含真实请求域名的完整日志。

即使仓库是私有的，也不要把它当成专用密码管理器。凭据应放在专门的密码管理工具或受控的本地配置中。

## Controller 远程访问

Surge 支持通过 `external-controller-access` 让外部控制器操作实例，格式示例为：

```ini
external-controller-access = key@192.168.1.10:6165
```

这类访问应限制在可信网络，使用强密钥，并避免端口暴露到公网。官方 CLI 文档要求远程实例启用该能力，并支持通过安全提示、环境变量或标准输入提供密码。[CLI](https://manual.nssurge.com/tools/cli.html) [General Options](https://manual.nssurge.com/profile/general.html)

## MITM

MITM 会扩大 Surge 能观察和处理的内容范围，只在明确需要调试 HTTPS 时启用，并认真管理证书。普通分流不需要启用 MITM。

## 发现泄露后的处理

如果凭据已经提交到 GitHub：

1. 立即撤销或轮换凭据；
2. 停止继续使用旧订阅或密钥；
3. 从当前分支移除泄露内容；
4. 检查访问日志和异常流量；
5. 再处理 Git 历史清理。

仅删除当前文件不能保证历史中的秘密消失，因此凭据轮换优先于历史清理。
