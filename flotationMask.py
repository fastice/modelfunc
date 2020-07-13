import firedrake
from icepack.constants import ice_density as rhoI, water_density as rhoW


def flotationMask(s, zF, Q, rhoI=rhoI, rhoW=rhoW):
    """Using flotation height, create masks for floating and grounded ice.

    Parameters
    ----------
    zF firedrake interp function
        Flotation height (m)
    Q : firedrake function space
        function space
    rhoI : [type], optional
        [description], by default rhoI
    rhoW : [type], optional
        [description], by default rhoW
    Returns
    -------
    floating firedrake interp function
         ice shelf mask 1 floating, 0 grounded
    grounded firedrake interp function
        Grounded mask 1 grounded, 0 floating
    """
    floating = firedrake.interpolate(s <= zF, Q)
    grounded = firedrake.interpolate(s > zF, Q)
    return floating, grounded
