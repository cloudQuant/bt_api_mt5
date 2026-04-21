from __future__ import annotations

from typing import Any

from bt_api_base.gateway.registrar import GatewayRuntimeRegistrar
from bt_api_base.plugins.protocol import PluginInfo
from bt_api_base.registry import ExchangeRegistry

from bt_api_mt5 import __version__
from bt_api_mt5.gateway.adapter import Mt5GatewayAdapter


def register_plugin(
    registry: type[ExchangeRegistry], runtime_factory: type[GatewayRuntimeRegistrar]
) -> PluginInfo:
    runtime_factory.register_adapter("MT5", Mt5GatewayAdapter)

    return PluginInfo(
        name="bt_api_mt5",
        version=__version__,
        core_requires=">=0.15,<1.0",
        supported_exchanges=("MT5___STK", "MT5___FX"),
        supported_asset_types=("STK", "FX"),
    )
