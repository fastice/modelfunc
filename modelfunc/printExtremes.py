#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 21 08:18:10 2025

@author: ian
"""


def printExtremes(**kwargs):
    ''' Print min/max of firedrake functions to flag bad inputs'''
    print('Min/Max of input values')
    print(''.join(['-']*40))
    for arg in kwargs:
        print(arg, kwargs[arg].dat.data_ro.min(),
              kwargs[arg].dat.data_ro.max())
    print(''.join(['-']*40))
