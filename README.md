# MetaTrader 5 provider status

## English

The `bt_api_mt5` package declares its provider unavailable and returns no supported exchanges or asset types. Its legacy gateway adapter and Base Gateway export have been removed. The package does not provide a direct MT5 feed, account-session provider, managed market provider, or ServiceHost order-entry capability.

Installing the package does not connect to an MT5 terminal or make trading and market-data operations available. Do not use examples from older adapter documentation as current API guidance.

A future MT5 provider must be integrated with the host's direct provider interfaces. Managed live writes belong to ServiceExecutionSession through service-v2 after that integration exists. This package does not currently provide that integration.

## 中文

`bt_api_mt5` 当前将 provider 声明为不可用，插件不声明受支持的交易所或资产类型。旧 gateway adapter 与 Base Gateway 导出已经移除。本包未提供 MT5 直连 feed、账户会话 provider、托管行情 provider 或 ServiceHost 下单能力。

安装本包不会自动连接 MT5 终端，也不会开放交易或行情操作。旧版 adapter 文档不再代表当前 API。

后续 MT5 provider 必须接入宿主的直连 provider 接口。完成集成后，托管实盘写操作应通过 service-v2 的 ServiceExecutionSession。当前包尚未提供该集成。
