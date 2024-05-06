import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import netCDF4 as nc
import dateutil.parser
import datetime
import gzip
import shutil

# read the data
ice_vol = pd.read_table('data/vol/ice_vol.dat', sep='\s+')
ice_vol = ice_vol.to_numpy()
ice_vol = np.delete(ice_vol, range(16425, 16485), 0)
ice_vol_year = ice_vol = ice_vol.reshape((45, 365, 3))
ice_vol_year_average = [0]*45

# plot
# 45 years month-average
plt.figure()
day_sequence = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
month = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
plt.xticks(day_sequence, month, fontsize=12, rotation=45)
plt.yticks(range(2, 37, 4), fontsize=12)
plt.xlabel('Month', fontsize=14)
plt.ylabel('Sea Ice Volume/10\N{SUPERSCRIPT THREE} km\N{SUPERSCRIPT THREE}', fontsize=14)
plt.xlim(0, 365)
plt.ylim(2, 34)
plt.title('1979-2023 daily SIV', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
for i in range(45):
    plt.plot(range(365), ice_vol_year[i, :, 2], linewidth=2.0)
plt.savefig('picture/vol/1979_2023_daily.png', dpi=500)

# 45 years average SIV
for i in range(45):
    for j in range(365):
        ice_vol_year_average[i] += ice_vol_year[i, j, 2]
    ice_vol_year_average[i] = ice_vol_year_average[i]/365
plt.figure()
plt.plot(range(1979, 2024), ice_vol_year_average, linewidth=2.0)
plt.xticks(range(1979, 2025, 5), fontsize=12, rotation=45)
plt.yticks(range(2, 37, 4), fontsize=12)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Sea Ice Volume/10\N{SUPERSCRIPT THREE} km\N{SUPERSCRIPT THREE}', fontsize=14)
plt.xlim(1979, 2024)
plt.ylim(2, 34)
plt.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
plt.title('1979-2023 yearly SIV', fontsize=12)
plt.savefig('picture/vol/1979_2023_yearly.png', dpi=500)
