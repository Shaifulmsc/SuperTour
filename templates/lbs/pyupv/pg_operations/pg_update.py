# -*- coding: utf-8 -*-
'''
Created on 25 feb. 2017
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
joamona@cgf.upv.es
'''


import json
import transform_coords_ol_to_postgis

def pg_update(d_conn, tabla,pk_name,pk_value, registro, src='25830', as_json=True):
    #ejemplo de consulta: update d.pozos set (z_tapa, profundidad) = (21,2) where gid=5;
    dic_registro=json.loads(registro)
    
    claves=dic_registro.keys()
    
    hay_geom=False
    if 'coordinates' in claves:
        coords_geom=dic_registro['coordinates']
        coords_geom=transform_coords_ol_to_postgis.transform_coords_ol_to_postgis(coords_geom)
        tipo_geom=dic_registro['type'].upper()
        hay_geom=True
        del dic_registro['coordinates']
        del dic_registro['type']
    
    claves=dic_registro.keys()#updates the claves vector
    
    #now we have the diccionary only with data attributes, without id or gid, coordinates and type
    #and we have that data in local variables
    #we are ready to try update the record
    
    #we need a string with all the fields to update
    cadena_claves=''
    cadena_valores=''
    for clave in claves:
        cadena_claves=cadena_claves + ',' + clave
        cadena_valores=cadena_valores + ',' + '%s'
    cadena_claves=cadena_claves[1:]#elimitate the first charácter -->','  
    cadena_valores=cadena_valores[1:]#elimitate the first charácter -->','
    
    #cadena_claves contains: field1, field2, ....
    #cadena_valores contains: %s, %s, ....
    #the same number of fields than %s
    #now we form the query
    #example: update d.pozos set (z_tapa, profundidad) = (21,2) where gid=5;
    lista_valores=dic_registro.values()
    if not(hay_geom):
        cons= 'UPDATE {tabla} set ({cadena_claves})=({cadena_valores}) where {pk_name} = %s;'.format(tabla=tabla,cadena_claves=cadena_claves,cadena_valores=cadena_valores, pk_name=pk_name)
    else:
        cadena_claves=cadena_claves + ',geom'
        #example: ST_GeomFromText('POINT(-71.064544 42.28787)', 25830);
        if tipo_geom == 'POINT' or tipo_geom == 'LINESTRING':
            #It needs one parenthesis
            geometria=",ST_GeomFromText('{tipo_geom}({coords_geom})', {src})".format(tipo_geom=tipo_geom,src=src,coords_geom=coords_geom)
        else:
            #It needs two parenthesis
            geometria=",ST_GeomFromText('{tipo_geom}(({coords_geom}))', {src})".format(tipo_geom=tipo_geom,src=src,coords_geom=coords_geom)
            
        cadena_valores = cadena_valores + geometria
        cons= 'UPDATE {tabla} set ({cadena_claves})=({cadena_valores}) where {pk_name} = %s;'.format(tabla=tabla,cadena_claves=cadena_claves,cadena_valores=cadena_valores, pk_name=pk_name)
        #lista_valores.append(coords_geom)
    
    #it is necessary to append the pk_value to the list of values
    lista_valores.append(pk_value)
    cursor=d_conn['cursor']
    try:
        cursor.execute(cons,lista_valores)
        d_conn['conn'].commit()
    except Exception as e:
        if as_json:
            json_resp=json.dumps({"ok":False, 'mensaje':e.message})
        else:
            json_resp={"ok":False, 'mensaje':e.message}
        return json_resp
    if as_json:
        json_resp=json.dumps({"ok":True, 'mensaje':'Actualización realizada', 'tabla':tabla})
    else:
        json_resp={"ok":True, 'mensaje':'Actualización realizada', 'tabla':tabla}
    return json_resp

    