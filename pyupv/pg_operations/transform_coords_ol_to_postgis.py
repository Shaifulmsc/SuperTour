# -*- coding: utf-8 -*-
'''
Created on 25 feb. 2017
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
joamona@cgf.upv.es
'''


def transform_coords_ol_to_postgis(coords_geom):
    """
    Receives a string coordinate like 'x,y,x,y,x,y,....' from openlayers
    Returns a string like 'x y, x y, x y, ....'
    """
    lc=coords_geom.split(',')
    n=len(lc)
    sc=''
    for i in xrange(0,n,2):#starts in 0, stops in n, step 2
        #xrange(0,10,2)-->[0,2,4,6,8]
        x=lc[i]
        y=lc[i+1]
        sc=sc + ',' + x + ' ' + y
    return sc[1:]