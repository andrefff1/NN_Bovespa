# From data available on CVM, extracts .csv files and store then in the Extract folder

# Imports
import wget
from zipfile import ZipFile
import os

# Subtract 1 from first year, as the fundamental data will be shifted by six months.
# i.e. Analysis from 2013 to 2023 -> first_year = 2012
first_year = 2012
last_year = 2023

url_base = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/'

# Get file names to download
zip_files = []
for year in range(first_year, last_year+1):
    if not os.path.exists(f'dfp_cia_aberta_{year}.zip'):
        zip_files.append(f'dfp_cia_aberta_{year}.zip')

# Download files
for i, file in enumerate(zip_files):
    print('Dowloading File ('+str(i+1)+'/'+str(len(zip_files))+'):', file)
    wget.download(url_base+file, out='Extracted')

# Extract files
for i, file in enumerate(zip_files):
    print('Extractiong File ('+str(i+1)+'/'+str(len(zip_files))+'):', file)
    ZipFile('Extracted/'+file, 'r').extractall('Extracted')
