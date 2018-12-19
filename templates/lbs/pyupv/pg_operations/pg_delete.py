# -*- coding: utf-8 -*-
'''
Created on 25 feb. 2017
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
joamona@cgf.upv.es
'''

import json

def pg_delete(d_conn, tabla, pk_name, pk_value, as_json=True):
    """
    Deletes the rows of a table which math with pk_name=pk_value
    @type d_conn: dictionary 
    @param d_conn: is a dictionary key:value, where there have to be two keys: conn and
        cursor. The values of this keys have to be:
            conn: a psycopg2 connection
            cursor: the cursor of the psycop connection
    @type tabla: string
    @param tabla: table name where the selection will have place
    @type pk_name: string
    @param pk_name: name of a field used to the where to filter the rows. If no set all the reccords will be retrieved
    @type pk_value: string
    @param pk_value: value of the pk_name to be used in the where condition to filter the rows. If
        pk_name is set, then pk_value have to be also set
    @type as_json: boolean
    @param as_json: if true returns a json, else a dictionary with the same content 

    @return: a string json or a dictionary, depending in the as_json parameter value
        if all ok --> {"ok":True, 'mensaje':'Regisro borrado', 'tabla':tabla}
        if some fail --> {"ok":False, 'mensaje':e.message}
   """

    cond_where='where {pk_name}=%s'.format(pk_name=pk_name)
    cons= 'delete from ' + tabla + ' ' + cond_where
        #lista_valores.append(coords_geom)
    
    #it is necessary to append the pk_value to the list of values
    cursor=d_conn['cursor']
    try:
        cursor.execute(cons,[pk_value])
        d_conn['conn'].commit()
    except Exception as e:
        if as_json:
            json_resp=json.dumps({"ok":False, 'mensaje':e.message})
        else:
            json_resp={"ok":False, 'mensaje':e.message}
        return json_resp
    if as_json:
        json_resp=json.dumps({"ok":True, 'mensaje':'Regisro borrado', 'tabla':tabla})
    else:
        json_resp={"ok":True, 'mensaje':'Regisro borrado', 'tabla':tabla}
    return json_resp

