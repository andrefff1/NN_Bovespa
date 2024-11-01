import yfinance as yf

# Lista de tickers
tickers = ["ABEV3.SA", "ACES4.SA", "AEDU3.SA", "AGEI3.SA", "ALLL11.SA", "ALLL3.SA", "ALPA4.SA", "ALSO3.SA"]

# Dicionário para armazenar os nomes das companhias
company_names = {}

# Obter informações de cada ticker
for ticker in tickers:
    stock_info = yf.Ticker(ticker)
    company_names[ticker] = stock_info.info.get('longName', 'Nome não encontrado')

# Exibir o resultado
for ticker, name in company_names.items():
    print(f"{ticker}: {name}")
