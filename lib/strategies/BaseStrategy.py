import pandas as pd

class BaseStrategy:
    accumulated_return_percent: float = 0.0
    def __init__(self):
        pass
    def execute(self, data:pd.DataFrame)->float:
        pass
