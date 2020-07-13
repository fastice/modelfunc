import yaml
from utilities import myerror
import firedrake

def inputMeltParams(meltParams):
    """Read parameters for melt models
    Parameters
    ----------
    meltParams : str
        yaml file with melt params for various models
    """
    with open(meltParams,'r') as fp:
        meltParams = yaml.load(fp, Loader=yaml.FullLoader)
    return meltParams


def piecewiseWithDepth(h, floating, meltParams):
    """[summary]

    Parameters
    ----------
    h : firedrake function
        ice thickness
    s : firedrake function
        surface elevation
    meltParams : dict
        parameters for melt function
    Returns
    -------
    firedrake function
        melt rates
    """
    try:
        meltModel = meltParams['piecewiseWithDepth']
    except Exception:
        myerror(f'Params for melt - piecewiseWithDepth -  not in {meltParams}')
    # compute depth
    melt = firedrake.Constant(0)
    for i in range(1, meltModel['numberOfPolynomials'] + 1):
        poly = meltModel[f'poly{i}']
        tmpMelt = firedrake.Constant(poly['coeff'][0])
        for j in range(1, poly['deg'] + 1):
            tmpMelt = tmpMelt + poly['coeff'][j] * h**j
        melt = melt + tmpMelt * (h > poly['min']) * (h < poly['max'])
        melt = melt * floating
    return melt