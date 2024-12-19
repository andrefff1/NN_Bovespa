# Extract technical data from assets

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

# Combine all data into a single DataFrame and rename columns
technicalData_yf = pd.concat(results, ignore_index=True)

# Rename columns
technicalData_yf.rename(
    columns={
        'Ticker': 'TICKER',
        'Date': 'DATE',
        'Close': 'CLOSE',
        'Adj Close': 'ADJ_CLOSE',
        'Market Cap': 'MARKET_CAP'
    },
    inplace=True
)

technicalData_yf = technicalData_yf[['TICKER', 'DATE', 'CLOSE', 'ADJ_CLOSE', 'MARKET_CAP']]

# Save to a CSV file
technicalData_yf.to_csv("Extracted/technicalData_yf.csv", sep=';', decimal='.', encoding='ISO-8859-1', index=False)

########################################################################################################################
# Extract BOVA11
print(f"Extracting data from BOVA11")

# Prepare a DataFrame for results
results = []

# Historical values
stock_info = yf.download("BOVA11.SA", start=start_date, end=end_date, interval="1mo")
# Number of shares
shares_outstanding = yf.Ticker("BOVA11.SA").info.get('sharesOutstanding', None)
# Ticker
stock_info['Ticker'] = "BOVA11.SA"
# Reset index and append
results.append(stock_info.reset_index())

# Combine all data into a single DataFrame and rename columns
technicalData_yf = pd.concat(results, ignore_index=True)


# Rename columns
technicalData_yf.rename(
    columns={
        'Ticker': 'TICKER',
        'Date': 'DATE',
        'Close': 'CLOSE'
    },
    inplace=True
)

technicalData_yf = technicalData_yf[['TICKER', 'DATE', 'CLOSE']]

# Save to a CSV file
technicalData_yf.to_csv("Extracted/technicalData_BOVA11_yf.csv", sep=';', decimal='.', encoding='ISO-8859-1',
                        index=False)
