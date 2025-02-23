from lib.strategies.BaseStrategy import BaseStrategy
import pandas as pd

class Decision:
    BUY = 0
    HOLD = 1
    SELL = 2

class MeanReversionStrategy(BaseStrategy):
    has_bought: bool = False
    def __init__(self):
        super().__init__()
    
    def _interpretRSI(self, rsi:float)->int:
        if rsi <= 30:
            return Decision.BUY
        elif rsi >= 70:
            return Decision.SELL
        else:
            return Decision.HOLD

    def _vote(self, data:pd.DataFrame, day:int)->int:
        rsi_lookback_window = 20
        vote_map = {
            Decision.BUY:0, 
            Decision.HOLD:0, 
            Decision.SELL:0
        }

        for i in range(1, rsi_lookback_window+1):
            column_name = f'rsi_{i}' 
            vote_map[self._interpretRSI(data[column_name].iloc[day])] += 1
        
        for decision, votes in vote_map.items():
            if votes > rsi_lookback_window // 2:
                return decision
        
        return Decision.HOLD

    def execute(self, data:pd.DataFrame)->float:
        if data.empty:
            return 0.0
        
        self.accumulated_return_percent = 0.0
        for day in range(len(data)):
            decision = self._vote(data, day)
            if decision == Decision.BUY:
                buy_spot = data['close'].iloc[day]
                self.has_bought = True
            if decision == Decision.SELL:
                sell_spot = data['close'].iloc[day]
                if self.has_bought:
                    self.accumulated_return_percent += ((sell_spot - buy_spot) / buy_spot) * 100
                    self.has_bought = False
        return self.accumulated_return_percent