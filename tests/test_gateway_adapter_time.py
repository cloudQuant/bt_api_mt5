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


def test_refresh_server_offset_uses_terminal_info_server_offset_time() -> None:
    class FakeClient:
        async def terminal_info(self) -> dict[str, int]:
            return {"server_offset_time": 10800}

    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._client = FakeClient()

    asyncio.run(adapter._refresh_server_offset())

    assert adapter._server_offset_seconds == 10800
    assert adapter._server_time_to_utc_timestamp(1782367860) == pytest.approx(1782357060)
