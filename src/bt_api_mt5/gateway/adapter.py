from __future__ import annotations

import asyncio
import importlib
import logging
import threading
import time
from typing import Any

from bt_api_base.gateway.adapters.base import BaseGatewayAdapter
from bt_api_base.gateway.models import GatewayTick
from bt_api_base.gateway.protocol import CHANNEL_EVENT, CHANNEL_MARKET

logger = logging.getLogger(__name__)

_TIMEFRAME_MAP: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
    "W1": 10080,
    "MN1": 43200,
}

_MT5_ORDER_STATE_MAP: dict[int, str] = {
    0: "submitted",
    1: "accepted",
    2: "canceled",
    3: "partial",
    4: "completed",
    5: "rejected",
    6: "canceled",
}

_RETCODE_STATUS: dict[int, str] = {
    10004: "rejected",
    10006: "rejected",
    10007: "canceled",
    10008: "submitted",
    10009: "completed",
    10010: "partial",
    10013: "rejected",
    10014: "rejected",
    10015: "rejected",
    10016: "rejected",
    10017: "rejected",
    10018: "rejected",
    10019: "rejected",
    10030: "rejected",
    10031: "rejected",
}


def _resolve_default_filling() -> int | None:
    try:
        pymt5 = importlib.import_module("pymt5")
        value = getattr(pymt5, "ORDER_FILLING_FOK", None)
        if value is not None:
            return int(value)
    except Exception:
        return None
    return None


class Mt5GatewayAdapter(BaseGatewayAdapter):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._client: Any = None

        self._login = int(kwargs.get("login") or 0)
        self._password = str(kwargs.get("password") or "")
        self._ws_uri = str(kwargs.get("ws_uri") or "")
        self._timeout = float(kwargs.get("timeout") or 60.0)
        self._heartbeat_interval = float(kwargs.get("heartbeat_interval") or 30.0)
        self._auto_reconnect = bool(kwargs.get("auto_reconnect", True))
        self._max_reconnect_attempts = int(kwargs.get("max_reconnect_attempts") or 5)

        self._symbol_suffix = str(kwargs.get("symbol_suffix") or "")
        self._symbol_map: dict[str, str] = dict(kwargs.get("symbol_map") or {})
        self._resolved_symbols: dict[str, str] = {}
        self._reverse_resolved_symbols: dict[str, str] = {
            str(value): str(key) for key, value in self._symbol_map.items()
        }

        self._subscribed_symbols: list[str] = []
        self._symbol_specs: dict[str, dict[str, Any]] = {}
        self._running = False

    def connect(self) -> None:
        if self._running:
            return
        if not self._login or not self._password:
            raise ValueError("MT5 adapter requires 'login' and 'password' parameters")
        self._loop = asyncio.new_event_loop()
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        future = asyncio.run_coroutine_threadsafe(self._async_connect(), self._loop)
        connect_timeout = max(self._timeout * 4, 120.0)
        future.result(timeout=connect_timeout)
        self.logger.info("Mt5GatewayAdapter connected (login=%s)", self._login)

    def _require_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            raise RuntimeError("MT5 adapter loop is not running")
        return self._loop

    def disconnect(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._loop is not None and self._client is not None:
            try:
                future = asyncio.run_coroutine_threadsafe(self._client.close(), self._loop)
                future.result(timeout=5.0)
            except Exception as exc:
                self.logger.warning(
                    "Mt5GatewayAdapter close failed during disconnect: %s: %s",
                    type(exc).__name__,
                    exc,
                )
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        self._loop = None
        self._thread = None
        self._client = None
        self.logger.info("Mt5GatewayAdapter disconnected")

    def subscribe_symbols(self, symbols: list[str]) -> dict[str, Any]:
        resolved = [self._resolve_symbol(symbol) for symbol in symbols]
        future = asyncio.run_coroutine_threadsafe(
            self._async_subscribe(symbols, resolved), self._require_loop()
        )
        result = future.result(timeout=self._timeout)
        for symbol in result.get("symbols") or []:
            if symbol not in self._subscribed_symbols:
                self._subscribed_symbols.append(symbol)
        return result

    def get_balance(self) -> dict[str, Any]:
        getter = getattr(self._client, "get_account_summary", None)
        if getter is None:
            getter = self._client.get_account
        future = asyncio.run_coroutine_threadsafe(getter(), self._require_loop())
        account = future.result(timeout=self._timeout)
        if isinstance(account, dict):
            balance = account.get("balance", 0.0)
            equity = account.get("equity", 0.0)
            credit = account.get("credit", 0.0)
            currency = account.get("currency", "")
            leverage = account.get("leverage", 0)
            margin = account.get("margin", 0.0)
            margin_free = account.get("margin_free", 0.0)
            profit = account.get("profit", 0.0)
        else:
            balance = getattr(account, "balance", 0.0)
            equity = getattr(account, "equity", 0.0)
            credit = getattr(account, "credit", 0.0)
            currency = getattr(account, "currency", "")
            leverage = getattr(account, "leverage", 0)
            margin = getattr(account, "margin", 0.0)
            margin_free = getattr(account, "margin_free", 0.0)
            profit = getattr(account, "profit", 0.0)
        return {
            "balance": balance,
            "equity": equity,
            "credit": credit,
            "currency": currency,
            "leverage": leverage,
            "cash": balance,
            "value": equity,
            "margin": margin,
            "margin_free": margin_free,
            "profit": profit,
        }

    def get_positions(self) -> list[dict[str, Any]]:
        future = asyncio.run_coroutine_threadsafe(
            self._client.get_positions(), self._require_loop()
        )
        positions = future.result(timeout=self._timeout)
        result: list[dict[str, Any]] = []
        for position in positions or []:
            result.append(
                {
                    "instrument": position.get("trade_symbol", ""),
                    "position_id": position.get("position_id"),
                    "direction": "buy" if position.get("trade_action") == 0 else "sell",
                    "volume": position.get("trade_volume", 0),
                    "price": position.get("price_open", 0.0),
                    "sl": position.get("sl", 0.0),
                    "tp": position.get("tp", 0.0),
                    "profit": position.get("profit", 0.0),
                    "commission": position.get("commission", 0.0),
                    "swap": position.get("storage", 0.0),
                    "comment": position.get("comment", ""),
                }
            )
        return result

    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        future = asyncio.run_coroutine_threadsafe(
            self._async_place_order(payload), self._require_loop()
        )
        return future.result(timeout=self._timeout)

    def cancel_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        order_id = payload.get("order_id") or payload.get("external_order_id")
        if order_id is None:
            return {"status": "error", "error": "missing order_id"}
        future = asyncio.run_coroutine_threadsafe(
            self._client.cancel_pending_order(int(order_id)), self._require_loop()
        )
        result = future.result(timeout=self._timeout)
        return self._trade_result_to_dict(result)

    def get_bars(self, symbol: str, timeframe: str, count: int) -> list[dict[str, Any]]:
        period_minutes = _TIMEFRAME_MAP.get(timeframe)
        if period_minutes is None:
            return []
        to_ts = int(time.time())
        from_ts = to_ts - count * period_minutes * 60
        mt5_symbol = self._resolve_symbol(symbol)
        future = asyncio.run_coroutine_threadsafe(
            self._client.get_rates(mt5_symbol, period_minutes, from_ts, to_ts),
            self._require_loop(),
        )
        rates = future.result(timeout=self._timeout)
        return [
            {
                "timestamp": float(rate.get("time", 0)),
                "open": float(rate.get("open", 0)),
                "high": float(rate.get("high", 0)),
                "low": float(rate.get("low", 0)),
                "close": float(rate.get("close", 0)),
                "volume": float(rate.get("tick_volume", 0)),
                "symbol": symbol,
                "timeframe": timeframe,
            }
            for rate in (rates or [])
        ]

    def get_symbol_info(self, symbol: str) -> dict[str, Any]:
        cached = self._symbol_specs.get(symbol)
        if cached:
            return dict(cached)
        mt5_symbol = self._resolve_symbol(symbol)
        future = asyncio.run_coroutine_threadsafe(
            self._client.get_full_symbol_info(mt5_symbol), self._require_loop()
        )
        info = future.result(timeout=self._timeout)
        if not info:
            return {}
        spec = {
            "contract_size": info.get("contract_size", 100000),
            "volume_min": info.get("volume_min", 0.01),
            "volume_max": info.get("volume_max", 100.0),
            "volume_step": info.get("volume_step", 0.01),
            "tick_size": info.get("tick_size", 0.00001),
            "digits": info.get("digits", 5),
            "margin_initial": info.get("margin_initial", 0.0),
        }
        self._symbol_specs[symbol] = spec
        return dict(spec)

    def get_open_orders(self) -> list[dict[str, Any]]:
        future = asyncio.run_coroutine_threadsafe(self._client.get_orders(), self._require_loop())
        orders = future.result(timeout=self._timeout)
        result: list[dict[str, Any]] = []
        for order in orders or []:
            result.append(
                {
                    "order_id": order.get("order_id"),
                    "symbol": order.get("trade_symbol", ""),
                    "type": order.get("trade_type"),
                    "volume": order.get("trade_volume", 0),
                    "price": order.get("price_order", 0.0),
                    "sl": order.get("sl", 0.0),
                    "tp": order.get("tp", 0.0),
                    "state": order.get("order_state"),
                    "comment": order.get("comment", ""),
                }
            )
        return result

    def _run_loop(self) -> None:
        loop = self._require_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def _async_connect(self) -> None:
        pymt5 = importlib.import_module("pymt5")
        mt5_web_client = getattr(pymt5, "MT5WebClient")

        client_kwargs: dict[str, Any] = {
            "auto_reconnect": self._auto_reconnect,
            "max_reconnect_attempts": self._max_reconnect_attempts,
        }
        if self._ws_uri:
            client_kwargs["uri"] = self._ws_uri
        if self._heartbeat_interval:
            client_kwargs["heartbeat_interval"] = self._heartbeat_interval
        if self._timeout:
            client_kwargs["timeout"] = self._timeout

        self._client = mt5_web_client(**client_kwargs)
        await self._client.connect()
        await self._client.login(login=self._login, password=self._password)
        symbol_count = await self._load_symbol_cache()
        logger.info("MT5 symbol cache loaded: %d symbols", symbol_count)

        self._client.on_tick(self._on_tick_push)
        self._client.on_disconnect(self._on_ws_disconnect)
        try:
            self._client.on_trade_transaction(self._on_transaction_push)
        except Exception as exc:
            self.logger.warning(
                "Mt5GatewayAdapter failed to register trade transaction callback: %s: %s",
                type(exc).__name__,
                exc,
            )
        try:
            self._client.on_trade_result(self._on_trade_result_push)
        except Exception as exc:
            self.logger.warning(
                "Mt5GatewayAdapter failed to register trade result callback: %s: %s",
                type(exc).__name__,
                exc,
            )
        try:
            self._client.on_order_update(self._on_order_update_push)
        except Exception as exc:
            self.logger.warning(
                "Mt5GatewayAdapter failed to register order update callback: %s: %s",
                type(exc).__name__,
                exc,
            )
        try:
            self._client.on_position_update(self._on_position_update_push)
        except Exception as exc:
            self.logger.warning(
                "Mt5GatewayAdapter failed to register position update callback: %s: %s",
                type(exc).__name__,
                exc,
            )

    async def _async_subscribe(
        self, standard_symbols: list[str], resolved_symbols: list[str]
    ) -> dict[str, Any]:
        available_symbols = await self._get_available_symbols()
        candidate_pairs: list[tuple[str, str]] = []
        skipped_symbols: list[str] = []

        for standard_symbol, mt5_symbol in zip(standard_symbols, resolved_symbols):
            if available_symbols.get(mt5_symbol) is None:
                discovered = self._discover_symbol(
                    standard_symbol, symbol_names=list(available_symbols.keys())
                )
                if discovered and available_symbols.get(discovered) is not None:
                    mt5_symbol = discovered
                else:
                    skipped_symbols.append(standard_symbol)
                    logger.warning(
                        "skipping MT5 subscription for %s; resolved symbol %s not found in cache",
                        standard_symbol,
                        mt5_symbol,
                    )
                    continue
            candidate_pairs.append((standard_symbol, mt5_symbol))

        subscribed_id_set: set[int] | None = None
        if candidate_pairs:
            subscribe_batch = getattr(self._client, "subscribe_symbols_batch", None)
            if subscribe_batch is not None:
                subscribed_ids = await subscribe_batch(
                    [mt5_symbol for _, mt5_symbol in candidate_pairs]
                )
                subscribed_id_set = {int(symbol_id) for symbol_id in subscribed_ids}
            else:
                subscribe_symbols = getattr(self._client, "subscribe_symbols", None)
                if subscribe_symbols is None:
                    raise AttributeError(
                        f"{type(self._client).__name__} has neither subscribe_symbols_batch nor subscribe_symbols"
                    )
                await subscribe_symbols([mt5_symbol for _, mt5_symbol in candidate_pairs])

        subscribed_symbols: list[str] = []
        resolved_map: dict[str, str] = {}
        for standard_symbol, mt5_symbol in candidate_pairs:
            info = available_symbols.get(mt5_symbol)
            symbol_id = getattr(info, "symbol_id", None)
            if subscribed_id_set is not None and symbol_id not in subscribed_id_set:
                skipped_symbols.append(standard_symbol)
                continue
            subscribed_symbols.append(standard_symbol)
            resolved_map[standard_symbol] = mt5_symbol
            self._resolved_symbols[standard_symbol] = mt5_symbol
            self._reverse_resolved_symbols[mt5_symbol] = standard_symbol
            try:
                full_info = await self._client.get_full_symbol_info(mt5_symbol)
                if full_info:
                    self._symbol_specs[standard_symbol] = {
                        "contract_size": full_info.get("contract_size", 100000),
                        "volume_min": full_info.get("volume_min", 0.01),
                        "volume_max": full_info.get("volume_max", 100.0),
                        "volume_step": full_info.get("volume_step", 0.01),
                        "tick_size": full_info.get("tick_size", 0.00001),
                        "digits": full_info.get("digits", 5),
                        "margin_initial": full_info.get("margin_initial", 0.0),
                    }
            except Exception as exc:
                logger.warning("failed to cache symbol info for %s: %s", standard_symbol, exc)
                skipped_symbols.append(standard_symbol)

        return {
            "symbols": subscribed_symbols,
            "skipped_symbols": skipped_symbols,
            "resolved_symbols": resolved_map,
        }

    async def _async_place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        symbol = str(payload.get("data_name") or payload.get("symbol") or "")
        mt5_symbol = self._resolve_symbol(symbol)
        volume = float(payload.get("volume") or payload.get("size") or 0.01)
        volume = self._normalize_volume(symbol, volume)
        price = payload.get("price")
        if price is not None:
            price = float(price)
        side = str(payload.get("side") or "buy").lower()
        order_type = str(payload.get("order_type") or "market").lower()
        sl = float(payload.get("sl") or payload.get("stop_loss") or 0.0)
        tp = float(payload.get("tp") or payload.get("take_profit") or 0.0)
        deviation = int(payload.get("deviation") or 20)
        comment = str(payload.get("comment") or "")
        magic = int(payload.get("magic") or 0)
        filling_value = payload.get("filling")
        if filling_value is None:
            filling_value = _resolve_default_filling()
        filling = int(filling_value) if filling_value is not None else None
        request_kwargs = {
            "sl": sl,
            "tp": tp,
            "deviation": deviation,
            "comment": comment,
            "magic": magic,
        }
        if filling is not None:
            request_kwargs["filling"] = filling

        if order_type == "market":
            if side == "buy":
                result = await self._client.buy_market(mt5_symbol, volume, **request_kwargs)
            else:
                result = await self._client.sell_market(mt5_symbol, volume, **request_kwargs)
        elif order_type == "limit":
            if price is None:
                return {"status": "error", "error": "limit order requires price"}
            if side == "buy":
                result = await self._client.buy_limit(mt5_symbol, volume, price, **request_kwargs)
            else:
                result = await self._client.sell_limit(mt5_symbol, volume, price, **request_kwargs)
        elif order_type == "stop":
            if price is None:
                return {"status": "error", "error": "stop order requires price"}
            if side == "buy":
                result = await self._client.buy_stop(mt5_symbol, volume, price, **request_kwargs)
            else:
                result = await self._client.sell_stop(mt5_symbol, volume, price, **request_kwargs)
        elif order_type == "close":
            position_id = int(payload.get("position_id") or 0)
            result = await self._client.close_position(
                mt5_symbol, position_id, volume, **request_kwargs
            )
        else:
            return {"status": "error", "error": f"unsupported order_type: {order_type}"}

        return self._trade_result_to_dict(result, symbol=symbol)

    def _on_tick_push(self, ticks: list[dict]) -> None:
        for tick in ticks:
            symbol_name = tick.get("symbol", "")
            if not symbol_name:
                symbol_id = tick.get("symbol_id")
                if symbol_id is not None and self._client is not None:
                    info = getattr(self._client, "_symbols_by_id", {}).get(symbol_id)
                    if info is not None:
                        symbol_name = info.name
            standard_symbol = self._to_standard_symbol(symbol_name)
            gateway_tick = GatewayTick(
                timestamp=tick.get("tick_time", 0),
                symbol=standard_symbol,
                exchange="MT5",
                asset_type="OTC",
                local_time=time.time(),
                bid_price=tick.get("bid", 0.0),
                ask_price=tick.get("ask", 0.0),
                price=((tick.get("bid") or 0.0) + (tick.get("ask") or 0.0)) / 2.0,
                volume=tick.get("tick_volume", 0.0),
                instrument_id=symbol_name,
            )
            self.emit(CHANNEL_MARKET, gateway_tick)

    def _on_order_update_push(self, orders: list[dict]) -> None:
        for order in orders:
            order_state = int(order.get("order_state", 0) or 0)
            status = _MT5_ORDER_STATE_MAP.get(order_state, "submitted")
            self.emit(
                CHANNEL_EVENT,
                {
                    "kind": "order",
                    "exchange": "MT5",
                    "status": status,
                    "external_order_id": str(
                        order.get("order_id") or order.get("trade_order") or ""
                    ),
                    "order_ref": str(order.get("order_id") or order.get("trade_order") or ""),
                    "data_name": order.get("trade_symbol", ""),
                    "side": "buy" if order.get("order_type", 0) in (0, 2, 4) else "sell",
                    "price": float(order.get("price_order") or 0.0),
                    "size": float(order.get("volume_initial") or 0.0),
                    "filled": float(
                        (order.get("volume_initial") or 0) - (order.get("volume_current") or 0)
                    ),
                    "remaining": float(order.get("volume_current") or 0.0),
                },
            )

    def _on_position_update_push(self, positions: list[dict]) -> None:
        for position in positions:
            trade_action = position.get("trade_action", -1)
            side = "buy" if trade_action == 0 else "sell"
            self.emit(
                CHANNEL_EVENT,
                {
                    "kind": "trade",
                    "exchange": "MT5",
                    "trade_id": str(position.get("position_id") or ""),
                    "external_order_id": str(position.get("order_id") or ""),
                    "order_ref": str(position.get("order_id") or ""),
                    "data_name": position.get("trade_symbol", ""),
                    "side": side,
                    "size": abs(float(position.get("trade_volume") or 0)),
                    "price": float(position.get("price_open") or 0.0),
                    "commission": float(position.get("commission") or 0.0),
                    "profit": float(position.get("profit") or 0.0),
                    "position_id": position.get("position_id"),
                },
            )

    def _on_transaction_push(self, transactions: list[dict] | dict | None) -> None:
        if transactions is None:
            return
        if isinstance(transactions, dict):
            transactions = [transactions]
        for transaction in transactions:
            deals = transaction.get("deals", [])
            orders = transaction.get("orders", [])
            if not deals and isinstance(transaction.get("deal"), dict):
                deals = [transaction["deal"]]
            if not orders and isinstance(transaction.get("order"), dict):
                orders = [transaction["order"]]
            for deal in deals:
                self.emit(
                    CHANNEL_EVENT,
                    {
                        "kind": "trade",
                        "exchange": "MT5",
                        "trade_id": str(deal.get("deal_id") or deal.get("deal") or ""),
                        "external_order_id": str(
                            deal.get("order_id") or deal.get("trade_order") or ""
                        ),
                        "order_ref": str(deal.get("order_id") or deal.get("trade_order") or ""),
                        "data_name": deal.get("symbol") or deal.get("trade_symbol") or "",
                        "side": "buy"
                        if deal.get("entry", deal.get("trade_action", 0)) == 0
                        else "sell",
                        "size": abs(float(deal.get("volume") or deal.get("trade_volume") or 0)),
                        "price": float(deal.get("price") or deal.get("price_open") or 0.0),
                        "commission": float(deal.get("commission") or 0.0),
                        "profit": float(deal.get("profit") or 0.0),
                    },
                )
            for order in orders:
                order_state = int(order.get("order_state", 0) or 0)
                status = _MT5_ORDER_STATE_MAP.get(order_state, "submitted")
                self.emit(
                    CHANNEL_EVENT,
                    {
                        "kind": "order",
                        "exchange": "MT5",
                        "status": status,
                        "external_order_id": str(
                            order.get("order_id") or order.get("trade_order") or ""
                        ),
                        "order_ref": str(order.get("order_id") or order.get("trade_order") or ""),
                        "data_name": order.get("symbol") or order.get("trade_symbol") or "",
                        "side": "buy" if order.get("order_type", 0) in (0, 2, 4) else "sell",
                        "price": float(order.get("price") or order.get("price_order") or 0.0),
                        "size": float(order.get("volume_initial") or 0.0),
                        "filled": float(
                            (order.get("volume_initial") or 0) - (order.get("volume_current") or 0)
                        ),
                        "remaining": float(order.get("volume_current") or 0.0),
                    },
                )

    def _on_trade_result_push(self, result: Any) -> None:
        if isinstance(result, dict) and "result" in result:
            result = result["result"]
        if isinstance(result, dict):
            retcode = result.get("retcode", -1)
            order_id = result.get("order")
            deal = result.get("deal")
            price = result.get("price")
            volume = result.get("volume")
            description = result.get("description", "")
            success = retcode in (10008, 10009, 10010)
        else:
            retcode = getattr(result, "retcode", -1)
            order_id = getattr(result, "order", None)
            deal = getattr(result, "deal", None)
            price = getattr(result, "price", None)
            volume = getattr(result, "volume", None)
            description = getattr(result, "description", "")
            success = getattr(result, "success", False)
        status = _RETCODE_STATUS.get(retcode, "unknown")
        self.emit(
            CHANNEL_EVENT,
            {
                "kind": "order",
                "exchange": "MT5",
                "status": status,
                "retcode": retcode,
                "description": description,
                "success": success,
                "order_id": order_id,
                "external_order_id": str(order_id) if order_id else "",
                "deal": deal,
                "volume": volume,
                "price": price,
            },
        )

    def _on_ws_disconnect(self) -> None:
        self.emit(
            CHANNEL_EVENT,
            {
                "kind": "health",
                "exchange": "MT5",
                "type": "disconnected",
                "message": "MT5 WebSocket connection lost",
            },
        )

    def _resolve_symbol(self, standard_symbol: str) -> str:
        cached = self._resolved_symbols.get(standard_symbol)
        if cached:
            return cached
        if standard_symbol in self._symbol_map:
            resolved = self._symbol_map[standard_symbol]
            self._resolved_symbols[standard_symbol] = resolved
            self._reverse_resolved_symbols[resolved] = standard_symbol
            return resolved
        if self._symbol_suffix:
            resolved = standard_symbol + self._symbol_suffix
            self._resolved_symbols[standard_symbol] = resolved
            self._reverse_resolved_symbols[resolved] = standard_symbol
            return resolved
        discovered = self._discover_symbol(standard_symbol)
        if discovered:
            self._resolved_symbols[standard_symbol] = discovered
            self._reverse_resolved_symbols[discovered] = standard_symbol
            return discovered
        return standard_symbol

    @staticmethod
    def _normalize_symbol_key(symbol: str) -> str:
        return "".join(ch for ch in str(symbol or "").upper() if ch.isalnum())

    def _match_symbol_candidate(
        self, target_symbol: str, candidate_symbol: str
    ) -> tuple[int, int] | None:
        target_upper = str(target_symbol or "").upper()
        candidate_upper = str(candidate_symbol or "").upper()
        if not target_upper or not candidate_upper:
            return None
        if candidate_upper == target_upper:
            return (0, len(candidate_symbol))

        normalized_target = self._normalize_symbol_key(target_symbol)
        normalized_candidate = self._normalize_symbol_key(candidate_symbol)
        if normalized_target and normalized_candidate == normalized_target:
            return (1, len(candidate_symbol))
        if candidate_upper.startswith(target_upper):
            return (2, len(candidate_symbol) - len(target_symbol))
        if candidate_upper.endswith(target_upper):
            return (3, len(candidate_symbol) - len(target_symbol))
        if normalized_target:
            if normalized_candidate.startswith(normalized_target):
                return (4, len(normalized_candidate) - len(normalized_target))
            if normalized_candidate.endswith(normalized_target):
                return (5, len(normalized_candidate) - len(normalized_target))
            if normalized_target in normalized_candidate:
                return (6, len(normalized_candidate) - len(normalized_target))
        if target_upper in candidate_upper:
            return (7, len(candidate_symbol) - len(target_symbol))
        return None

    def _discover_symbol(
        self,
        standard_symbol: str,
        symbol_names: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> str | None:
        if self._client is None:
            return None
        available_names = list(symbol_names or getattr(self._client, "symbol_names", []) or [])
        ranked_matches: list[tuple[tuple[int, int], str]] = []
        for name in available_names:
            candidate = str(name)
            score = self._match_symbol_candidate(standard_symbol, candidate)
            if score is not None:
                ranked_matches.append((score, candidate))
        if not ranked_matches:
            return None
        ranked_matches.sort(key=lambda item: (item[0][0], item[0][1], len(item[1]), item[1]))
        return ranked_matches[0][1]

    async def _load_symbol_cache(self) -> int:
        if self._client is None:
            return 0
        symbols = await self._client.load_symbols()
        count = len(symbols or {})
        if count > 0:
            return count
        invalidate = getattr(self._client, "invalidate_symbol_cache", None)
        if callable(invalidate):
            invalidate()
        symbols = await self._client.load_symbols(use_gzip=False)
        return len(symbols or {})

    async def _get_available_symbols(self) -> dict[str, Any]:
        available_symbols = dict(getattr(self._client, "_symbols", {}) or {})
        if available_symbols:
            return available_symbols
        symbol_count = await self._load_symbol_cache()
        available_symbols = dict(getattr(self._client, "_symbols", {}) or {})
        if available_symbols:
            logger.info("MT5 symbol cache reloaded before subscribe: %d symbols", symbol_count)
        else:
            logger.warning("MT5 symbol cache is empty before subscribe")
        return available_symbols

    def _to_standard_symbol(self, raw_symbol: str) -> str:
        if not raw_symbol:
            return raw_symbol
        mapped = self._reverse_resolved_symbols.get(raw_symbol)
        if mapped:
            return mapped
        ranked_matches: list[tuple[tuple[int, int], str]] = []
        for symbol in self._subscribed_symbols:
            score = self._match_symbol_candidate(symbol, raw_symbol)
            if score is not None:
                ranked_matches.append((score, symbol))
        if ranked_matches:
            ranked_matches.sort(key=lambda item: (item[0][0], item[0][1], len(item[1]), item[1]))
            standard_symbol = ranked_matches[0][1]
            self._resolved_symbols.setdefault(standard_symbol, raw_symbol)
            self._reverse_resolved_symbols[raw_symbol] = standard_symbol
            return standard_symbol
        return raw_symbol

    def _normalize_volume(self, symbol: str, volume: float) -> float:
        spec = self._symbol_specs.get(symbol, {})
        step = spec.get("volume_step", 0.01)
        volume_min = spec.get("volume_min", 0.01)
        volume_max = spec.get("volume_max", 100.0)
        if step > 0:
            normalized = max(volume_min, min(volume_max, round(volume / step) * step))
        else:
            normalized = max(volume_min, min(volume_max, volume))
        return round(normalized, 8)

    @staticmethod
    def _trade_result_to_dict(result: Any, symbol: str = "") -> dict[str, Any]:
        retcode = getattr(result, "retcode", -1)
        return {
            "status": _RETCODE_STATUS.get(retcode, "unknown"),
            "retcode": retcode,
            "description": getattr(result, "description", ""),
            "success": getattr(result, "success", False),
            "order_id": getattr(result, "order", None),
            "external_order_id": getattr(result, "order", None),
            "deal": getattr(result, "deal", None),
            "volume": getattr(result, "volume", None),
            "price": getattr(result, "price", None),
            "bid": getattr(result, "bid", None),
            "ask": getattr(result, "ask", None),
            "comment": getattr(result, "comment", ""),
            "data_name": symbol,
        }


__all__ = [
    "_MT5_ORDER_STATE_MAP",
    "_RETCODE_STATUS",
    "_TIMEFRAME_MAP",
    "Mt5GatewayAdapter",
]
