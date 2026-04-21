# MetaTrader 5 Documentation

## English

Welcome to the MetaTrader 5 gateway adapter documentation for bt_api.

`bt_api_mt5` connects to MetaTrader 5 terminals via the `pymt5` WebSocket client, providing a unified trading and market data interface for the bt_api framework.

### Features

- Real-time tick data via WebSocket push
- Order placement — market, limit, stop orders with SL/TP
- Position & balance tracking
- Historical bars (M1 to MN1 timeframes)
- Symbol subscription with batch support
- Order management (place, cancel, track)

### Installation

```bash
pip install bt_api_mt5
```

### Quick Start

```python
from bt_api_mt5 import Mt5GatewayAdapter

adapter = Mt5GatewayAdapter(
    login=12345678,
    password="your_password",
    ws_uri="ws://localhost:8080",
)
adapter.connect()
adapter.subscribe_symbols(["EURUSD", "GBPUSD"])
balance = adapter.get_balance()
positions = adapter.get_positions()
adapter.disconnect()
```

### API Reference

#### `Mt5GatewayAdapter`

**Initialization Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `login` | `int` | Yes | MT5 account login ID |
| `password` | `str` | Yes | MT5 account password |
| `ws_uri` | `str` | Yes | MT5 WebAPI WebSocket URI (e.g., `ws://localhost:8080`) |
| `timeout` | `float` | No | Request timeout in seconds (default: 60.0) |
| `heartbeat_interval` | `float` | No | WebSocket heartbeat interval (default: 30.0) |
| `auto_reconnect` | `bool` | No | Auto-reconnect on disconnect (default: True) |
| `max_reconnect_attempts` | `int` | No | Max reconnect attempts (default: 5) |
| `symbol_suffix` | `str` | No | Suffix appended to all symbols |
| `symbol_map` | `dict` | No | Mapping from bt_api symbols to MT5 symbols |

**Methods:**

| Method | Description |
|--------|-------------|
| `connect()` | Establish WebSocket connection to MT5 terminal |
| `disconnect()` | Close connection gracefully |
| `subscribe_symbols(symbols)` | Subscribe to real-time updates for given symbols |
| `get_balance()` | Returns account balance, equity, margin info |
| `get_positions()` | Returns list of open positions |
| `place_order(payload)` | Place a market/limit/stop order |
| `cancel_order(payload)` | Cancel a pending order by order_id |
| `get_bars(symbol, timeframe, count)` | Get historical OHLCV bars |
| `get_symbol_info(symbol)` | Get symbol contract specifications |
| `get_open_orders()` | Returns list of open (pending) orders |

**Order Payload:**

```python
{
    "symbol": "EURUSD",      # Trading symbol
    "volume": 0.1,           # Volume in lots
    "price": 1.0850,         # Limit price (for limit/stop orders)
    "order_type": "limit",    # "market", "limit", "stop"
    "direction": "buy",       # "buy" or "sell"
    "sl": 1.0800,            # Stop loss price (optional)
    "tp": 1.0900,            # Take profit price (optional)
    "comment": "order comment"  # Optional comment
}
```

**Timeframe Constants:**

| Timeframe | Minutes |
|-----------|---------|
| `M1` | 1 |
| `M5` | 5 |
| `M15` | 15 |
| `M30` | 30 |
| `H1` | 60 |
| `H4` | 240 |
| `D1` | 1440 |
| `W1` | 10080 |
| `MN1` | 43200 |

### Platform Requirements

- **Windows/macOS**: MT5 terminal with WebAPI enabled required
- **Linux**: Can install the package, but requires remote MT5 terminal for connection
- **Python**: 3.9+

### Resources

- [GitHub Repository](https://github.com/cloudQuant/bt_api_mt5)
- [Issue Tracker](https://github.com/cloudQuant/bt_api_mt5/issues)
- [bt_api Framework](https://github.com/cloudQuant/bt_api_py)

---

## 中文

欢迎使用 bt_api 框架的 MetaTrader 5 网关适配器文档。

`bt_api_mt5` 通过 `pymt5` WebSocket 客户端连接 MetaTrader 5 终端，为 bt_api 框架提供统一的交易和行情数据接口。

### 功能特点

- WebSocket 推送实时 tick 行情
- 下单 — 市价单、限价单、止损单，支持 SL/TP
- 持仓与余额查询
- 历史 K 线（M1 到 MN1 时间周期）
- 品种批量订阅
- 订单管理（下单、撤单、查询）

### 安装

```bash
pip install bt_api_mt5
```

### 快速开始

```python
from bt_api_mt5 import Mt5GatewayAdapter

adapter = Mt5GatewayAdapter(
    login=12345678,
    password="your_password",
    ws_uri="ws://localhost:8080",
)
adapter.connect()
adapter.subscribe_symbols(["EURUSD", "GBPUSD"])
balance = adapter.get_balance()
positions = adapter.get_positions()
adapter.disconnect()
```

### API 参考

#### `Mt5GatewayAdapter`

**初始化参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `login` | `int` | 是 | MT5 账户登录名 |
| `password` | `str` | 是 | MT5 账户密码 |
| `ws_uri` | `str` | 是 | MT5 WebAPI WebSocket 地址（如 `ws://localhost:8080`）|
| `timeout` | `float` | 否 | 请求超时时间秒数（默认：60.0）|
| `heartbeat_interval` | `float` | 否 | WebSocket 心跳间隔（默认：30.0）|
| `auto_reconnect` | `bool` | 否 | 断线自动重连（默认：True）|
| `max_reconnect_attempts` | `int` | 否 | 最大重连次数（默认：5）|
| `symbol_suffix` | `str` | 否 | 附加到所有品种的后缀 |
| `symbol_map` | `dict` | 否 | bt_api 品种名到 MT5 品种名的映射 |

**方法：**

| 方法 | 说明 |
|------|------|
| `connect()` | 建立到 MT5 终端的 WebSocket 连接 |
| `disconnect()` | 优雅关闭连接 |
| `subscribe_symbols(symbols)` | 订阅指定品种的实时行情 |
| `get_balance()` | 返回账户余额、权益、保证金信息 |
| `get_positions()` | 返回持仓列表 |
| `place_order(payload)` | 下市价单/限价单/止损单 |
| `cancel_order(payload)` | 按 order_id 撤销待成交订单 |
| `get_bars(symbol, timeframe, count)` | 获取历史 OHLCV K 线 |
| `get_symbol_info(symbol)` | 获取品种合约规格 |
| `get_open_orders()` | 返回挂单列表 |

**下单参数：**

```python
{
    "symbol": "EURUSD",      # 交易品种
    "volume": 0.1,           # 委托数量（手）
    "price": 1.0850,         # 委托价格（限价单/止损单）
    "order_type": "limit",    # "market", "limit", "stop"
    "direction": "buy",       # "buy" 或 "sell"
    "sl": 1.0800,            # 止损价格（可选）
    "tp": 1.0900,            # 止盈价格（可选）
    "comment": "订单备注"       # 可选备注
}
```

**时间周期常量：**

| 时间周期 | 分钟数 |
|---------|--------|
| `M1` | 1 |
| `M5` | 5 |
| `M15` | 15 |
| `M30` | 30 |
| `H1` | 60 |
| `H4` | 240 |
| `D1` | 1440 |
| `W1` | 10080 |
| `MN1` | 43200 |

### 平台要求

- **Windows/macOS**：需要 MT5 终端并启用 WebAPI
- **Linux**：可以安装包，但需要远程 MT5 终端才能建立连接
- **Python**：3.9+

### 相关资源

- [GitHub 仓库](https://github.com/cloudQuant/bt_api_mt5)
- [问题反馈](https://github.com/cloudQuant/bt_api_mt5/issues)
- [bt_api 框架](https://github.com/cloudQuant/bt_api_py)
