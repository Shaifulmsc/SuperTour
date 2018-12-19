# -*- coding: utf-8 -*-
'''
Created on 25 feb. 2017
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
joamona@cgf.upv.es
'''

import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

def pg_connect(database,user,password,host,port):
    """
    Connects with the database with the library psycopg2
    The credentials of the connection are imported from the file var_globales.py
    @return a dictionary wirh the connection and the cursor of the connection
        {'conn':conn, 'cursor':cursor}
    """
    #conexion
    conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
    cursor=conn.cursor()
    
    return {'conn':conn, 'cursor':cursor}