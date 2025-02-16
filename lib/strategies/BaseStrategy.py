import pandas as pd

class BaseStrategy:
    accumulated_return_percent: float = 0.0
    def __init__(self):
        pass
    def execute(self, data:pd.DataFrame)->float:
        pass

class BuyAndHoldStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
    def execute(self, data:pd.DataFrame)->float:
        # Ensure the DataFrame is not empty
        if data.empty:
            return 0.0
        
        # Get the closing prices of the first and last rows
        first_close = data['close'].iloc[0]
        last_close = data['close'].iloc[-1]
        
        # Calculate the percentage change
        self.accumulated_return_percent = ((last_close - first_close) / first_close) * 100
        
        return self.accumulated_return_percent

class SellAndHoldStrategy(BaseStrategy):
    def __init__(self):
        super().__init__()
    def execute(self, data:pd.DataFrame)->float:
        # Ensure the DataFrame is not empty
        if data.empty:
            return 0.0
        
        # Get the closing prices of the first and last rows
        first_close = data['close'].iloc[0]
        last_close = data['close'].iloc[-1]
        
        # Calculate the percentage change
        self.accumulated_return_percent = -((last_close - first_close) / first_close) * 100
        
        return self.accumulated_return_percent

class MeanReversionStrategy(BaseStrategy):
    has_bought: bool = False
    def __init__(self):
        super().__init__()
    def execute(self, data:pd.DataFrame)->float:
        if data.empty:
            return 0.0
        
        self.accumulated_return_percent = 0.0
        for day in range(len(data)):
            rsi_14 = data['rsi_14'].iloc[day]
            if rsi_14 <= 30:
                buy_spot = data['close'].iloc[day]
                self.has_bought = True
            if rsi_14 >= 70:
                sell_spot = data['close'].iloc[day]
                if self.has_bought:
                    self.accumulated_return_percent += ((sell_spot - buy_spot) / buy_spot) * 100
                    self.has_bought = False
        return self.accumulated_return_percent