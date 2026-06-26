from __future__ import annotations

import asyncio

import pytest
from bt_api_base.gateway.protocol import CHANNEL_MARKET

from bt_api_mt5.gateway.adapter import Mt5GatewayAdapter


def test_server_time_to_utc_timestamp_subtracts_configured_offset() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret", server_offset_time=10800)

    assert adapter._server_time_to_utc_timestamp(1782367860) == pytest.approx(1782357060)
    assert adapter._server_time_to_utc_timestamp(1782367860000) == pytest.approx(1782357060)


def test_on_tick_push_emits_utc_timestamp_from_server_millis() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret", server_offset_time=10800)

    adapter._on_tick_push(
        [
            {
                "symbol": "EURUSD",
                "tick_time": 1782367860,
                "tick_time_ms": 1782367860123,
                "bid": 1.1,
                "ask": 1.1002,
                "tick_volume": 3,
            }
        ]
    )

    channel, tick = adapter.poll_output()

    assert channel == CHANNEL_MARKET
    assert tick.symbol == "EURUSD"
    assert tick.timestamp == pytest.approx(1782357060.123)
    assert tick.price == pytest.approx(1.1001)


def test_on_tick_push_caches_latest_price_for_symbol_info() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._symbol_specs["EURUSD"] = {"contract_size": 100000}

    adapter._on_tick_push(
        [
            {
                "symbol": "EURUSD",
                "tick_time_ms": 1782367860123,
                "bid": 1.1,
                "ask": 1.1002,
            }
        ]
    )

    spec = adapter.get_symbol_info("EURUSD")

    assert adapter.last_price["EURUSD"] == pytest.approx(1.1001)
    assert spec["current_price"] == pytest.approx(1.1001)
    assert spec["latest_price"] == pytest.approx(1.1001)
    assert spec["last_price"] == pytest.approx(1.1001)


def test_on_tick_push_prefers_last_price_over_bid_ask_midpoint() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._symbol_specs["XAUUSD"] = {"contract_size": 100}

    adapter._on_tick_push(
        [
            {
                "symbol": "XAUUSD",
                "tick_time_ms": 1782367860123,
                "bid": 2330.0,
                "ask": 2332.0,
                "last": 2331.5,
            }
        ]
    )

    channel, tick = adapter.poll_output()
    spec = adapter.get_symbol_info("XAUUSD")

    assert channel == CHANNEL_MARKET
    assert tick.price == pytest.approx(2331.5)
    assert spec["current_price"] == pytest.approx(2331.5)


def test_on_tick_push_uses_single_sided_quote_without_halving() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._symbol_specs["XAUUSD"] = {"contract_size": 100}

    adapter._on_tick_push(
        [
            {
                "symbol": "XAUUSD",
                "tick_time_ms": 1782367860123,
                "bid": 2330.0,
                "ask": 0.0,
            }
        ]
    )

    channel, tick = adapter.poll_output()
    spec = adapter.get_symbol_info("XAUUSD")

    assert channel == CHANNEL_MARKET
    assert tick.price == pytest.approx(2330.0)
    assert spec["current_price"] == pytest.approx(2330.0)


def test_refresh_server_offset_uses_terminal_info_server_offset_time() -> None:
    class FakeClient:
        async def terminal_info(self) -> dict[str, int]:
            return {"server_offset_time": 10800}

    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._client = FakeClient()

    asyncio.run(adapter._refresh_server_offset())

    assert adapter._server_offset_seconds == 10800
    assert adapter._server_time_to_utc_timestamp(1782367860) == pytest.approx(1782357060)
