from modelfunc import argusToFiredrakeMesh
import firedrake
import utilities as u


def setupMesh(meshFile, degree=2, meshOversample=None, savegmsh=False):
    """
    Read argus mesh file and return mesh alongw ith function spaces

    Parameters
    ----------
    meshFile : str
        argus meshfile name
    degree : int, optional
        degree of function spaces, by default 2

    Returns
    -------
    mesh
        firedrake mesh
    Q, V
        firedrake scalar and vectory functions
    """
    # Input the mesh
    maxOversample = 4  # Arbitrary could be increased
    mesh, opts = argusToFiredrakeMesh(meshFile, savegmsh=savegmsh)
    if meshOversample is not None:
        numLevels = meshOversample - 1
        if numLevels < 0 or numLevels > (maxOversample-1):
            u.myerror(f'meshOverample={meshOversample} but  0 < '
                      'meshOversample < 4')
        mesh = firedrake.MeshHierarchy(mesh, numLevels)[numLevels]
    # Create scalar and vector function spaces
    Q = firedrake.FunctionSpace(mesh, family='CG', degree=degree)
    V = firedrake.VectorFunctionSpace(mesh, family='CG', degree=degree)
    return mesh, Q, V, opts
