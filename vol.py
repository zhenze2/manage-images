import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import netCDF4 as nc
import dateutil.parser
import datetime
import gzip
import shutil

# read the data
ice_vol_raw = gzip.open('data/vol/PIOMAS.vol.daily.1979.2024.Current.v2.1.dat.gz', 'rb')
ice_vol = open('data/vol/ice_vol.dat', 'wb')
shutil.copyfileobj(ice_vol_raw, ice_vol)
ice_vol = pd.read_table('data/vol/ice_vol.dat', sep='\s+')
ice_vol = ice_vol.to_numpy()
ice_vol = np.delete(ice_vol, range(16425, 16485), 0)
ice_vol = ice_vol.reshape((45, 365, 3))

# plot
start_date = datetime.date(2021, 1, 1)
date_strings = [(start_date + datetime.timedelta(days=i)).strftime('%m-%d') for i in range(365)]
day_sequence = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
month = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
plt.plot(range(365), ice_vol[42, :, 2], linewidth=2.0)
plt.xticks(day_sequence, month, fontsize=12, rotation=45)
plt.yticks(range(2, 24, 4), fontsize=12)
plt.xlabel('Month', fontsize=14)
plt.ylabel('Sea Ice Volume/10\N{SUPERSCRIPT THREE} km\N{SUPERSCRIPT THREE}', fontsize=14)
plt.xlim(0, 365)
plt.title('2021', fontsize=14)
plt.grid(True, linestyle='--', alpha=0.5, linewidth=0.5)
plt.savefig('picture/vol/' + '2021' + '.png', dpi=500)
