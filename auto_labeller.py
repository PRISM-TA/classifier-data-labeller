from lib.labeller import load_data, save_labels
from lib.strategies.BuyAndHoldStrategy import BuyAndHoldStrategy
from lib.strategies.SellAndHoldStrategy import SellAndHoldStrategy
from lib.strategies.MeanReversionStrategy import MeanReversionStrategy

import numpy as np
from datetime import datetime

ticker_list = [
    "AAPL",
    "AXP",
    "BA",
    "CAT",
    "CSCO",
    "CVX",
    "DD",
    "DIS",
    "GE",
    "HD",
    "IBM",
    "INTC",
    "JNJ",
    "JPM",
    "KO",
    "MCD",
    "MMM",
    "MRK",
    "MSFT",
    "NKE",
    "PFE",
    "PG",
    "TRV",
    "UNH",
    "UTX",
    "VZ",
    "WMT",
    "XOM",
]
label_set = {}
window_size = 20

for ticker in ticker_list:
    ticker_df = load_data(ticker)
    print(f"[DEBUG] Processing {ticker}...")
    for offset in range(len(ticker_df)):
        window_df = ticker_df.iloc[offset : offset + window_size]
        if len(window_df) < window_size:
            continue

        start_date = window_df.index[0]
        end_date = window_df.index[-1]

        BaH_return_percentage = BuyAndHoldStrategy().execute(window_df)
        SaH_return_percentage = SellAndHoldStrategy().execute(window_df)
        MR_return_percentage = MeanReversionStrategy().execute(window_df)

        label = np.argmax(
            [BaH_return_percentage, MR_return_percentage, SaH_return_percentage]
        )
        pkey = f"{ticker}_{start_date.strftime('%Y-%m-%d')}"
        timestamp = datetime.now().isoformat()
        label_set[pkey] = {
            "ticker": ticker,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "pattern": ["uptrend", "sideways", "downtrend"][label],
            "timestamp": timestamp,
        }
    print(f"[DEBUG] Finished processing {ticker}")

save_labels(label_set, filename="auto_labels.csv")
