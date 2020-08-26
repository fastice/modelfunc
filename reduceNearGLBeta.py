import icepack
import firedrake


def reduceNearGLBeta(s, sOrig, zF, grounded, Q, thresh, limit=False):
    """Compute beta reduction in area near grounding line where the height
    above floation is less than thresh.

    Parameters
    ----------
    s : firedrake function
        Current surface.
    sOrig : firedrake function
        Original surface.
    zF : firedrake function
        Flotation height.
    grounded : firedrake function
        grounde mask
    Q : firedrake function space
        scaler function space for model
    thresh : float
        Threshold to determine where to reduce beta (zAbove < thresh)
    """
    # compute original height above flotation for grounded region
    sAboveOrig = (sOrig - zF) * grounded
    # avoid negative/zero values
    sAboveOrig = firedrake.max_value(sAboveOrig, 0.001)
    # Current height above flotation with negative values zeroed out.
    sAbove = firedrake.max_value((s - zF) * grounded, 0)
    # mask so only areas less than thresh but grounded
    sMask = (sAbove <= thresh) * grounded
    # Inverse mask
    sMaskInv = sMask < 1
    # scale = fraction of of original height above flotation
    scaleBeta = sAbove / \
        firedrake.max_value(firedrake.min_value(thresh, sAboveOrig), 5)
    if limit:
        scaleBeta = firedrake.min_value(3, scaleBeta)
    scaleBeta = scaleBeta * sMask + sMaskInv
    # scaleBeta = icepack.interpolate(firedrake.min_value(scaleBeta,1.),Q)
    # sqrt so tau = scale * beta^2
    scaleBeta = icepack.interpolate(firedrake.sqrt(scaleBeta) * grounded, Q)
    return scaleBeta
