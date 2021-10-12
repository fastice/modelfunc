import yaml
from modelfunc.myerror import myerror
import firedrake
import icepack
from modelfunc.firedrakeSmooth import firedrakeSmooth
import os


def inputMeltParams(meltParams):
    """Read parameters for melt models
    Parameters
    ----------
    meltParams : str
        yaml file with melt params for various models
    """
    if not os.path.exists(meltParams):
        myerror(f'inputMeltParams: meltParams file ({meltParams}) not found.')
    with open(meltParams, 'r') as fp:
        meltParams = yaml.load(fp, Loader=yaml.FullLoader)
    return meltParams


def piecewiseWithDepth(h, floating, meltParams, Q, *argv, returnScale=False,
                       **kwargs):
    """ Melt function that is described piecewise by set of polynomials
    Melt is in units of m/yr w.e.
    Parameters
    ----------
    h : firedrake function
        ice thickness
    floating : firedrake function
        floating mask
    meltParams : dict
        parameters for melt function
    Q firedrake function space
    returnScale return scale factor too (optional)
    Returns
    -------
    firedrake function
        melt rates
    """
    # compute depth
    melt = firedrake.Constant(0)
    for i in range(1, meltParams['numberOfPolynomials'] + 1):
        poly = meltParams[f'poly{i}']
        tmpMelt = firedrake.Constant(poly['coeff'][0])
        for j in range(1, poly['deg'] + 1):
            tmpMelt = tmpMelt + poly['coeff'][j] * h**j
        # Apply melt to all shelf ice (ice > 30 m)
        melt = melt + tmpMelt * \
            (h > max(poly['min'], 30.1)) * (h < poly['max'])
    # Smooth result
    alpha = 4000  # Default
    if 'alpha' in meltParams:
        alpha = meltParams['alpha']
    #
    # if filterWithFloatMask apply float mask before filter, which will shift
    # melt distribution up in the column. If filter applied afterwards, it
    # will be concentrated nearer the GL.
    filterWithFloatMask = False
    if 'filterWithFloatMask' in meltParams:
        filterWithFloatMask = meltParams['filterWithFloatMask']
    if filterWithFloatMask:
        # Changed to avoid petsc memory issue on store
        # melt1 = icepack.interpolate(melt * floating, Q)
        melt1 = icepack.interpolate(melt, Q)
        melt1 = icepack.interpolate(floating * melt1, Q)
    else:
        melt1 = icepack.interpolate(melt, Q)
    melt1 = firedrakeSmooth(melt1, alpha=alpha)
    # 'totalMelt' given renormalize melt to produce this value
    if 'totalMelt' in meltParams.keys():
        trend = 0.
        if 'trend' in kwargs.keys():
            trend = kwargs['trend']
        intMelt = firedrake.assemble(melt1 * floating * firedrake.dx)
        total = float(meltParams['totalMelt']) + trend
        scale = firedrake.Constant(-1.0 * total/float(intMelt))
    else:
        scale = firedrake.Constant(1.)
    #
    melt = icepack.interpolate(melt1 * scale * floating, Q)
    if returnScale:
        return melt, scale
    return melt


def divMelt(h, floating, meltParams, u, Q):
    """ Melt function that is a scaled version of the flux divergence
    h : firedrake function
        ice thickness
    u : firedrake vector function
        surface elevation
    floating : firedrake function
        floating mask
    V : firedrake vector space
        vector space for velocity
    meltParams : dict
        parameters for melt function
    Returns
    -------
    firedrake function
        melt rates
    """
    flux = u * h
    fluxDiv = icepack.interpolate(firedrake.div(flux), Q)
    fluxDivS = firedrakeSmooth(fluxDiv, alpha=8000)
    fluxDivS = firedrake.min_value(fluxDivS * floating *
                                   meltParams['meltMask'], 0)
    intFluxDiv = firedrake.assemble(fluxDivS * firedrake.dx)
    scale = -1.0 * float(meltParams['intMelt']) / float(intFluxDiv)
    scale = firedrake.Constant(scale)
    melt = icepack.interpolate(firedrake.min_value(fluxDivS * scale,
                                                   meltParams['maxMelt']), Q)

    return melt
