# From the data Extracted in the Extract Step, get the relevant Fundamental Data for the analysis and store it in a
# CSV File

import pandas as pd
import numpy as np

########################################################################################################################
# Data import

# Set the display option to show all columns
pd.set_option('display.max_columns', None)
# Set display option to show all rows
pd.set_option('display.max_rows', None)

# CSV File Names Suffixes to extract data from:
# DRE_con:      Demonstração de Resultado - Consolidado
# DFC_MI_con:   Demonstração de Fluxo de Caixa - Método Indireto - Consolidado
# DFC_MD_con:   Demonstração de Fluxo de Caixa - Método Direto - Consolidado
# BPA_con:      Balanço Patrimonial Ativo - Consolidado
# BPP_con:      Balanço Patrimonial Passivo - Consolidado
# DRE_ind:      Demonstração de Resultado - Individual
# DFC_MI_ind:   Demonstração de Fluxo de Caixa - Método Indireto - Individual
# DFC_MD_ind:   Demonstração de Fluxo de Caixa - Método Direto - Individual
# BPA_ind:      Balanço Patrimonial Ativo - Individual
# BPP_ind:      Balanço Patrimonial Passivo - Individual
file_suffix = ['DRE_con', 'DFC_MI_con', 'DFC_MD_con', 'BPA_con', 'BPP_con', 'DRE_ind', 'DFC_MI_ind', 'DFC_MD_ind',
               'BPA_ind', 'BPP_ind']

# Subtract 1 from first year, as the fundamental data will be shifted by six months.
# i.e. Analysis from 2013 to 2023 -> first_year = 2012
first_year = 2012
last_year = 2023

# Dictionary to store DataFrames with suffix as the key
data_frames = {}

for suffix in file_suffix:
    file = pd.DataFrame()
    for year in range(first_year, last_year+1):
        file = pd.concat([file, pd.read_csv(f'../../Extract/CVM/Extracted/dfp_cia_aberta_{suffix}_{year}.csv', sep=';',
                                            decimal='.', encoding='ISO-8859-1')])
        print(f'{suffix} ({year}) - Shape: {file.shape}')
    data_frames[suffix] = file  # store in dictionary
    print(f'Combined DataFrame for {suffix}: {file.shape}')

# Combine DFC_MI_con and DFC_MD_con into a new DataFrame
data_frames['DFC_con'] = pd.concat([data_frames['DFC_MI_con'], data_frames['DFC_MD_con']], ignore_index=True)

# Combine DFC_MI_ind and DFC_MD_ind into a new DataFrame
data_frames['DFC_ind'] = pd.concat([data_frames['DFC_MI_ind'], data_frames['DFC_MD_ind']], ignore_index=True)

# Drop the old DFC_MI_con and DFC_MD_con DataFrames
del data_frames['DFC_MI_con']
del data_frames['DFC_MD_con']
# Drop the old DFC_MI_ind and DFC_MD_ind DataFrames
del data_frames['DFC_MI_ind']
del data_frames['DFC_MD_ind']

########################################################################################################################
# Cleaning

for key in data_frames.keys():
    print(f'Cleaning ORDER_EXERC from {key}')

    # Remove data from second to last year (Penúltimo)
    data_frames[key] = data_frames[key][data_frames[key]['ORDEM_EXERC'] == 'ÚLTIMO']

    # Transform DT_REFER to DateTime.
    # Shift DateTime six months in the future (to keep the model in training phase from accessing data it would
    # not have access to)
    data_frames[key]['DT_REFER'] = pd.to_datetime(data_frames[key]['DT_REFER']) + pd.DateOffset(months=6)

    # Turn CD_CVM to String
    data_frames[key]['CD_CVM'] = data_frames[key]['CD_CVM'].astype(str)

    # If column ESCALA_MOEDA is MIL, multiply VL_CONTA by 1000
    # Except if the row shows EPS value (CD_CONTA contains 3.99)
    data_frames[key]['VL_CONTA'] = np.where((data_frames[key]['ESCALA_MOEDA'] == 'MIL') &
                                            (~data_frames[key]['CD_CONTA'].
                                            str.contains("3.99", case=False, na=False)),
                                            data_frames[key]['VL_CONTA'] * 1000,
                                            data_frames[key]['VL_CONTA'])
    # Drop columns of no interest
    data_frames[key].drop(['CNPJ_CIA', 'VERSAO', 'GRUPO_DFP', 'MOEDA', 'ESCALA_MOEDA', 'ORDEM_EXERC',
                          'DT_FIM_EXERC', 'ST_CONTA_FIXA'], axis=1, inplace=True)
    if key in ['DRE_con', 'DFC_con', 'DRE_ind', 'DFC_ind']:
        data_frames[key].drop(
            ['DT_INI_EXERC'], axis=1, inplace=True)

########################################################################################################################
# The resulting dataframes will be merged with the Ticker_CVMCode data in order to create a new Dataframe with only the
# stocks of interest. The script will run through the sheets generated so far to fill the empty spaces with the
# fundamental data required.

stockList = pd.read_csv(f'../../Ticker_CVMCode.csv', sep=';', encoding='ISO-8859-1')

# Drop rows with companies without information
stockList = stockList[stockList['DENOM_CIA'] != '-']

# Add empty columns with the relevant data:
columns = {
    'TICKER': None,
    'DT_REFER': None,   # Reference Date
    'E': None,          # Earnings
    'EPS': None,        # Earnings per Share
    'CA': None,         # Current Assets
    'CL': None,         # Current Liabilities
    'GROSS_DEBT': None,
    'EQUITY': None,
    'D': None           # Dividends
}

# Add the columns all at once
fundamentalData = pd.DataFrame(columns=columns)

# The script will run through each stock of the stockList dataframe and collect the relevant data from the sheets
# extracted earlier
for i, ticker in enumerate(stockList['Ticker']):

    # Trigger to orient the processes inside the if's statements
    # 0: no effect
    # 1: data unavailable in the '_con' sheets
    # 2: data unavailable in any sheet
    trigger = 0

    # Get CVM Code from Ticker
    cvm_code = stockList[stockList['Ticker'] == ticker]['CD_CVM'].iloc[0]
    print(f'Processing {ticker}: {i+1}/{len(stockList["Ticker"])}')

    ####################################################################################################################
    # Extract Earnings
    # Filter sheet to get only data of the analysed Ticker and data regarding Earnings
    filtered_data = data_frames['DRE_con'][(data_frames['DRE_con']['CD_CVM'] == cvm_code) &
                                           data_frames['DRE_con']['DS_CONTA'].
                                           str.contains("lucro", case=False, na=False) &
                                           data_frames['DRE_con']['DS_CONTA'].
                                           str.contains("preju[ií]zo", case=False, na=False) &
                                           data_frames['DRE_con']['DS_CONTA'].
                                           str.contains("consolidado do per[ií]odo", case=False, na=False)]

    fundamentalData = pd.concat([fundamentalData, pd.DataFrame({'TICKER': [ticker] * len(filtered_data['DT_REFER']),
                                                                'DT_REFER': filtered_data['DT_REFER'],
                                                                'E': filtered_data['VL_CONTA']})], ignore_index=True)

    # If the Stock is not present in DRE_con Sheet, it must be searched for in the DRE_ind
    if filtered_data.empty:
        trigger = 1
        filtered_data = data_frames['DRE_ind'][(data_frames['DRE_ind']['CD_CVM'] == cvm_code) &
                                               data_frames['DRE_ind']['DS_CONTA'].
                                               str.contains("lucro", case=False, na=False) &
                                               data_frames['DRE_ind']['DS_CONTA'].
                                               str.contains("preju[ií]zo", case=False, na=False) &
                                               data_frames['DRE_ind']['DS_CONTA'].
                                               str.contains("do per[ií]odo", case=False, na=False)]
        fundamentalData = pd.concat([fundamentalData, pd.DataFrame({'TICKER': [ticker] * len(filtered_data['DT_REFER']),
                                                                    'DT_REFER': filtered_data['DT_REFER'],
                                                                    'E': filtered_data['VL_CONTA']})],
                                    ignore_index=True)
        # If the ticker is also not present in DRE_ind, append it in the fundamentalData but keep all columns empty
        if filtered_data.empty:
            trigger = 2
            print('Warning: Ticker not in DRE Sheets!')
            fundamentalData = pd.concat([fundamentalData, pd.DataFrame({'TICKER': ticker})])

    ####################################################################################################################
    # Extract Earning per Share
    # Filter sheet to get only data of the analysed Ticker and data regarding Earnings per Share
    # Iterate in the Dates extracted from the Earnings step:
    for date in filtered_data['DT_REFER']:
        # If data is in _con Sheet
        if trigger == 0:
            filtered_EPS = data_frames['DRE_con'][(data_frames['DRE_con']['CD_CVM'] == cvm_code) &
                                                  (data_frames['DRE_con']['DT_REFER'] == date) &
                                                  data_frames['DRE_con']['CD_CONTA'].
                                                  str.contains("3.99", case=False, na=False)]
        # If data is in _ind Sheet
        elif trigger == 1:
            filtered_EPS = data_frames['DRE_ind'][(data_frames['DRE_ind']['CD_CVM'] == cvm_code) &
                                                  (data_frames['DRE_ind']['DT_REFER'] == date) &
                                                  data_frames['DRE_ind']['CD_CONTA'].
                                                  str.contains("3.99", case=False, na=False)]
        # If no data was retrieved in the previous iteration
        else:
            break

        EPS = None  # Initialize EPS to None or another default value

        # CD_CONTA values related to EPS. It is not standardized, so some trial and error is required to get a valid
        # value.
        codes_to_check = ['3.99.02.02', '3.99.02.01', '3.99.01.02', '3.99.01.01', '3.99.02', '3.99.01', '3.99']

        for code in codes_to_check:
            values = filtered_EPS['VL_CONTA'][filtered_EPS['CD_CONTA'] == code]
            ds_conta = filtered_EPS['DS_CONTA'][filtered_EPS['CD_CONTA'] == code]
            earnings = fundamentalData.loc[(fundamentalData['TICKER'] == ticker) &
                                           (fundamentalData['DT_REFER'] == date), 'E'].iloc[0]
            if not values.empty and values.iloc[0] != 0:
                EPS = values.iloc[0]

                # Check if the conditions to break the loop are met
                # If checking codes 3.99.0X.0X, only break in the DS_CONTA received is 'ON' (ordinary stocks)
                # Also check for errors in the EPS entry (Earnings and EPS must have the same sign)
                if ((code in ['3.99.02.02', '3.99.02.01', '3.99.01.02', '3.99.01.01'] and ds_conta.iloc[0] == 'ON') or
                        code in ['3.99.02', '3.99.01']) and \
                        (earnings * EPS > 0):
                    break  # Stop once we find a valid EPS value
            elif (code == '3.99') and (values.iloc[0] == 0):
                EPS = 0

        fundamentalData.loc[(fundamentalData['TICKER'] == ticker) &
                            (fundamentalData['DT_REFER'] == date), 'EPS'] = EPS

    ####################################################################################################################
    # Extract Current Assets (CA)
    filtered_CA = pd.DataFrame()
    if trigger == 0:
        filtered_CA = data_frames['BPA_con'][(data_frames['BPA_con']['CD_CVM'] == cvm_code) &
                                             (data_frames['BPA_con']['CD_CONTA'] == '1.01')].copy()
    elif trigger == 1:
        filtered_CA = data_frames['BPA_ind'][(data_frames['BPA_ind']['CD_CVM'] == cvm_code) &
                                             (data_frames['BPA_ind']['CD_CONTA'] == '1.01')].copy()
    else:
        continue
    filtered_CA.loc[:, 'TICKER'] = ticker

    # MergeAndTransform the current fundamentalData to the filtered_CA dataframe where TICKER and DT_REFER match.
    # Assign the VL_CONTA value in filtered_CA to CA in fundamentalData
    merged_df = fundamentalData[fundamentalData['TICKER'] == ticker].\
        merge(filtered_CA[['TICKER', 'DT_REFER', 'VL_CONTA']], on=['TICKER', 'DT_REFER'], how='left')
    fundamentalData.loc[fundamentalData['TICKER'] == ticker, 'CA'] = merged_df['VL_CONTA'].values

    ####################################################################################################################
    # Extract Current Liabilities (CL)
    filtered_CL = pd.DataFrame()
    if trigger == 0:
        filtered_CL = data_frames['BPP_con'][(data_frames['BPP_con']['CD_CVM'] == cvm_code) &
                                             (data_frames['BPP_con']['CD_CONTA'] == '2.01')].copy()
    elif trigger == 1:
        filtered_CL = data_frames['BPP_ind'][(data_frames['BPP_ind']['CD_CVM'] == cvm_code) &
                                             (data_frames['BPP_ind']['CD_CONTA'] == '2.01')].copy()
    else:
        continue
    filtered_CL.loc[:, 'TICKER'] = ticker

    # MergeAndTransform the current fundamentalData to the filtered_CL dataframe where TICKER and DT_REFER match.
    # Assign the VL_CONTA value in filtered_CL to CL in fundamentalData
    merged_df = fundamentalData[fundamentalData['TICKER'] == ticker].\
        merge(filtered_CL[['TICKER', 'DT_REFER', 'VL_CONTA']], on=['TICKER', 'DT_REFER'], how='left')
    fundamentalData.loc[fundamentalData['TICKER'] == ticker, 'CL'] = merged_df['VL_CONTA'].values

    ####################################################################################################################
    # Extract Gross Debt
    filtered_GD = pd.DataFrame()
    aggregated_GD = pd.DataFrame()
    if trigger == 0:
        filtered_GD = data_frames['BPP_con'][(data_frames['BPP_con']['CD_CVM'] == cvm_code) &
                                             ((data_frames['BPP_con']['CD_CONTA'] == '2.01.04') |
                                             (data_frames['BPP_con']['CD_CONTA'] == '2.02.01'))].copy()

    elif trigger == 1:
        filtered_GD = data_frames['BPP_ind'][(data_frames['BPP_ind']['CD_CVM'] == cvm_code) &
                                             ((data_frames['BPP_ind']['CD_CONTA'] == '2.01.04') |
                                              (data_frames['BPP_ind']['CD_CONTA'] == '2.02.01'))].copy()
    else:
        continue
    if not filtered_GD.empty:
        filtered_GD.loc[:, 'TICKER'] = ticker
        # Gross debt is the sum of the values of current debt and non-current debt
        aggregated_GD = filtered_GD.groupby(['TICKER', 'DT_REFER'], as_index=False)['VL_CONTA'].sum()

        # MergeAndTransform the current fundamentalData to the aggregated_GD dataframe where TICKER and DT_REFER match.
        # Assign the VL_CONTA value in aggregated_GD to GROSS DEBT in fundamentalData
        merged_df = fundamentalData[fundamentalData['TICKER'] == ticker].\
            merge(aggregated_GD[['TICKER', 'DT_REFER', 'VL_CONTA']], on=['TICKER', 'DT_REFER'], how='left')
        fundamentalData.loc[fundamentalData['TICKER'] == ticker, 'GROSS_DEBT'] = merged_df['VL_CONTA'].values

    ####################################################################################################################
    # Extract Equity (patrimônio líquido)
    filtered_EQ = pd.DataFrame()
    if trigger == 0:
        filtered_EQ = data_frames['BPP_con'][(data_frames['BPP_con']['CD_CVM'] == cvm_code) &
                                             data_frames['BPP_con']['DS_CONTA'].
                                             str.contains("patrim[oô]nio l[ií]quido consolidado",
                                                          case=False, na=False)].copy()
    elif trigger == 1:
        filtered_EQ = data_frames['BPP_ind'][(data_frames['BPP_ind']['CD_CVM'] == cvm_code) &
                                             data_frames['BPP_ind']['DS_CONTA'].
                                             str.contains("patrim[oô]nio l[ií]quido",
                                                          case=False, na=False)].copy()
    else:
        continue
    filtered_EQ.loc[:, 'TICKER'] = ticker

    # MergeAndTransform the current fundamentalData to the filtered_EQ dataframe where TICKER and DT_REFER match.
    # Assign the VL_CONTA value in filtered_EQ to EQUITY in fundamentalData
    merged_df = fundamentalData[fundamentalData['TICKER'] == ticker].\
        merge(filtered_EQ[['TICKER', 'DT_REFER', 'VL_CONTA']], on=['TICKER', 'DT_REFER'], how='left')
    fundamentalData.loc[fundamentalData['TICKER'] == ticker, 'EQUITY'] = merged_df['VL_CONTA'].values

    ####################################################################################################################
    # Extract Dividends (D)
    filtered_D = pd.DataFrame()
    aggregated_D = pd.DataFrame()
    if trigger == 0:
        filtered_D = data_frames['DFC_con'][(data_frames['DFC_con']['CD_CVM'] == cvm_code) &
                                            (data_frames['DFC_con']['CD_CONTA'].isin(
                                                [f"6.03.{i:02d}" for i in range(1, 21)])) &
                                            (data_frames['DFC_con']['DS_CONTA'].
                                             str.contains("dividend", case=False, na=False) |
                                             (data_frames['DFC_con']['DS_CONTA'].
                                              str.contains("juro", case=False, na=False) &
                                              data_frames['DFC_con']['DS_CONTA'].
                                              str.contains("capital pr[oó]prio", case=False, na=False))) &
                                            (data_frames['DFC_con']['VL_CONTA'] < 0)].copy()

    elif trigger == 1:
        filtered_D = data_frames['DFC_ind'][(data_frames['DFC_ind']['CD_CVM'] == cvm_code) &
                                            (data_frames['DFC_ind']['CD_CONTA'].isin(
                                                [f"6.03.{i:02d}" for i in range(1, 21)])) &
                                            (data_frames['DFC_ind']['DS_CONTA'].
                                             str.contains("dividend", case=False, na=False) |
                                             (data_frames['DFC_ind']['DS_CONTA'].
                                             str.contains("juro", case=False, na=False) &
                                             data_frames['DFC_ind']['DS_CONTA'].
                                             str.contains("capital pr[oó]prio", case=False, na=False))) &
                                            (data_frames['DFC_ind']['VL_CONTA'] < 0)].copy()
    else:
        continue
    if not filtered_D.empty:
        filtered_D.loc[:, 'TICKER'] = ticker
        # Aggregate values extracted by sum
        aggregated_D = filtered_D.groupby(['TICKER', 'DT_REFER'], as_index=False)['VL_CONTA'].sum()

        # MergeAndTransform the current fundamentalData to the aggregated_D dataframe where TICKER and DT_REFER match.
        # Assign the VL_CONTA value in aggregated_D to D in fundamentalData
        merged_df = fundamentalData[fundamentalData['TICKER'] == ticker].\
            merge(aggregated_D[['TICKER', 'DT_REFER', 'VL_CONTA']], on=['TICKER', 'DT_REFER'], how='left')
        fundamentalData.loc[fundamentalData['TICKER'] == ticker, 'D'] = merged_df['VL_CONTA'].values

# fill NaN with zeros
fundamentalData.fillna({'D': 0.0}, inplace=True)
fundamentalData.fillna({'CL': 0.0}, inplace=True)
fundamentalData.fillna({'GROSS_DEBT': 0.0}, inplace=True)

fundamentalData.to_csv('Transformed/fundamentalData_CVM.csv', sep=';', decimal='.', encoding='ISO-8859-1', index=False)
print('fundamentalData_CVM successfully generated')

# NOTES

# Get only CD_CONTA of interest
# DRE_con:
#       3.09:       Lucro/Prejuízo Consolidado do Período
#       3.11:       Lucro ou Prejuízo Líquido Consolidado do Período / Lucro/Prejuízo Consolidado do Período
#       3.13:       Lucro/Prejuízo Consolidado do Período
#       3.99.02.01: Lucro Diluído por Ação: ON/PN
#
#       NOTE: Whether 3.09, 3.11 or 3.13 refers to Earnings is not standardized. All three will be extracted and only
#       the one with 'lucro', 'prejuízo' and 'Consolidado do Período' in 'DS_CONTA' will be kept.
#
# BPA_con:
#       1:          Ativo Total
#       1.01:       Caixa e Equivalentes de Caixa / Ativo Circulante
# BPP_con:
#       2.01:       Passivo Circulante
#       2.01.04:    Passivo Circulante - Empréstimos e Financiamentos
#       2.02.01:    Passivo Não Circulante - Empréstimos e Financiamentos
#       2.07:       Patrimônio Líquido Consolidado
# DFC_con:
#       6.03.01 to 6.03.20
#
# NOTE: There is no fixed standard on whether the CD_CONTA in DFC_con concerns the payment of dividends
# Any CD_CONTA from the 6.03.XX subgroup with negative values and 'Dividendos' in 'DS_CONTA' will be considered
# as dividend payout. All the values extracted will then be aggregated by sum in the column 'Dividend'.
#
# NOTE: IND sheets will only be used if there is no data for a given company in the CON sheets



