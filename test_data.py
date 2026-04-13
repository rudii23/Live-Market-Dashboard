import yfinance as yf
import pandas as pd

TICKERS = ["^NSEI", "RELIANCE.NS", "INR=X", "BZ=F", "^TNX"]

def test_fetch():
    for ticker in TICKERS:
        print(f"Fetching {ticker}...")
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if data.empty:
            print(f"FAILED: {ticker} returned no data.")
            continue
            
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        last_close = data['Close'].iloc[-1]
        print(f"SUCCESS: {ticker} last close: {last_close}")
        
        ma20 = data['Close'].rolling(window=20).mean()
        ma50 = data['Close'].rolling(window=50).mean()
        print(f"MA20: {ma20.iloc[-1]}, MA50: {ma50.iloc[-1]}")
        print("-" * 20)

if __name__ == "__main__":
    test_fetch()
