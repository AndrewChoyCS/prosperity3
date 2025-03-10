from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order


class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}

        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':

                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]

                # Initialize the list of Orders to be sent as an empty list
                orders: List[Order] = []

                # Define a fair value for the PEARLS.
                # Note that this value of 1 is just a dummy value, you should likely change it!
                acceptable_price = 1

                # If statement checks if there are any SELL orders in the PEARLS market
                if len(order_depth.sell_orders) > 0:

                    # Sort all the available sell orders by their price,
                    # and select only the sell order with the lowest price
                    best_ask = min(order_depth.sell_orders.keys())
                    best_ask_volume = order_depth.sell_orders[best_ask]

                    # Check if the lowest ask (sell order) is lower than the above defined fair value
                    if best_ask < acceptable_price:

                        # In case the lowest ask is lower than our fair value,
                        # This presents an opportunity for us to buy cheaply
                        # The code below therefore sends a BUY order at the price level of the ask,
                        # with the same quantity
                        # We expect this order to trade with the sell order
                        print("BUY", str(-best_ask_volume) + "x", best_ask)
                        orders.append(Order(product, best_ask, -best_ask_volume))

                # The below code block is similar to the one above,
                # the difference is that it finds the highest bid (buy order)
                # If the price of the order is higher than the fair value
                # This is an opportunity to sell at a premium
                if len(order_depth.buy_orders) != 0:
                    best_bid = max(order_depth.buy_orders.keys())
                    best_bid_volume = order_depth.buy_orders[best_bid]
                    if best_bid > acceptable_price:
                        print("SELL", str(best_bid_volume) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_volume))

                # Add all the above the orders to the result dict
                result[product] = orders

        # Return the dict of orders
        # These possibly contain buy or sell orders for PEARLS
        print(result)
        return result


def __main__():
    # Create mock data for the TradingState object
    order_depths = {
        'RAINFOREST_RESIN': OrderDepth(),
        'KELP': OrderDepth()
    }
    
    # Add some dummy orders for RAINFOREST_RESIN to test
    order_depths['RAINFOREST_RESIN'].buy_orders = {5: 10, 6: 15}  # Buy orders at price 5 and 6
    order_depths['RAINFOREST_RESIN'].sell_orders = {3: -5, 4: -10}  # Sell orders at price 3 and 4
    # Add some dummy orders for KELP to test
    order_depths['KELP'].buy_orders = {5: 10, 6: 15}  # Buy orders at price 5 and 6
    order_depths['KELP'].sell_orders = {3: -5, 4: -10}  # Sell orders at price 3 and 4

    # Create a dummy TradingState
    trading_state = TradingState(
        traderData="test_data", 
        timestamp=1000, 
        listings={}, 
        order_depths=order_depths, 
        own_trades={}, 
        market_trades={}, 
        position={}, 
        observations={}
    )

    # Instantiate the Trader and run the method
    trader = Trader()
    trader.run(trading_state)


# Call the main function to execute the script
if __name__ == "__main__":
    __main__()
