# Strats

## 1. Market Orders and Order Matching
- **Leverage Best Prices**: Keep track of the best bid and ask prices. These are the most likely points where orders will be matched. Placing your orders at competitive prices can help you execute trades quickly and efficiently.
- **Immediate Execution**: Since the exchange executes orders immediately, you can take advantage of any price discrepancies in the market. If you spot an undervalued product (a buy order with a price lower than your expected price), you can place a buy order right away.
- **Partial Matches**: If your order doesn't match entirely, the remaining quantity is still visible to other bots. You can benefit from this by placing strategic orders that may be picked up by other bots if they find them favorable.

## 2. Price Dynamics and Market Analysis
- **Calculated Fair Value**: Determine the fair value of each product based on its price history, demand-supply trends, or any other insights you gain from the observations. This allows you to make informed buy/sell decisions. For instance, if your calculated fair value is significantly higher than the best ask, buying at that price could be a good move.
- **Track Trends**: If you can analyze past market trends (such as prices moving in a certain direction), you can anticipate the market’s next moves. Use the historical trades and orders to model how products might behave in the future and base your buy/sell decisions on these predictions.

## 3. Position Management
- **Avoid Position Limits**: Always keep an eye on your current position and the product's position limit. You can use this to your advantage by ensuring you stay within the limit and by making orders that help you adjust your position appropriately (e.g., reducing your long position in a product if it's getting too high).
- **Market Sentiment**: If you are able to assess whether bots are more likely to take certain actions (based on their own orders or market trades), you can predict and manipulate your position to maximize the return on your trades.

## 4. Strategic Order Placement
- **Timed Orders**: Make use of the available orders and position data to place timed orders that are likely to get matched as soon as possible. By being aggressive or subtle in your pricing, you can take advantage of order depth and make trades that profit from market inefficiencies.
- **Order Size**: Adjust your order size based on available liquidity. Large orders can sometimes be too risky, but smaller, more numerous orders can be easier to fill. Use this to balance risk and reward.

## 5. Bot Behavior Insights
- **Observations and Market Sentiment**: The observations object can provide valuable insights into the market conditions, such as sugar prices, transport fees, and sunlight index, which may impact the product’s price and demand. Analyzing these can give you a more refined view of the market and help you make better trading decisions.
- **Anticipate Bot Actions**: Bots will trade based on market data, and since they are all operating under similar conditions, you may be able to predict their behavior. By understanding how bots generally respond to orders (e.g., placing a large sell order when prices are high), you can strategically place your orders to either match their trades or take advantage of them.

## 6. Conversion Opportunities
- **Position Conversion**: If you have a position in a product, you can convert it into another product. This could help you hedge or re-balance your portfolio. Monitor the market conditions for each product and place conversions strategically to take advantage of market movements and tariffs.
- **Optimize Conversions**: Factor in transport fees, export/import tariffs, and other charges when deciding on conversion requests. By carefully considering the cost of conversions, you can decide whether it’s worth converting your positions based on the available margins.

## 7. Efficient State Management
- **Trader Data**: The `traderData` string allows you to store and retrieve state across multiple iterations. This is useful for tracking long-term trends and maintaining a consistent strategy. Keep important information about your past trades, positions, or observations in this variable to enhance your algorithm’s decision-making over time.
- **Reacting to Changing Conditions**: Market conditions will change frequently (e.g., products become available or new bots enter the market). Stay adaptable and adjust your strategy based on the state you have stored and the new data that comes in.

## 8. Leveraging Market Feedback
- **Reviewing Own Trades**: Keep track of your own trades and market trades to understand how your actions are affecting the market. This feedback loop allows you to adjust your strategy in future rounds.
- **Bot Behavior Reactions**: Analyze how bots react to your orders and others' orders. For example, if bots consistently sell at a certain price, you can plan to buy at that price when it's advantageous.

## 9. Optimizing for Speed
- **Efficient Algorithms**: Your algorithm must run within 900ms. Be mindful of the performance of your code. Avoid expensive operations like unnecessary loops or complex data manipulations during each iteration. Keeping the logic simple and direct will allow you to make decisions faster and more efficiently.

## 10. Sample Data
- **Use Available Data**: Sample data for each product will be available to help you understand market behavior and improve your strategy.
- **Analyze Historical Data**: Use the data to build a trading strategy that accounts for price trends, market orders, and bot behavior.

## 11. Optimizing Execution
- **Review Market Depth Regularly**: Stay up-to-date with the order depth to make quick decisions on where to place your orders and when to execute them based on best ask and bid prices.
- **Track Bid-Ask Spread**: Observe the bid-ask spread regularly to identify potential opportunities for profitable trades. 

By leveraging these opportunities, you can design a trading algorithm that is responsive, adaptable, and competitive in the marketplace. The key is understanding the market data, managing your positions effectively, and adapting your strategy based on real-time observations and feedback.
