# MetaTrader 5 Documentation

## English

Welcome to the MetaTrader 5 documentation for bt_api.

### Quick Start

```bash
pip install bt_api_mt5
```

```python
from bt_api_mt5 import MT5Api
feed = MT5Api(api_key="your_key", secret="your_secret")
ticker = feed.get_ticker("EURUSD")
```

## 中文

欢迎使用 bt_api 的 MT5 文档。

### 快速开始

```bash
pip install bt_api_mt5
```

```python
from bt_api_mt5 import MT5Api
feed = MT5Api(api_key="your_key", secret="your_secret")
ticker = feed.get_ticker("EURUSD")
```

## API Reference

See source code in `src/bt_api_mt5/` for detailed API documentation.
