import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.mpl.ticker as cticker
import netCDF4 as nc
import matplotlib.path as mpath
import os
from scipy.interpolate import griddata
import cmaps
import matplotlib.ticker as mticker
from cartopy.util import add_cyclic_point
from matplotlib import colors
from scipy.stats import pearsonr
from scipy import signal
import pandas as pd
import numpy.ma as ma
import datetime
import time


def z_masked_overlap(axe, X, Y, Z, source_projection=None):
    """
    for data in projection axe.projection
    find and mask the overlaps (more 1/2 the axe.projection range)

    X, Y either the coordinates in axe.projection or longitudes latitudes
    Z the data
    operation one of 'pcorlor', 'pcolormesh', 'countour', 'countourf'

    if source_projection is a geodetic CRS data is in geodetic coordinates
    and should first be projected in axe.projection

    X, Y are 2D same dimension as Z for contour and contourf
    same dimension as Z or with an extra row and column for pcolor
    and pcolormesh

    return ptx, pty, Z
    """
    if not hasattr(axe, 'projection'):
        return Z
    if not isinstance(axe.projection, ccrs.Projection):
        return Z

    if len(X.shape) != 2 or len(Y.shape) != 2:
        return Z

    if (source_projection is not None and
            isinstance(source_projection, ccrs.Geodetic)):
        transformed_pts = axe.projection.transform_points(
            source_projection, X, Y)
        ptx, pty = transformed_pts[..., 0], transformed_pts[..., 1]
    else:
        ptx, pty = X, Y

    with np.errstate(invalid='ignore'):
        # diagonals have one less row and one less columns
        diagonal0_lengths = np.hypot(
            ptx[1:, 1:] - ptx[:-1, :-1],
            pty[1:, 1:] - pty[:-1, :-1]
        )
        diagonal1_lengths = np.hypot(
            ptx[1:, :-1] - ptx[:-1, 1:],
            pty[1:, :-1] - pty[:-1, 1:]
        )
        to_mask = (
            (diagonal0_lengths > (
                abs(axe.projection.x_limits[1]
                    - axe.projection.x_limits[0])) / 2) |
            np.isnan(diagonal0_lengths) |
            (diagonal1_lengths > (
                abs(axe.projection.x_limits[1]
                    - axe.projection.x_limits[0])) / 2) |
            np.isnan(diagonal1_lengths)
        )

        # TODO check if we need to do something about surrounding vertices

        # add one extra colum and row for contour and contourf
        if (to_mask.shape[0] == Z.shape[0] - 1 and
                to_mask.shape[1] == Z.shape[1] - 1):
            to_mask_extended = np.zeros(Z.shape, dtype=bool)
            to_mask_extended[:-1, :-1] = to_mask
            to_mask_extended[-1, :] = to_mask_extended[-2, :]
            to_mask_extended[:, -1] = to_mask_extended[:, -2]
            to_mask = to_mask_extended
        if np.any(to_mask):

            Z_mask = getattr(Z, 'mask', None)
            to_mask = to_mask if Z_mask is None else to_mask | Z_mask

            Z = ma.masked_where(to_mask, Z)

        return ptx, pty, Z


def date_name_shift(x):
    publishtime = x
    array = time.strptime(publishtime, u"%Y-%m-%d")
    publishTime = time.strftime("%Y_%m_%d", array)
    return publishTime


# read the file
thickness_file = nc.Dataset(r'data/thickness/2021.nc', 'r')
thickness = thickness_file.variables['thickness'][:].data

# set the date
start_date = datetime.date(2021, 1, 1)
end_date = datetime.date(2021, 12, 31)
current_date = start_date
date = []

while current_date <= end_date:
    date.append(current_date)
    current_date += datetime.timedelta(days=1)
date_new = [date_name_shift(str(i)) for i in date]

for day in range(365):
    # read the data
    thickness_day = thickness[day, :, :]
    lon = thickness_file.variables['longitude'][:].data
    lat = thickness_file.variables['latitude'][:].data

    projection = ccrs.NorthPolarStereo(central_longitude=0, globe=None)
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, dpi=600)

    # map set
    ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=False, linewidth=0.35, color='k', alpha=1, linestyle=':', zorder=11,
                 xlocs=np.arange(-180, 180, 30), ylocs=[70, 75, 80, 85])
    ax.coastlines(lw=0.5, alpha=1)
    ax.add_feature(cfeature.LAND, zorder=1, facecolor=cfeature.COLORS['land'])
    ax.set_extent([-180, 180, 66.5, 90], ccrs.PlateCarree())
    theta = np.linspace(0, 2*np.pi, 100)
    center, radius = [0.5, 0.5], 0.5
    verts = np.vstack([np.sin(theta), np.cos(theta)]).T
    circle = mpath.Path(verts * radius + center)
    ax.set_boundary(circle, transform=ax.transAxes)

    X, Y, masked_MDT = z_masked_overlap(ax, lon, lat, thickness_day, source_projection=ccrs.Geodetic())
    c = ax.contourf(X, Y, masked_MDT, 30, cmap=cmaps.WhiteBlueGreenYellowRed, levels=np.arange(0, 5, 0.2),
                    zorder=0,)
    plt.title(str(date[day]), size=14)
    cb = plt.colorbar(c, orientation='vertical', fraction=0.05, extend='both')
    cb.ax.set_title('m', size=10)
    plt.savefig('picture/thickness/thickness_' + str(date_new[day]) + '.png', bbox_inches='tight', dpi=500)
