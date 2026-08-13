#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 10:23:27 2020

@author: ian
"""
import rasterio
import icepack


def getRateFactor(rateFile, Q, Ainput=False):
    """
    Read rate factor as A or B and  return as A
    Parameters
    ----------
    rateFile : str
        File with rate factor data
    Q : firedrake function space
        function space
    Ainput : bool, optional
      Set True to treat rateFile as A instead of B. The default is False.
        
    Returns
    -------
    A : firedrake function
        A Glenns flow law parameter
    """
    print(rateFile)
    if Ainput:
        Aras = rasterio.open(rateFile)
        A = icepack.interpolate(Aras, Q)
    else:    
        Bras = rasterio.open(rateFile)
        B = icepack.interpolate(Bras, Q)
        convFactor = 1e-6 * (86400*365.25)**(-1./3.)
        A = icepack.interpolate((B * convFactor)**-3, Q)
        
    return A

