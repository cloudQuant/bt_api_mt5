from __future__ import annotations

from bt_api_base.plugins.protocol import PluginInfo
from bt_api_base.registry import ExchangeRegistry

from bt_api_mt5 import __version__
from bt_api_mt5.gateway.adapter import Mt5GatewayAdapter
from bt_api_mt5.plugin import register_plugin


class _RuntimeFactory:
    adapters: dict[str, type] = {}

    @classmethod
    def register_adapter(cls, exchange: str, adapter: type) -> None:
        cls.adapters[exchange] = adapter


def test_register_plugin_returns_plugin_info() -> None:
    _RuntimeFactory.adapters = {}

    info = register_plugin(ExchangeRegistry, _RuntimeFactory)

    assert isinstance(info, PluginInfo)
    assert info.name == "bt_api_mt5"
    assert info.version == __version__
    assert info.core_requires == ">=0.15,<1.0"
    assert info.supported_exchanges == ("MT5___STK", "MT5___FX")
    assert info.supported_asset_types == ("STK", "FX")
    assert _RuntimeFactory.adapters["MT5"] is Mt5GatewayAdapter
