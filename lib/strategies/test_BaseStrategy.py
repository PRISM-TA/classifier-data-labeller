import pandas as pd
from BaseStrategy import BuyAndHoldStrategy, SellAndHoldStrategy, MeanReversionStrategy

def test_buy_and_hold_strategy():
    # Create a DataFrame with closing prices
    data = pd.DataFrame({
        'close': [100, 105, 110, 115]
    })
    
    strategy = BuyAndHoldStrategy()
    result = strategy.execute(data)
    
    expected_result = ((115 - 100) / 100) * 100
    assert abs(result - expected_result) < 1e-6, f"Expected {expected_result}, got {result}"
    print("BuyAndHoldStrategy test passed.")

def test_sell_and_hold_strategy():
    # Create a DataFrame with closing prices
    data = pd.DataFrame({
        'close': [100, 105, 110, 115]
    })
    
    strategy = SellAndHoldStrategy()
    result = strategy.execute(data)
    
    expected_result = -((115 - 100) / 100) * 100
    assert abs(result - expected_result) < 1e-6, f"Expected {expected_result}, got {result}"
    print("SellAndHoldStrategy test passed.")

def test_mean_reversion_strategy_no_sell():
    # Create a DataFrame with closing prices and RSI values
    data = pd.DataFrame({
        'close': [100, 95, 90, 85, 110, 115, 120],
        'rsi_14': [80, 75, 65, 50, 30, 25, 20]
    })
    
    strategy = MeanReversionStrategy()
    result = strategy.execute(data)
    expected_result = 0
    assert abs(result - expected_result) < 1e-6, f"Expected {expected_result}, got {result}"
    print("MeanReversionStrategy no sell test passed.")

def test_mean_reversion_strategy_no_buy():
    # Create a DataFrame with closing prices and RSI values
    data = pd.DataFrame({
        'close': [120, 115, 110, 85, 90, 95, 100], 
        'rsi_14': [35, 45, 60, 50, 65, 75, 80]
    })
    
    strategy = MeanReversionStrategy()
    result = strategy.execute(data)
    expected_result = 0
    assert abs(result - expected_result) < 1e-6, f"Expected {expected_result}, got {result}"
    print("MeanReversionStrategy no buy test passed.")

def test_mean_reversion_strategy_normal():
    # Create a DataFrame with closing prices and RSI values
    data = pd.DataFrame({
        'close': [95, 115, 110, 85, 90, 120, 100], 
        'rsi_14': [30, 45, 60, 50, 65, 75, 80]
    })
    
    strategy = MeanReversionStrategy()
    result = strategy.execute(data)
    buy_spot = data['close'].iloc[0]
    sell_spot = data['close'].iloc[-2]
    expected_result = (sell_spot - buy_spot) / buy_spot * 100
    assert abs(result - expected_result) < 1e-6, f"Expected {expected_result}, got {result}"
    print("MeanReversionStrategy no buy test passed.")

def main():
    test_buy_and_hold_strategy()
    test_sell_and_hold_strategy()
    test_mean_reversion_strategy_no_buy()
    test_mean_reversion_strategy_no_sell()
    test_mean_reversion_strategy_normal()

if __name__ == "__main__":
    main()
