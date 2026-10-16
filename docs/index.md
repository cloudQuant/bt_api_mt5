# MetaTrader 5 provider status

## English

bt_api_mt5 currently advertises an unavailable provider: it declares no supported exchange or asset type. The legacy gateway package remains in the source tree pending the complete migration, but is retired and unsupported as a public integration. This repository does not currently expose a direct MT5 feed.

Older examples that construct a gateway adapter are obsolete. Package installation alone does not provide terminal connectivity, market data, account queries, or order operations. ServiceHost integration and managed writes through ServiceExecutionSession/service-v2 are also not implemented here.

## 中文

bt_api_mt5 当前声明 provider 不可用，未声明受支持的交易所或资产类型。完整迁移尚未完成，旧 gateway 包仍保留在源码树中，但已退役，不再作为受支持的公共集成接口。本仓库当前没有 MT5 直连 feed。

旧版创建 gateway adapter 的示例已经过时。单独安装本包不会提供终端连接、行情、账户查询或订单操作。此仓库也尚未实现 ServiceHost 集成或通过 ServiceExecutionSession/service-v2 托管写入。
