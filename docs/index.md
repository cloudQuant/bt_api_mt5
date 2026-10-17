# MetaTrader 5 provider status

## English

bt_api_mt5 currently advertises an unavailable provider: it declares no supported exchange or asset type. Its legacy gateway adapter and Base Gateway export have been removed. This repository does not provide a direct MT5 feed, account-session provider, managed market provider, or ServiceHost order-entry capability.

Older examples that construct a gateway adapter are obsolete. Package installation alone does not provide terminal connectivity, market data, account queries, or order operations. ServiceHost integration and managed writes through ServiceExecutionSession/service-v2 are also not implemented here.

## 中文

bt_api_mt5 当前声明 provider 不可用，未声明受支持的交易所或资产类型。旧 gateway adapter 与 Base Gateway 导出已经移除。本仓库未提供 MT5 直连 feed、账户会话 provider、托管行情 provider 或 ServiceHost 下单能力。

旧版创建 gateway adapter 的示例已经过时。单独安装本包不会提供终端连接、行情、账户查询或订单操作。此仓库也尚未实现 ServiceHost 集成或通过 ServiceExecutionSession/service-v2 托管写入。
