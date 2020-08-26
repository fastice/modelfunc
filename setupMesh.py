from modelfunc import argusToFiredrakeMesh
import firedrake


def setupMesh(meshFile, degree=2):
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
    mesh, opts = argusToFiredrakeMesh(meshFile)
    # Create scalar and vector function spaces
    Q = firedrake.FunctionSpace(mesh, family='CG', degree=degree)
    V = firedrake.VectorFunctionSpace(mesh, family='CG', degree=degree)
    return mesh, Q, V, opts
