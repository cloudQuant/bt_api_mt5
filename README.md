# MetaTrader 5

MetaTrader 5 plugin for bt_api, supporting multi-asset trading via MT5 Web API.

[![PyPI Version](https://img.shields.io/pypi/v/bt_api_mt5.svg)](https://pypi.org/project/bt_api_mt5/)
[![Python Versions](https://img.shields.io/pypi/pyversions/bt_api_mt5.svg)](https://pypi.org/project/bt_api_mt5/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/cloudQuant/bt_api_mt5/actions/workflows/ci.yml/badge.svg)](https://github.com/cloudQuant/bt_api_mt5)
[![Docs](https://readthedocs.org/projects/bt-api-mt5/badge/?version=latest)](https://bt-api-mt5.readthedocs.io/)

---

## English | [中文](#中文)

### Overview

This package provides a **MetaTrader 5 gateway adapter** for the [bt_api](https://github.com/cloudQuant/bt_api_py) framework. It connects to MT5 terminals via the `pymt5` WebSocket client and exposes a unified interface for trading and market data.

### Features

- **MT5 WebSocket connection** via `pymt5` library
- **Real-time tick data** via WebSocket push notifications
- **Order placement** — market, limit, stop orders with SL/TP support
- **Position & balance tracking** — open positions, account balance, equity
- **Historical bars** — M1/M5/M15/M30/H1/H4/D1/W1/MN1 timeframes
- **Symbol subscription** — batch subscribe to multiple symbols
- **Order management** — place, cancel, track open orders

### Requirements

- Python 3.9+
- `bt_api_base >= 0.15`
- `pymt5 >= 0.5.0` (Windows/macOS only — MT5 terminal required)
- A running MT5 terminal with WebAPI enabled

### Installation

```bash
pip install bt_api_mt5
```

Or install from source:

```bash
git clone https://github.com/cloudQuant/bt_api_mt5
cd bt_api_mt5
pip install -e .
```

> **Note:** `pymt5` connects to a running MT5 terminal via WebSocket. MT5 only runs on Windows and macOS. Linux users can install the package but will not be able to establish connections without a remote MT5 terminal.

### Quick Start

```python
from bt_api_mt5 import Mt5GatewayAdapter

# Initialize the adapter
adapter = Mt5GatewayAdapter(
    login=12345678,        # MT5 account login
    password="your_password",
    ws_uri="ws://localhost:8080",  # MT5 WebAPI URI
    symbol_suffix="",      # optional: symbol suffix mapping
)

# Connect to MT5
adapter.connect()

# Subscribe to symbols
adapter.subscribe_symbols(["EURUSD", "GBPUSD"])

# Get account balance
balance = adapter.get_balance()
print(balance)

# Get open positions
positions = adapter.get_positions()
print(positions)

# Place a limit order
order_result = adapter.place_order({
    "symbol": "EURUSD",
    "volume": 0.1,
    "price": 1.0850,
    "order_type": "limit",
    "direction": "buy",
    "sl": 1.0800,
    "tp": 1.0900,
})
print(order_result)

# Cancel an order
cancel_result = adapter.cancel_order({"order_id": 12345678})
print(cancel_result)

# Get historical bars
bars = adapter.get_bars("EURUSD", "H1", 100)
print(f"Got {len(bars)} bars")

# Disconnect
adapter.disconnect()
```

### Supported Operations

| Operation | Method | Status |
|-----------|--------|--------|
| Connect | `connect()` | ✅ |
| Disconnect | `disconnect()` | ✅ |
| Subscribe symbols | `subscribe_symbols(symbols)` | ✅ |
| Account balance | `get_balance()` | ✅ |
| Open positions | `get_positions()` | ✅ |
| Place order | `place_order(payload)` | ✅ |
| Cancel order | `cancel_order(payload)` | ✅ |
| Historical bars | `get_bars(symbol, timeframe, count)` | ✅ |
| Symbol info | `get_symbol_info(symbol)` | ✅ |
| Open orders | `get_open_orders()` | ✅ |

### Order Payload Format

```python
{
    "symbol": "EURUSD",      # Trading symbol
    "volume": 0.1,           # Order volume (lots)
    "price": 1.0850,         # Limit price (for limit/stop orders)
    "order_type": "limit",    # "market", "limit", "stop"
    "direction": "buy",       # "buy" or "sell"
    "sl": 1.0800,            # Stop loss price (optional)
    "tp": 1.0900,            # Take profit price (optional)
    "comment": "order comment"  # Optional comment
}
```

### Symbol Resolution

The adapter maintains a symbol map for mapping bt_api symbol names to MT5 symbol names. Configure it via the `symbol_map` kwarg:

```python
adapter = Mt5GatewayAdapter(
    login=12345678,
    password="your_password",
    ws_uri="ws://localhost:8080",
    symbol_map={
        "EURUSD": "EURUSD",
        "XAUUSD": "GOLD",
    },
    symbol_suffix=""  # optional suffix appended to all symbols
)
```

### Architecture

```
bt_api_mt5/
├── src/bt_api_mt5/
│   ├── __init__.py          # Package init, exports Mt5GatewayAdapter
│   ├── plugin.py            # bt_api plugin registration
│   └── gateway/
│       ├── __init__.py
│       └── adapter.py       # Mt5GatewayAdapter implementation
├── tests/
│   └── conftest.py         # Pytest configuration
└── docs/
    └── index.md            # Documentation
```

### Online Documentation

| Resource | Link |
|----------|------|
| English Docs | https://bt-api-mt5.readthedocs.io/ |
| Chinese Docs | https://bt-api-mt5.readthedocs.io/zh/latest/ |
| GitHub Repository | https://github.com/cloudQuant/bt_api_mt5 |
| Issue Tracker | https://github.com/cloudQuant/bt_api_mt5/issues |

### License

MIT License - see [LICENSE](LICENSE) for details.

### Support

- Report bugs via [GitHub Issues](https://github.com/cloudQuant/bt_api_mt5/issues)
- Email: yunjinqi@gmail.com

---

## 中文

### 概述

本包为 [bt_api](https://github.com/cloudQuant/bt_api_py) 框架提供 **MetaTrader 5 网关适配器**。通过 `pymt5` WebSocket 客户端连接 MT5 终端，提供统一的交易和行情数据接口。

### 功能特点

- **MT5 WebSocket 连接** — 通过 `pymt5` 库连接 MT5 终端
- **实时 tick 数据** — WebSocket 推送行情
- **下单** — 市价单、限价单、止损单，支持 SL/TP
- **持仓与余额查询** — 持仓、账户余额、权益
- **历史 K 线** — M1/M5/M15/M30/H1/H4/D1/W1/MN1 时间周期
- **品种订阅** — 批量订阅多个交易品种
- **订单管理** — 下单、撤单、查询挂单

### 系统要求

- Python 3.9+
- `bt_api_base >= 0.15`
- `pymt5 >= 0.5.0`（仅 Windows/macOS，需运行 MT5 终端）
- 已启用 WebAPI 的 MT5 终端

### 安装

```bash
pip install bt_api_mt5
```

或从源码安装：

```bash
git clone https://github.com/cloudQuant/bt_api_mt5
cd bt_api_mt5
pip install -e .
```

> **注意：** `pymt5` 通过 WebSocket 连接运行中的 MT5 终端。MT5 仅在 Windows 和 macOS 上运行。Linux 用户可以安装包，但需要远程 MT5 终端才能建立连接。

### 快速开始

```python
from bt_api_mt5 import Mt5GatewayAdapter

# 初始化适配器
adapter = Mt5GatewayAdapter(
    login=12345678,        # MT5 账户登录名
    password="your_password",
    ws_uri="ws://localhost:8080",  # MT5 WebAPI 地址
    symbol_suffix="",      # 可选：品种后缀映射
)

# 连接 MT5
adapter.connect()

# 订阅品种
adapter.subscribe_symbols(["EURUSD", "GBPUSD"])

# 查询账户余额
balance = adapter.get_balance()
print(balance)

# 查询持仓
positions = adapter.get_positions()
print(positions)

# 下限价单
order_result = adapter.place_order({
    "symbol": "EURUSD",
    "volume": 0.1,
    "price": 1.0850,
    "order_type": "limit",
    "direction": "buy",
    "sl": 1.0800,
    "tp": 1.0900,
})
print(order_result)

# 撤单
cancel_result = adapter.cancel_order({"order_id": 12345678})
print(cancel_result)

# 查询历史 K 线
bars = adapter.get_bars("EURUSD", "H1", 100)
print(f"获取了 {len(bars)} 根 K 线")

# 断开连接
adapter.disconnect()
```

### 支持的操作

| 操作 | 方法 | 状态 |
|------|------|------|
| 连接 | `connect()` | ✅ |
| 断开 | `disconnect()` | ✅ |
| 订阅品种 | `subscribe_symbols(symbols)` | ✅ |
| 账户余额 | `get_balance()` | ✅ |
| 持仓查询 | `get_positions()` | ✅ |
| 下单 | `place_order(payload)` | ✅ |
| 撤单 | `cancel_order(payload)` | ✅ |
| 历史 K 线 | `get_bars(symbol, timeframe, count)` | ✅ |
| 品种信息 | `get_symbol_info(symbol)` | ✅ |
| 挂单查询 | `get_open_orders()` | ✅ |

### 下单参数格式

```python
{
    "symbol": "EURUSD",      # 交易品种
    "volume": 0.1,           # 委托数量（手）
    "price": 1.0850,         # 委托价格（限价单/止损单）
    "order_type": "limit",   # "market", "limit", "stop"
    "direction": "buy",       # "buy" 或 "sell"
    "sl": 1.0800,            # 止损价格（可选）
    "tp": 1.0900,            # 止盈价格（可选）
    "comment": "订单备注"       # 可选备注
}
```

### 品种名称解析

适配器维护品种映射表，通过 `symbol_map` 参数配置 bt_api 品种名到 MT5 品种名的映射：

```python
adapter = Mt5GatewayAdapter(
    login=12345678,
    password="your_password",
    ws_uri="ws://localhost:8080",
    symbol_map={
        "EURUSD": "EURUSD",
        "XAUUSD": "GOLD",
    },
    symbol_suffix=""
)
```

### 架构

```
bt_api_mt5/
├── src/bt_api_mt5/
│   ├── __init__.py          # 包初始化，导出 Mt5GatewayAdapter
│   ├── plugin.py            # bt_api 插件注册
│   └── gateway/
│       ├── __init__.py
│       └── adapter.py       # Mt5GatewayAdapter 实现
├── tests/
│   └── conftest.py         # Pytest 配置
└── docs/
    └── index.md            # 文档
```

### 在线文档

| 资源 | 链接 |
|------|------|
| 英文文档 | https://bt-api-mt5.readthedocs.io/ |
| 中文文档 | https://bt-api-mt5.readthedocs.io/zh/latest/ |
| GitHub 仓库 | https://github.com/cloudQuant/bt_api_mt5 |
| 问题反馈 | https://github.com/cloudQuant/bt_api_mt5/issues |

### 许可证

MIT 许可证 - 详见 [LICENSE](LICENSE)。

### 技术支持

- 通过 [GitHub Issues](https://github.com/cloudQuant/bt_api_mt5/issues) 反馈问题
- 邮箱: yunjinqi@gmail.com
