# 1 - Merge fundamental and technical data on ticker and year.
# 2 - Perform drill across operation on year and year+1 to get the asset appreciation in a given year.
# 3 - Transform the data to get the final DataFrame with the necessary features.

import pandas as pd

########################################################################################################################
# Technical Data
# Retrieve technical data
print('Processing Technical Data')
technicalData_yf = pd.read_csv(f'../../Extract/YFinance/Extracted/technicalData_yf.csv', sep=';',
                               encoding='ISO-8859-1')

# Convert Date to pd.Datetime
technicalData_yf['DATE'] = pd.to_datetime(technicalData_yf['DATE'])

# Get year, month and year-1
technicalData_yf['YEAR'] = technicalData_yf['DATE'].dt.year
technicalData_yf['YEAR_MINUS_1'] = technicalData_yf['DATE'].dt.year - 1
technicalData_yf['MONTH'] = technicalData_yf['DATE'].dt.month

# Drill across operation
technicalData_yf_future = technicalData_yf[['TICKER', 'ADJ_CLOSE', 'YEAR_MINUS_1', 'MONTH']]
technicalData_yf_future = technicalData_yf_future.rename(
    columns={
        'TICKER': 'TICKER',
        'ADJ_CLOSE': 'FUTURE_ADJ_CLOSE',
        'YEAR_MINUS_1': 'YEAR',
        'MONTH': 'MONTH'
    }
)

technicalData_yf = technicalData_yf.merge(technicalData_yf_future, on=['TICKER', 'YEAR', 'MONTH'], how='left')

########################################################################################################################
# Get market aprreciation from BOVA11:

technicalData_BOVA11_yf = pd.read_csv(f'../../Extract/YFinance/Extracted/technicalData_BOVA11_yf.csv', sep=';',
                               encoding='ISO-8859-1')

# Convert Date to pd.Datetime
technicalData_BOVA11_yf['DATE'] = pd.to_datetime(technicalData_BOVA11_yf['DATE'])

# Get year, month and year-1
technicalData_BOVA11_yf['YEAR'] = technicalData_BOVA11_yf['DATE'].dt.year
technicalData_BOVA11_yf['YEAR_MINUS_1'] = technicalData_BOVA11_yf['DATE'].dt.year - 1
technicalData_BOVA11_yf['MONTH'] = technicalData_BOVA11_yf['DATE'].dt.month

# Drill across operation
technicalData_BOVA11_yf_future = technicalData_BOVA11_yf[['TICKER', 'CLOSE', 'YEAR_MINUS_1', 'MONTH']]
technicalData_BOVA11_yf_future = technicalData_BOVA11_yf_future.rename(
    columns={
        'TICKER': 'TICKER',
        'CLOSE': 'FUTURE_CLOSE',
        'YEAR_MINUS_1': 'YEAR',
        'MONTH': 'MONTH'
    }
)

technicalData_BOVA11_yf = technicalData_BOVA11_yf.merge(technicalData_BOVA11_yf_future, on=['TICKER', 'YEAR', 'MONTH'],
                                                        how='left')

# Get 1 year appreciation
technicalData_BOVA11_yf['APPRECIATION'] = \
    technicalData_BOVA11_yf['FUTURE_CLOSE']/technicalData_BOVA11_yf['CLOSE'] - 1

# Drop rows with NaN values in FUTURE_CLOSE_PRICE
# (which are residues from the previous iterations)
technicalData_BOVA11_yf.dropna(subset=['FUTURE_CLOSE'], how='any', inplace=True)

# Save IBOVESPA data
technicalData_BOVA11_yf[['TICKER', 'DATE', 'CLOSE', 'FUTURE_CLOSE', 'APPRECIATION']].\
    to_csv("../../Load/marketData.csv", sep=';', decimal='.', encoding='ISO-8859-1', index=False)

########################################################################################################################
# Fundamental Data
# Retrieve fundamental data
print('Processing Fundamental Data')
fundamentalData_CVM = pd.read_csv(f'../CVM/Transformed/fundamentalData_CVM.csv', sep=';', encoding='ISO-8859-1')

# Convert Date to pd.Datetime
fundamentalData_CVM['DT_REFER'] = pd.to_datetime(fundamentalData_CVM['DT_REFER'])

# Get year and month
fundamentalData_CVM['YEAR'] = fundamentalData_CVM['DT_REFER'].dt.year
fundamentalData_CVM['MONTH'] = fundamentalData_CVM['DT_REFER'].dt.month + 1

####################################################################################################################
# Outer merge Data
mergedData = technicalData_yf.merge(fundamentalData_CVM, on=['TICKER', 'YEAR', 'MONTH'], how='outer')

# List of fundamental features that need to be filled in NaN Spaces
fundamental_features = ['E', 'EPS', 'CA', 'CL', 'GROSS_DEBT', 'EQUITY', 'D']


# Fill NaN in fundamental data where Date difference is within 1 year
def fill_feature(row, feature, fundamental_data):
    if pd.isna(row[feature]):
        ref = fundamental_data[
            (fundamental_data['TICKER'] == row['TICKER']) &
            ((row['DATE'] - fundamental_data['DT_REFER']).dt.days <= 365) &
            ((row['DATE'] - fundamental_data['DT_REFER']).dt.days > 0)
        ]
        if not ref.empty:
            return ref[feature].iloc[-1]  # Take the most recent value within the range
    return row[feature]


# Apply the filling logic to all fundamental features
for fundamental_feature in fundamental_features:
    print('Forward filling NaNs for:', fundamental_feature)
    mergedData[fundamental_feature] = mergedData.apply(
        lambda row: fill_feature(row, fundamental_feature, fundamentalData_CVM), axis=1
    )

####################################################################################################################
# Calculate other features
print('Calculating all features')

# Weighted Average Number of Shares
mergedData['ANS'] = mergedData['E']/mergedData['EPS']

# Price to Earnings Ratio
mergedData['PE'] = mergedData['MARKET_CAP']/mergedData['E']

# Book Value per Share
mergedData['BVPS'] = mergedData['EQUITY']/mergedData['ANS']

# Return on Equities
mergedData['ROE'] = mergedData['E']/mergedData['EQUITY']

# Dividend Payout Ratio
mergedData['DPR'] = -mergedData['D']/mergedData['E']

# Dividend Yield
mergedData['DY'] = -mergedData['D']/mergedData['MARKET_CAP']

# Price to Book Ratio
mergedData['PBR'] = mergedData['MARKET_CAP']/mergedData['EQUITY']

# Current Ratio
mergedData['CURRENT_RATIO'] = mergedData['CA']/mergedData['CL']

# 1 Year Asset Appreciation
mergedData['APPRECIATION'] = mergedData['FUTURE_ADJ_CLOSE']/mergedData['ADJ_CLOSE'] - 1

# Class
mergedData['CLASS'] = 0
mergedData.loc[mergedData['APPRECIATION'] >= 0.8, 'CLASS'] = 1

####################################################################################################################
# Clean and save
print('Cleaning Data')
# Drop rows with NaN values in fundamental data or adjusted close price in next year
# (which are residues from the previous iterations)
mergedData.dropna(subset=['E', 'FUTURE_ADJ_CLOSE'], how='any', inplace=True)

# Drop rows with EPS = 0 (ANS will be infinite)
mergedData = mergedData[mergedData['EPS'] != 0]

# Save raw data to CSV
print('Saving Data')
mergedData.to_csv("mergedData.csv", sep=';', decimal='.', encoding='ISO-8859-1', index=False)

# Clean unused columns for the final model input

stockData = mergedData[['TICKER', 'DATE', 'PE', 'BVPS', 'ROE', 'DPR', 'DY', 'PBR', 'CA', 'GROSS_DEBT', 'ANS', 
                        'CURRENT_RATIO', 'EPS', 'APPRECIATION', 'CLASS']]

stockData.to_csv("../../Load/stockData.csv", sep=';', decimal='.', encoding='ISO-8859-1', index=False)
