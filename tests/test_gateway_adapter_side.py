from __future__ import annotations

import asyncio
from types import SimpleNamespace

from bt_api_base.gateway.protocol import CHANNEL_EVENT

from bt_api_mt5.gateway.adapter import Mt5GatewayAdapter


class _DoneFuture:
    def __init__(self, value):
        self._value = value

    def result(self, timeout=None):
        return self._value


def test_cancel_order_accepts_gateway_order_ref_alias(monkeypatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.cancelled_ticket = None

        async def cancel_pending_order(self, ticket):
            self.cancelled_ticket = ticket
            return SimpleNamespace(
                retcode=10009,
                description="cancelled",
                success=True,
                order=ticket,
            )

    def run_coroutine_threadsafe(coro, _loop):
        return _DoneFuture(asyncio.run(coro))

    def require_loop():
        return object()

    client = FakeClient()
    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._client = client
    adapter._require_loop = require_loop
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", run_coroutine_threadsafe)

    result = adapter.cancel_order({"order_ref": "123456"})

    assert client.cancelled_ticket == 123456
    assert result["order_id"] == 123456


def test_cancel_order_rejects_non_numeric_gateway_order_ref_alias() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")

    result = adapter.cancel_order({"order_ref": "local-ref"})

    assert result["status"] == "error"
    assert result["error"] == "invalid order_id: local-ref"


def test_position_to_dict_treats_string_zero_trade_action_as_buy() -> None:
    row = Mt5GatewayAdapter._position_to_dict(
        {
            "trade_symbol": "XAUUSD",
            "position_id": 42,
            "trade_action": "0",
            "trade_volume": 0.02,
            "price_open": 2330.0,
        }
    )

    assert row["direction"] == "buy"
    assert row["volume"] == 0.02


def test_position_to_dict_preserves_current_price_and_swap() -> None:
    row = Mt5GatewayAdapter._position_to_dict(
        {
            "trade_symbol": "XAUUSD",
            "position_id": 42,
            "trade_action": "0",
            "trade_volume": 0.02,
            "price_open": 2330.0,
            "price_current": 2331.5,
            "swap": -0.12,
            "profit": 3.0,
        }
    )

    assert row["current_price"] == 2331.5
    assert row["latest_price"] == 2331.5
    assert row["last_price"] == 2331.5
    assert row["swap"] == -0.12


def test_position_to_dict_does_not_invent_missing_commission_or_swap() -> None:
    row = Mt5GatewayAdapter._position_to_dict(
        {
            "trade_symbol": "XAUUSD",
            "position_id": 42,
            "trade_action": "0",
            "trade_volume": 0.02,
            "price_open": 2330.0,
            "price_current": 2331.5,
            "profit": 3.0,
        }
    )

    assert "commission" not in row
    assert "swap" not in row


def test_get_balance_uses_free_margin_as_cash(monkeypatch) -> None:
    async def get_account_summary():
        return {
            "balance": 100000.0,
            "equity": 100500.0,
            "margin": 1200.0,
            "margin_free": 99300.0,
            "profit": 500.0,
            "currency": "USD",
            "leverage": 100,
        }

    def fake_run_coroutine_threadsafe(coro, loop):
        coro.close()
        return _DoneFuture(
            {
                "balance": 100000.0,
                "equity": 100500.0,
                "margin": 1200.0,
                "margin_free": 99300.0,
                "profit": 500.0,
                "currency": "USD",
                "leverage": 100,
            }
        )

    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._loop = SimpleNamespace()
    adapter._client = SimpleNamespace(get_account_summary=get_account_summary)
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", fake_run_coroutine_threadsafe)

    balance = adapter.get_balance()

    assert balance["value"] == 100500.0
    assert balance["equity"] == 100500.0
    assert balance["balance"] == 100000.0
    assert balance["cash"] == 99300.0
    assert balance["available"] == 99300.0
    assert balance["available_funds"] == 99300.0
    assert balance["margin_free"] == 99300.0
    assert balance["margin"] == 1200.0


def test_get_balance_derives_cash_from_formatted_equity_minus_margin(monkeypatch) -> None:
    async def get_account_summary():
        return {
            "balance": "100,000",
            "equity": "100,500",
            "margin": {"amount": "1,200"},
            "profit": "500",
            "currency": "USD",
            "leverage": "100",
        }

    def fake_run_coroutine_threadsafe(coro, loop):
        coro.close()
        return _DoneFuture(
            {
                "balance": "100,000",
                "equity": "100,500",
                "margin": {"amount": "1,200"},
                "profit": "500",
                "currency": "USD",
                "leverage": "100",
            }
        )

    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._loop = SimpleNamespace()
    adapter._client = SimpleNamespace(get_account_summary=get_account_summary)
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", fake_run_coroutine_threadsafe)

    balance = adapter.get_balance()

    assert balance["value"] == 100500.0
    assert balance["equity"] == 100500.0
    assert balance["balance"] == 100000.0
    assert balance["cash"] == 99300.0
    assert balance["available_funds"] == 99300.0
    assert balance["margin"] == 1200.0
    assert balance["profit"] == 500.0
    assert balance["leverage"] == 100.0


def test_get_balance_preserves_zero_free_margin(monkeypatch) -> None:
    async def get_account_summary():
        return {
            "balance": 100000.0,
            "equity": 100500.0,
            "margin": 1200.0,
            "margin_free": "0",
        }

    def fake_run_coroutine_threadsafe(coro, loop):
        coro.close()
        return _DoneFuture(
            {
                "balance": 100000.0,
                "equity": 100500.0,
                "margin": 1200.0,
                "margin_free": "0",
            }
        )

    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._loop = SimpleNamespace()
    adapter._client = SimpleNamespace(get_account_summary=get_account_summary)
    monkeypatch.setattr(asyncio, "run_coroutine_threadsafe", fake_run_coroutine_threadsafe)

    balance = adapter.get_balance()

    assert balance["cash"] == 0.0
    assert balance["available"] == 0.0
    assert balance["available_funds"] == 0.0
    assert balance["margin_free"] == 0.0


def test_position_update_push_normalizes_text_position_side() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")

    adapter._on_position_update_push(
        [
            {
                "position_id": 42,
                "trade_symbol": "XAUUSD",
                "trade_action": "POSITION_TYPE_BUY",
                "trade_volume": 0.02,
                "price_open": 2330.0,
                "price_current": 2331.5,
            }
        ]
    )

    channel, event = adapter.poll_output()

    assert channel == CHANNEL_EVENT
    assert event["kind"] == "position"
    assert event["side"] == "buy"
    assert event["size"] == 0.02
    assert event["volume"] == 0.02
    assert event["position_id"] == "42"
    assert event["current_price"] == 2331.5
    assert "commission" not in event


def test_order_update_push_normalizes_string_buy_limit_type() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")

    adapter._on_order_update_push(
        [
            {
                "order_id": 7,
                "trade_symbol": "EURUSD",
                "order_type": "2",
                "order_state": 1,
                "volume_initial": 1.0,
                "volume_current": 1.0,
            }
        ]
    )

    channel, event = adapter.poll_output()

    assert channel == CHANNEL_EVENT
    assert event["kind"] == "order"
    assert event["side"] == "buy"
    assert event["status"] == "accepted"


def test_order_update_push_preserves_expired_order_state() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")

    adapter._on_order_update_push(
        [
            {
                "order_id": 8,
                "trade_symbol": "EURUSD",
                "order_type": "3",
                "order_state": 6,
                "volume_initial": 1.0,
                "volume_current": 1.0,
            }
        ]
    )

    channel, event = adapter.poll_output()

    assert channel == CHANNEL_EVENT
    assert event["kind"] == "order"
    assert event["side"] == "sell"
    assert event["status"] == "expired"


def test_transaction_deal_side_uses_deal_type_not_entry_flag() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")

    adapter._on_transaction_push(
        {
            "deal": {
                "deal_id": 11,
                "order_id": 7,
                "symbol": "EURUSD",
                "entry": 0,
                "type": "DEAL_TYPE_SELL",
                "volume": 1.0,
                "price": 1.1,
            }
        }
    )

    channel, event = adapter.poll_output()

    assert channel == CHANNEL_EVENT
    assert event["kind"] == "trade"
    assert event["side"] == "sell"


def test_transaction_order_push_preserves_expired_order_state() -> None:
    adapter = Mt5GatewayAdapter(login=1, password="secret")

    adapter._on_transaction_push(
        {
            "orders": [
                {
                    "order_id": 9,
                    "symbol": "EURUSD",
                    "order_type": "2",
                    "order_state": 6,
                    "volume_initial": 1.0,
                    "volume_current": 1.0,
                }
            ]
        }
    )

    channel, event = adapter.poll_output()

    assert channel == CHANNEL_EVENT
    assert event["kind"] == "order"
    assert event["status"] == "expired"


def test_async_place_order_preserves_client_order_ids_for_immediate_fill() -> None:
    class Result:
        retcode = 10009
        success = True
        order = 0
        deal = 9001
        volume = 0.1
        price = 1.2345
        description = "filled"
        bid = 1.2344
        ask = 1.2346
        comment = ""

    class FakeClient:
        async def buy_market(self, symbol, volume, **_kwargs):
            assert symbol == "EURUSD"
            assert volume == 0.1
            return Result()

    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._client = FakeClient()

    result = asyncio.run(
        adapter._async_place_order(
            {
                "symbol": "EURUSD",
                "side": "buy",
                "size": 0.1,
                "order_type": "market",
                "client_order_id": "client-7",
                "bt_order_ref": 7,
            }
        )
    )

    assert result["status"] == "completed"
    assert result["order_id"] == 0
    assert result["order_ref"] == "client-7"
    assert result["client_order_id"] == "client-7"
    assert result["bt_order_ref"] == 7
    assert result["deal"] == 9001
    assert result["volume"] == 0.1


def test_async_place_order_rejects_volume_below_minimum_without_clamping() -> None:
    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def buy_market(self, *_args, **_kwargs):
            self.calls += 1
            raise AssertionError("buy_market should not be called")

    client = FakeClient()
    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._client = client
    adapter._symbol_specs["EURUSD"] = {
        "volume_min": 0.1,
        "volume_max": 100.0,
        "volume_step": 0.1,
    }

    result = asyncio.run(
        adapter._async_place_order(
            {
                "symbol": "EURUSD",
                "side": "buy",
                "size": 0.05,
                "order_type": "market",
            }
        )
    )

    assert result["status"] == "error"
    assert "below minimum" in result["error"]
    assert client.calls == 0


def test_async_place_order_rejects_volume_step_mismatch_without_rounding() -> None:
    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def buy_market(self, *_args, **_kwargs):
            self.calls += 1
            raise AssertionError("buy_market should not be called")

    client = FakeClient()
    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._client = client
    adapter._symbol_specs["EURUSD"] = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
    }

    result = asyncio.run(
        adapter._async_place_order(
            {
                "symbol": "EURUSD",
                "side": "buy",
                "size": 0.015,
                "order_type": "market",
            }
        )
    )

    assert result["status"] == "error"
    assert "does not align with step" in result["error"]
    assert client.calls == 0


def test_async_place_order_rejects_nonpositive_limit_price() -> None:
    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def buy_limit(self, *_args, **_kwargs):
            self.calls += 1
            raise AssertionError("buy_limit should not be called")

    client = FakeClient()
    adapter = Mt5GatewayAdapter(login=1, password="secret")
    adapter._client = client
    adapter._symbol_specs["EURUSD"] = {
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
    }

    result = asyncio.run(
        adapter._async_place_order(
            {
                "symbol": "EURUSD",
                "side": "buy",
                "size": 0.01,
                "price": 0,
                "order_type": "limit",
            }
        )
    )

    assert result["status"] == "error"
    assert "positive price" in result["error"]
    assert client.calls == 0
