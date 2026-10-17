from __future__ import annotations

from importlib.util import find_spec


def test_legacy_gateway_module_is_absent() -> None:
    try:
        adapter_spec = find_spec("bt_api_mt5.gateway.adapter")
    except ModuleNotFoundError:
        adapter_spec = None

    assert adapter_spec is None
