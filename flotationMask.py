from icepack.constants import ice_density as rhoI, water_density as rhoW
from modelfunc.firedrakeSmooth import firedrakeSmooth
import icepack


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
    # smooth to avoid isolated points dipping below flotation.
    zAbove = firedrakeSmooth(icepack.interpolate(s - zF, Q), alpha=100)
    floating = icepack.interpolate(zAbove < 0, Q)
    grounded = icepack.interpolate(zAbove > 0, Q)
    return floating, grounded
