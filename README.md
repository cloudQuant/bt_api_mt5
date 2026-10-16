# MetaTrader 5 provider status

## English

The bt_api_mt5 package currently declares its provider unavailable. Its plugin returns no supported exchanges or asset types. The legacy gateway runtime remains in the source tree pending the complete migration, but is retired and unsupported as a public integration. There is no supported direct MT5 feed or standalone gateway API in this package.

Installing the package does not connect to an MT5 terminal or make trading and market-data operations available. Do not use examples from older adapter documentation as current API guidance.

A future MT5 provider must be integrated with the host's direct provider interfaces. Managed live writes belong to ServiceExecutionSession through service-v2 after that integration exists. This package does not currently provide that integration.

## 中文

bt_api_mt5 当前将 provider 声明为不可用。插件不声明受支持的交易所或资产类型。完整迁移尚未完成，旧 gateway runtime 仍保留在源码树中，但已退役，不再作为受支持的公共集成接口。本包当前没有受支持的 MT5 直连 feed 或独立网关 API。

安装本包不会自动连接 MT5 终端，也不会开放交易或行情操作。旧版 adapter 文档不再代表当前 API。

后续 MT5 provider 必须接入宿主的直连 provider 接口。完成集成后，托管实盘写操作应通过 service-v2 的 ServiceExecutionSession。当前包尚未提供该集成。
