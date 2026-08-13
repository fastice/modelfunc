import firedrake
from firedrake import inner
import icepack
import rasterio
import xarray
import os
from utilities import myerror
import numpy as np

def getModelVelocity(baseName, Q, V, minSigma=5, maxSigma=100):
    """Read in a tiff velocity data set and return
    firedrake interpolate functions .

    Parameters
    ----------
    baseName : str
        baseName should be of the form pattern.*.abc or pattern
        The wildcard (*) will be filled with the suffixes (vx, vy.)
        e.g.,pattern.vx.abc.tif, pattern.vy.abc.tif.
    Q : firedrake function space
        function space
    V : firedrake vector space
        vector space
    Returns
    -------
    uObs firedrake interp function on V
        velocity (m/yr)
    speed firedrake interp function on Q
        speed in (m)
    sigmaX firedrake interp function on Q
        vx error (m)
    sigmaY firedrake interp function on Q
        vy error (m)
    """
    # suffixes for products used
   
    rasters = {}
    #
    # Nc case for antarctic measures
    if '.nc' in baseName:
        print('reading netcdf')
        velData = xarray.open_dataset(baseName)
        suffixes = {'VX': 'vx', 'VY': 'vy', 'ERRX': 'ex', 'ERRY': 'ey'}
        for suffix in suffixes:
            rasters[suffixes[suffix]] = velData[suffix]
    # tiff case
    else:
        # prep baseName - baseName.*.xyz.tif or baseName.*
        if '*' not in baseName:
            baseName += '.*'
        if '.tif' not in baseName:
            baseName += '.tif'
    # read data
        suffixes = ['vx', 'vy', 'ex', 'ey']
        for suffix in suffixes:
            myBand = baseName.replace('*', suffix)
            # print(myBand)
            if not os.path.exists(myBand):
                myerror(f'Velocity/error file - {myBand} - does not exist')
            rasters[suffix] = rasterio.open(myBand, 'r')   
    # Firedrake interpolators
    uObs = icepack.interpolate((rasters['vx'], rasters['vy']), V)
    # force error to be at least 1 to avoid 0 or negatives.
    sigmaX = icepack.interpolate(rasters['ex'], Q)
    sigmaX.dat.data[np.isnan(sigmaX.dat.data)] = maxSigma
    sigmaX = icepack.interpolate(firedrake.max_value(sigmaX, minSigma), Q)
    sigmaX = icepack.interpolate(firedrake.min_value(sigmaX, maxSigma), Q)
    sigmaY = icepack.interpolate(rasters['ey'], Q)
    sigmaY.dat.data[np.isnan(sigmaY.dat.data)] = maxSigma
    sigmaY = icepack.interpolate(firedrake.max_value(sigmaY, minSigma), Q)
    sigmaY = icepack.interpolate(firedrake.min_value(sigmaY, maxSigma), Q)
    speed = icepack.interpolate(firedrake.sqrt(inner(uObs, uObs)), Q)
    # return results
    return uObs, speed, sigmaX, sigmaY
