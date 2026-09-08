"""Native MT5 gateway consumes the unified SDK's lot and ticket intent."""

import asyncio
from types import SimpleNamespace

import pytest

from bt_api_mt5.gateway.adapter import Mt5GatewayAdapter


def run_order(**changes):
    calls = []

    async def close(symbol, ticket, volume, **kwargs):
        calls.append((symbol, ticket, volume))
        return SimpleNamespace(retcode=10009, success=True, order=51, deal=61, volume=volume)

    adapter = Mt5GatewayAdapter(login=1, password="fixture")
    adapter._client = SimpleNamespace(close_position=close)
    request = dict(
        symbol="XAUUSD",
        size=0.02,
        side="sell",
        order_type="market",
        quantity_unit="lots",
        position_side="long",
        offset="close",
        position_id="42",
    )
    request.update(changes)
    return asyncio.run(adapter._async_place_order(request)), calls


def test_unified_close_preserves_ticket_lots_and_distinct_result_ids():
    result, calls = run_order()
    assert calls == [("XAUUSD", 42, 0.02)]
    assert result["order_id"] == 51 and result["deal"] == 61


@pytest.mark.parametrize(
    "changes",
    [
        {"position_id": None},
        {"position_id": "invalid"},
        {"position_id": 0},
        {"order_type": "limit", "price": 2000},
        {"offset": "close_today"},
        {"offset": "open"},
        {"quantity_unit": "base"},
        {"quantity_unit": "contracts"},
        {"size": 0},
        {"size": -0.02},
        {"size": 0.025},
    ],
)
def test_unsupported_or_invalid_close_never_dispatches(changes):
    result, calls = run_order(**changes)
    assert result["status"] == "error"
    assert calls == []
