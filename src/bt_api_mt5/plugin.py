"""Module-level docstring."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bt_api_base.registry import ExchangeRegistry

from bt_api_base.plugins.protocol import PluginInfo

from bt_api_mt5 import __version__


def register_plugin(registry: ExchangeRegistry) -> PluginInfo:
    """Declare the provider unavailable until a direct feed is migrated.

    The old MT5 adapter belongs to the retired gateway runtime.  Returning its
    exchange names as supported without registering an ExchangeRegistry feed
    would make PluginLoader publish a capability that ordinary BtApi cannot
    create.
    """
    del registry
    return PluginInfo(
        name="bt_api_mt5",
        version=__version__,
        core_requires=">=0.15,<1.0",
        supported_exchanges=(),
        supported_asset_types=(),
        capabilities=frozenset({"unavailable"}),
    )
