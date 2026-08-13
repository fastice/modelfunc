import firedrake
import icepack
from icepack.constants import weertman_sliding_law as m
from icepack.constants import ice_density as rhoI
from firedrake import grad
from icepack.constants import gravity as g
from modelfunc import myerror, printExtremes


def taperedViscosityIS(velocity, thickness, fluidity, theta,
                       groundedSmooth, floatingSmooth, verbose=False):
    '''
    Used tapered grounding and floating masks to avoid discontinuity in A at
    the GL. This is the new version for the Icestream programs (not PIG)

    Parameters
    ----------
    velocity : firedrake
        Velocity.
    thickness : firedrake
        THickness.
    fluidity : firedrake
        Fluidity parameter (A) for grounded regions.
    theta : firedrake
        Inverted ln(A) for ice shelf.
    groundedSmooth : firedrake
        Tapered grounding line mask.
    floatingSmooth : firedrake
        Tapered floating ice mask.
    Returns
    -------
    viscosity : TYPE
        Viscosity to use in the model.
    '''
    # velocity, thickness, theta, floatingSmooth, groundedSmooth, fluidity = \
    #    map(kwargs.get, ("velocity", "thickness", "theta",
    #                     "floatingSmooth", "groundedSmooth", "fluidity"))
    if verbose:
        printExtremes(theta=theta)
    Atmp = groundedSmooth * fluidity + floatingSmooth * firedrake.exp(theta)
    return \
        icepack.models.viscosity.viscosity_depth_averaged(velocity=velocity,
                                                          thickness=thickness,
                                                          fluidity=Atmp)

def viscosityTheta(u, h, grounded, floating, A, theta):
    """Combine existing A on grounded ice with theta^2 from floating ice.
    Parameters
    ----------
    u : firedrake function
        modelled velocity
    h : firedrake function
        model thickness
    grounded : firedrake function
        Mask with 1s for grounded 0 for floating.
    floating : firedrake function
        Mask with 1s for floating 0 for grounded.
    A : firedrake function
        A for grounded areas
    theta : firedrake function
        theta for A on floating ice as theta^2
    Returns
    -------
    viscosityFunction function
        Viscosity funciton for model
    """
    # A = grounded * A + floating * theta**2
    A0 = grounded * A + floating * firedrake.exp(theta)
    # A 0 = firedrake.max_value(firedrake.min_value(A0, 1.), 100.)
    return icepack.models.viscosity.viscosity_depth_averaged(velocity=u,
                                                             thickness=h,
                                                             fluidity=A0)


def weertmanFriction(velocity, grounded, beta, uThresh):
    """Friction coefficient for weertman sliding law
    Parameters
    ----------
    velocity : firedrake function
        modelled velocity
    grounded : firedrake function
        Mask with 1s for grounded 0 for floating.
    beta : firedrake function
        Beta for friction model with C=beta^2

    Returns
    -------
    frictionFunction function
        Bed friction model
    """
    C = grounded * beta**2
    return icepack.models.friction.bed_friction(velocity=velocity, friction=C)


def getFrictionLaw(s, h, uObs, Q, V, frictionLaw, uThresh):
    """Get friction law for for ln beta parameterizations.
    Parameters
    ----------
    s : firedrake function
        model surface elevation
    h : firedrake function
        model thickness
    speed : firedrake function
        modelled speed
    V : firedrake vector function space
        vector function space
    Q : firedrake function space
        scalar function space
    grounded : firedrake function
        Mask with 1s for grounded 0 for floating.
    frictionLaw : str
        'weertman' or 'schoof'
    uThresh : float
        threshold speed for schoof law
    """
    m = 3
    speedObs = icepack.interpolate(firedrake.sqrt(firedrake.inner(uObs,
                                                                  uObs)), Q)
    tauD = firedrake.project(-rhoI * g * h * grad(s), V)
    #
    stress = firedrake.sqrt(firedrake.inner(tauD, tauD))
    print('stress', firedrake.assemble(stress * firedrake.dx))
    print("Speed min, max:", speedObs.dat.data_ro.min(),
          speedObs.dat.data_ro.max())
    fraction = firedrake.Constant(0.95)
    U = firedrake.max_value(speedObs, 1)
    # Schoofie
    if frictionLaw == 'schoof':
        mExp = 1/m + 1
        U0 = firedrake.Constant(uThresh)
        expr = (fraction * stress / U**(1 / m)) * \
            (m/(m+1)) * (U0**mExp + U**mExp)**(1/(m+1))
        C_0 = firedrake.Function(Q).interpolate(expr)
        # Create RCF log friction

        def logFriction(**kwargs):
            u, beta, grounded = map(kwargs.get,
                                    ("velocity", "beta", "grounded"))
            uMag = firedrake.sqrt(firedrake.inner(u, u))
            friction = grounded * C_0 * firedrake.exp(beta) * \
                ((U0**mExp + uMag**mExp)**(m/(m + 1.)) - U0)
            return friction
    # Weertman
    elif frictionLaw == 'weertman':
        expr = fraction * stress / U**(1 / m)
        C_0 = firedrake.Function(Q).interpolate(expr)

        # create Weertman version of logFriction
        def logFriction(**kwargs):
            u, beta, grounded = map(kwargs.get,
                                    ("velocity", "beta", "grounded"))
            u_0 = firedrake.Constant(1)
            return grounded * m / (m + 1) * C_0 * firedrake.exp(beta) * \
                firedrake.sqrt(firedrake.inner(u, u) + u_0**2) ** (1 / m + 1)
    else:
        myerror(f"Invalid friction model: {frictionLaw}")
    return logFriction


# Note m is a global variable
def schoofFriction(velocity, grounded, beta, uThresh):
    """Friction coefficient for regularized coloumb (Schoof) sliding law
    Parameters
    ----------
    velocity : firedrake function
        modelled velocity
    grounded : firedrake function
        Mask with 1s for grounded 0 for floating.
    beta : firedrake function
        Beta for friction model with C=beta^2
    uThresh : float
        Velocity transition for sliding law
    Returns
    -------
    frictionFunction function
        Bed friction model
    """
    C = grounded * beta**2
    mExp = (1./m + 1.)
    U = firedrake.sqrt(firedrake.inner(velocity, velocity))
    return C * ((uThresh**mExp + U**mExp)**(m/(m+1.)) - uThresh)
