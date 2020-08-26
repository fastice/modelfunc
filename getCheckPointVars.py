import firedrake
from utilities import myerror
import os


def getCheckPointVars(checkFile, varNames, Q, t=None):
    """ Read a variable from a firedrake checkpoint file

    Parameters
    ----------
    checkFile : str
        checkfile name sans .h5
    varNames : str or list of str
        Names of variables to extract
    Q : firedrake function space
        firedrake function space can be a vector space, V, but not mixed
    Returns
    -------
    myVars: dict
        {'myVar':}
    """
    # Ensure a list since a single str is allowed
    if type(varNames) is not list:
        varNames = [varNames]
    # open checkpoint
    myVars = {}
    if not os.path.exists(f'{checkFile}.h5'):
        myerror(f'getCheckPointVar: file {checkFile}.h5 does not exist')
    with firedrake.DumbCheckpoint(checkFile, mode=firedrake.FILE_READ) as chk:
        if t is not None:
            print(t)
            chk.set_timestep(t)
        for varName in varNames:
            myVar = firedrake.Function(Q, name=varName)
            chk.load(myVar, name=varName)
            myVars[varName] = myVar
    return myVars
