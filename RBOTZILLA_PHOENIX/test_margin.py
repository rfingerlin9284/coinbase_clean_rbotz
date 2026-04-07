from util.margin_maximizer import MarginMaximizer, MarginConfig
mm = MarginMaximizer(MarginConfig())
print("--- DEFAULT ---")
mm.print_allocation_report(6500)
units = mm.calculate_position_size('EUR_USD', 1.1000, 30.0, 6500, 0.0, {})
print(f"Calculated Units for 30 pip SL on EUR_USD: {units}")
