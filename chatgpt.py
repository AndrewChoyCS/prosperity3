from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import List
import string
import math
import numpy as np
import statistics as stats
import json
from typing import Any


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])
        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]
        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )
        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])
        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[: max_length - 3] + "..."


logger = Logger()


class Trader:
    def __init__(self):
        # For demonstration, we keep track of positions in these products
        self.positions = {"RAINFOREST_RESIN": [0, 0], "KELP": [0, 0]}
        self.past_data = {}
        self.kelp_timestep_to_avg_price = {}

        # For a quick linear regression approach, though you can adapt or remove
        self.time_stamp = np.array([[i for i in range(1, 101)]])
        self.preCompute = np.linalg.pinv(self.time_stamp.transpose() @ self.time_stamp) @ self.time_stamp.transpose()
        self.prevSlope = float('inf')
        self.delay = 0

        # Parameters for your slope-based strategy
        self.short_window = 5
        self.long_window = 15
        self.slope_threshold = 0.2  # slope magnitude threshold to trigger entries/exits

    def VWAP(self, order_depth: OrderDepth):
        """
        Example: compute a volume-weighted average price across all orders 
        and guess potential buy and sell amounts to place near that price.
        """
        if not order_depth.sell_orders or not order_depth.buy_orders:
            return False, 0, 0, 0, 0

        sell_lowest = list(order_depth.sell_orders.items())[0]
        buy_highest = list(order_depth.buy_orders.items())[0]

        sell_price, _ = sell_lowest
        buy_price, _ = buy_highest

        market_price = (sell_price + buy_price) / 2

        total_orders = 0
        volume_avg = 0

        sell_orders = list(order_depth.sell_orders.items())
        buy_orders = list(order_depth.buy_orders.items())

        logger.print("Sell Order Depth: ", sell_orders)
        logger.print("Buy Order Depth: ", buy_orders)

        for item in sell_orders:
            price, size = item
            volume_avg += price * abs(size)
            total_orders += abs(size)

        for item in buy_orders:
            price, size = item
            volume_avg += price * abs(size)
            total_orders += abs(size)

        if total_orders == 0:
            return False, 0, 0, 0, 0

        volume_avg = volume_avg / total_orders

        # Simple heuristic for how many to buy/sell
        buy_amount = min(max(1, (volume_avg - market_price) * 4), 50)
        sell_amount = min(max(1, (market_price - volume_avg) * 4), 50)

        return True, market_price, volume_avg, buy_amount, sell_amount

    def slopeDetection(self) -> tuple[float, float]:
        """
        Returns the short-term slope and the long-term slope.

        The approach:
         - If we have fewer than 2 points, short slope and long slope = 0
         - Else compute:
             - short_slope:  linear regression of last self.short_window data
             - long_slope:   linear regression of last self.long_window data
        """
        n_data = len(self.kelp_timestep_to_avg_price)
        if n_data < 2:
            return 0.0, 0.0

        # We only want the last max(long_window) data points for the linear fits
        # so that short/long comparisons are consistent.
        timestamps = np.array(list(self.kelp_timestep_to_avg_price.keys()), dtype=float)
        prices = np.array(list(self.kelp_timestep_to_avg_price.values()), dtype=float)

        # Sort by timestamp just to be safe
        sort_idx = np.argsort(timestamps)
        timestamps = timestamps[sort_idx]
        prices = prices[sort_idx]

        # Last self.short_window points
        short_slice = max(0, n_data - self.short_window)
        x_short = timestamps[short_slice:]
        y_short = prices[short_slice:]

        # Last self.long_window points
        long_slice = max(0, n_data - self.long_window)
        x_long = timestamps[long_slice:]
        y_long = prices[long_slice:]

        # If we can’t do regression on the short window, return 0
        if len(x_short) < 2:
            short_slope = 0.0
        else:
            short_slope, _ = np.polyfit(x_short, y_short, 1)

        # If we can’t do regression on the long window, return 0
        if len(x_long) < 2:
            long_slope = 0.0
        else:
            long_slope, _ = np.polyfit(x_long, y_long, 1)

        logger.print(f"Short-term slope over last {self.short_window} pts = {short_slope:.3f},",
                     f"Long-term slope over last {self.long_window} pts = {long_slope:.3f}")

        return short_slope, long_slope

    def decide_entry_exit(self, short_slope: float, long_slope: float) -> str:
        """
        Decide whether conditions are bullish, bearish, or neutral, 
        based on short/long slope comparisons and threshold checks.
        Returns one of ["BULLISH", "BEARISH", "NEUTRAL"].
        """

        # Example: if both slopes are positive, and short_slope > long_slope,
        # we say strong uptrend => "BULLISH". You can refine logic as needed.
        
        # Filter out small slopes
        if abs(short_slope) < self.slope_threshold and abs(long_slope) < self.slope_threshold:
            return "NEUTRAL"

        # BULLISH if short_slope & long_slope both > 0, short_slope > long_slope by some margin
        if short_slope > 0 and long_slope > 0 and short_slope > long_slope:
            return "BULLISH"

        # BEARISH if short_slope & long_slope both < 0, short_slope < long_slope by some margin
        if short_slope < 0 and long_slope < 0 and short_slope < long_slope:
            return "BEARISH"

        return "NEUTRAL"

    def LinearRegression(self):
        """
        (Optional) Example of some other linear regression approach
        if you want to incorporate that in your code differently.
        """
        if len(self.past_data) <= 100:
            return False, 0
        self.past_data.pop(0)
        slope = np.dot(np.array(self.past_data), self.preCompute)[0]
        return True, slope

    def run(self, state: TradingState):
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))

        # Orders to be placed on exchange matching engine
        result = {}
        self.delay += 1

        for product in state.order_depths:
            orders: List[Order] = []
            order_depth: OrderDepth = state.order_depths[product]

            sell_order_length = len(order_depth.sell_orders)
            buy_order_length = len(order_depth.buy_orders)
            position = state.position.get(product, 0)

            # For demonstration, track average price for KELP
            if product == 'KELP' and sell_order_length > 0 and buy_order_length > 0:
                sell_price, _ = list(order_depth.sell_orders.items())[0]
                buy_price, _ = list(order_depth.buy_orders.items())[0]
                avg_price = (sell_price + buy_price) / 2
                self.kelp_timestep_to_avg_price[state.timestamp] = avg_price

            # Simple check
            success, market_price, vwap, buy_amt, sell_amt = self.VWAP(order_depth)
            if not success:
                # No valid VWAP
                result[product] = orders
                continue

            # Calculate short and long slopes, then interpret them
            short_slope, long_slope = self.slopeDetection()
            trend_signal = self.decide_entry_exit(short_slope, long_slope)

            logger.print(f"{product} => Market: {market_price:.2f}, VWAP: {vwap:.2f}, Trend: {trend_signal}")

            # We'll do an example logic:
            # - If BULLISH => place extra buy orders
            # - If BEARISH => place extra sell orders
            # - If NEUTRAL => place small "market-making" orders

            sell_lowest = list(order_depth.sell_orders.items())[0]
            buy_highest = list(order_depth.buy_orders.items())[0]
            sell_price, _ = sell_lowest
            buy_price, _ = buy_highest

            mkt_width = sell_price - buy_price

            if trend_signal == "BULLISH":
                # Buy near the top of the best bid
                price_to_buy = min(sell_price, int(vwap - mkt_width / 3))
                orders.append(Order(product, price_to_buy, int(buy_amt * 2)))  # buy heavier
                # Optionally place a minimal sell order up high to get out if needed
                price_to_sell = max(buy_price, int(vwap + mkt_width / 3))
                orders.append(Order(product, price_to_sell, -int(sell_amt)))

            elif trend_signal == "BEARISH":
                # Sell near the bottom of the best offer
                price_to_sell = max(buy_price, int(vwap + mkt_width / 3))
                orders.append(Order(product, price_to_sell, -int(sell_amt * 2)))  # sell heavier
                # Optionally place a small buy order down low to catch dips
                price_to_buy = min(sell_price, int(vwap - mkt_width / 3))
                orders.append(Order(product, price_to_buy, int(buy_amt)))

            else:
                # NEUTRAL: do basic market-making on each side
                price_to_sell = max(buy_price, int(vwap + mkt_width / 3))
                orders.append(Order(product, price_to_sell, -int(sell_amt)))
                price_to_buy = min(sell_price, int(vwap - mkt_width / 3))
                orders.append(Order(product, price_to_buy, int(buy_amt)))

            # Example additional signals: if the slope crosses from negative to positive, 
            # you might adjust or add more buys, etc.

            result[product] = orders

        # Trader data for next run
        traderData = "SAMPLE"

        # Example conversion request logic
        conversions = 0  # By default we don't do conversions
        logger.print(result)
        logger.flush(state, result, conversions, traderData)

        return result, conversions, traderData
