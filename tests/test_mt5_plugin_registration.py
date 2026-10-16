from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bt_api_base.plugins.errors import PluginRegistrationError
from bt_api_base.plugins.loader import PluginLoader
from bt_api_base.plugins.protocol import PluginInfo
from bt_api_base.registry import ExchangeRegistry

from bt_api_mt5 import __version__
from bt_api_mt5.plugin import register_plugin


def test_register_plugin_returns_plugin_info() -> None:
    isolated_registry = ExchangeRegistry.create_isolated()
    info = register_plugin(isolated_registry)

    assert isinstance(info, PluginInfo)
    assert info.name == "bt_api_mt5"
    assert info.version == __version__
    assert info.core_requires == ">=0.15,<1.0"
    assert info.supported_exchanges == ()
    assert info.supported_asset_types == ()
    assert info.capabilities == frozenset({"unavailable"})
    assert isolated_registry.list_exchanges() == []


@dataclass
class _FakeEntryPoint:
    name: str
    module: str

    def load(self) -> Any:
        return register_plugin


def test_loader_does_not_report_mt5_as_loaded_without_direct_feed_registration(
    monkeypatch,
) -> None:
    isolated_registry = ExchangeRegistry.create_isolated()
    loader = PluginLoader(isolated_registry)
    monkeypatch.setattr(
        loader,
        "_discover_entry_points",
        lambda group: [_FakeEntryPoint("mt5", "bt_api_mt5.plugin")],
    )

    loader.load_all()

    assert loader.loaded == {}
    assert "bt_api_mt5" in loader.failed
    assert isinstance(loader.failed["bt_api_mt5"], PluginRegistrationError)
    assert "unavailable" in str(loader.failed["bt_api_mt5"])
    assert isolated_registry.list_exchanges() == []
