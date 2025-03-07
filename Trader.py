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
      self.positions = { "RAINFOREST_RESIN": [0, 0], "KELP": [0, 0]}
      self.past_data = []
      self.time_stamp = np.array([[i for i in range(1, 101)]])
      self.preCompute = np.linalg.pinv(self.time_stamp.transpose() @ self.time_stamp) @ self.time_stamp.transpose()
    
    def VWAP(self, order_depth: OrderDepth):
      sell_lowest = list(order_depth.sell_orders.items())[0]
      buy_highest = list(order_depth.buy_orders.items())[0]

      sell_price, sell_amount = sell_lowest
      buy_price, buy_amount = buy_highest
      market_price = (sell_price + buy_price) / 2

      total_orders = 0
      sell_orders = list(order_depth.sell_orders.items())[0:3]
      buy_orders = list(order_depth.buy_orders.items())[0:3]
      volume_avg = 0

      for item in sell_orders:
        price, size = item
        volume_avg += price * size
        total_orders += size
      
      for item in buy_orders:
        price, size = item
        volume_avg += price*size
        total_orders += size

      if total_orders == 0:
        return False, 10000, 0, 1, 1


      volume_avg = volume_avg / total_orders
      buy_amount = min(max(1, (volume_avg - market_price) * 4), 20)
      sell_amount = min(max(1, (market_price - volume_avg) * 4), 20)
      
      return True, market_price, volume_avg, buy_amount, sell_amount

    def LinearRegression (self):
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
        for product in state.order_depths:
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            sell_order_length = len(order_depth.sell_orders)
            buy_order_length = len(order_depth.buy_orders)

            badAlgo = True
            position = state.position[product] if product in state.position else 0
            if (badAlgo):
              success, market_price, vwap, buy_amt, sell_amt = self.VWAP(order_depth)
              logger.print(f"{product} Market Price: " + str(market_price) + " " + str(vwap) + " " + str(buy_amt) + " " + str(sell_amt))
              if success:
                orders.append(Order(product, int(market_price) + 1, -int(sell_amt)))
                orders.append(Order(product, int(market_price) - 1,  int(buy_amt)))

            else:
              position = state.position[product] if product in state.position else 0
              max_sell_size = -20 - position
              max_buy_size = 20 - position
              if product == "RAINFOREST_RESIN":
                acceptable_price = 10000 # Participant should calculate this value

                if sell_order_length != 0 and buy_order_length != 0:
                   best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                   best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                   market_price = (best_ask + best_bid)/2
                   market_spread = int(best_ask - best_bid)
                   if market_spread == 1:
                      best_ask = math.ceil(market_spread)
                      best_bid = math.floor(market_spread)
                      sell_size = min(abs(max_sell_size), max(1, 20 - 5*abs(best_ask - acceptable_price)))
                      buy_size = min(max_buy_size, max(1, 20 - 5*abs(best_bid - acceptable_price)))
                      orders.append(Order(product, best_ask, -1*sell_size))
                      orders.append(Order(product, best_bid, buy_size))
                   elif market_spread == 2:
                      if market_price > acceptable_price:
                         sell_size = min(abs(max_sell_size), max(1, 20 - 5*abs(best_ask - 1 - acceptable_price)))
                         buy_size = min(max_buy_size, max(1, 20 - 5*abs(best_bid - acceptable_price)))
                         orders.append(Order(product, best_ask-1, -1*sell_size))
                         orders.append(Order(product, best_bid, buy_size))
                      elif market_price < acceptable_price:
                         sell_size = min(abs(max_sell_size), max(1, 20 - 5*abs(best_ask - acceptable_price)))
                         buy_size = min(max_buy_size, max(1, 20 - 5*abs(best_bid + 1 - acceptable_price)))
                         orders.append(Order(product, best_ask, -1*sell_size))
                         orders.append(Order(product, best_bid+1, buy_size))
                   else:
                      sell_size = min(abs(max_sell_size), max(1, 20 - 5*abs(best_ask - 1 - acceptable_price)))
                      buy_size = min(max_buy_size, max(1, 20 - 5*abs(best_bid + 1 - acceptable_price)))
                      orders.append(Order(product, best_ask-1, -1*sell_size))
                      orders.append(Order(product, best_bid+1, buy_size))

                # if sell_order_length != 0:
                #     best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                #     if best_ask < acceptable_price:
                #        print("BUY", str(best_ask_amount) + "x", best_ask)
                #        orders.append(Order(product, best_ask, min(max_buy_size, -best_ask_amount)))
                #     else:
                #        orders.append(Order(product, min(acceptable_price+1, best_ask), max_sell_size))
                # else:
                #    orders.append(Order(product, acceptable_price+1, max_sell_size))
        
                # if buy_order_length != 0:
                #     best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                #     if best_bid > acceptable_price:
                #        print("SELL", str(best_bid_amount) + "x", best_bid)
                #        orders.append(Order(product, best_bid, max(-best_bid_amount, max_sell_size)))
                #     else:
                #        orders.append(Order(product, max(acceptable_price-1, best_bid), max_buy_size))
                # else:
                #    orders.append(Order(product, acceptable_price-1, max_buy_size))

              if product == "KELP": 
                if buy_order_length != 0 and sell_order_length != 0:
                  best_bid = list(order_depth.buy_orders.items())[0][0]
                  best_ask = list(order_depth.sell_orders.items())[0][0]
                  market_price = (best_bid + best_ask) / 2
                elif buy_order_length != 0:
                   market_price = list(order_depth.buy_orders.items())[0][0]
                elif sell_order_length != 0:
                   market_price = list(order_depth.sell_orders.items())[0][0]
                else:
                   market_price = 5000
                self.past_data.append(market_price)
                success, direction = self.LinearRegression()
                if success:
                    if direction > 0:
                        orders.append(Order(product, int(best_bid)+1, max_buy_size))
                    elif direction < 0:
                        orders.append(Order(product, int(best_ask)-1, max_sell_size))
                 
            result[product] = orders

		    # String value holding Trader state data required. 
				# It will be delivered as TradingState.traderData on next execution.
        traderData = "SAMPLE" 
        
				# Sample conversion request. Check more details below. 
        conversions = abs(position) if abs(position) == 20 else 0
        
        logger.flush(state, result, conversions, traderData)
        
        return result, conversions, traderData