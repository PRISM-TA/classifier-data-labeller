from lib.labeller import load_data, save_labels
from lib.strategies.BuyAndHoldStrategy import BuyAndHoldStrategy
from lib.strategies.SellAndHoldStrategy import SellAndHoldStrategy
from lib.strategies.MeanReversionStrategy import MeanReversionStrategy

import numpy as np

ticker_df = load_data("AAPL")

# TODO: Wrap into a function + upload logic
window_size = 20

for offset in range(len(ticker_df)):
    window_df = ticker_df.iloc[offset:offset + window_size]
    if len(window_df) < window_size:
        continue

    start_date = window_df.index[0]
    end_date = window_df.index[-1]

    BaH_return_percentage = BuyAndHoldStrategy().execute(window_df)
    SaH_return_percentage = SellAndHoldStrategy().execute(window_df)
    MR_return_percentage = MeanReversionStrategy().execute(window_df)

    label = np.argmax([BaH_return_percentage, MR_return_percentage, SaH_return_percentage])

    print(f"Start date: {start_date}, End date: {end_date}")
    print(f"Label: {['Buy and Hold', 'Sell and Hold', 'Mean Reversion'][label]}")
    # print(f"Buy and Hold: {BaH_return_percentage}")
    # print(f"Sell and Hold: {SaH_return_percentage}")
    # print(f"Mean Reversion: {MR_return_percentage}")
    
# print(ticker_df)