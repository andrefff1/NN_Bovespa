import yfinance as yf
import pandas as pd

# Ticker list
stockList = pd.read_csv(f'../../Ticker_CVMCode.csv', sep=';', encoding='ISO-8859-1')
tickers = stockList['Ticker']

# Time period
start_date = "2013-01-01"
end_date = "2024-12-31"

# Prepare a DataFrame for results
results = []

# Extract information from the ticker
for ticker in tickers:
    print(f"Extracting data from {ticker}")

    try:
        # Historical values
        stock_info = yf.download(ticker + ".SA", start=start_date, end=end_date, interval="1mo")
        # Number of shares
        shares_outstanding = yf.Ticker(ticker + ".SA").info.get('sharesOutstanding', None)
        # Market Cap
        stock_info["Market Cap"] = stock_info['Close'] * shares_outstanding
        # Ticker
        stock_info['Ticker'] = ticker
        # Reset index and append
        results.append(stock_info.reset_index())

    except Exception as e:
        print(f"Failed to fetch data for {ticker}: {e}")

# Combine all data into a single DataFrame
technicalData_yf = pd.concat(results, ignore_index=True)
technicalData_yf = technicalData_yf[['Ticker', 'Date', 'Close', 'Adj Close', 'Market Cap']]

# Save to a CSV file
technicalData_yf.to_csv("Extracted/technicalData_yf.csv", index=False)
