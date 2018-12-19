# -*- coding: utf-8 -*-
'''
Created on 25 feb. 2017
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
joamona@cgf.upv.es
'''


from dweb import dweb
import json
import transform_coords_ol_to_postgis

def pg_insert(d_conn, tabla,pk_name,registro, src='25830', as_json=True):
    """
    Insert a new row into a table. The table can have a column of geometry
    @type d_conn: dictionary 
    @param d_conn: is a dictionary key:value, where there have to be two keys: conn and
        cursor. The values of this keys have to be:
            conn: a psycopg2 connection
            cursor: the cursor of the psycop connection
    @type tabla: string
    @param tabla: table name where the selection will have place
    @type pk_name: string
    @param pk_name: name of the primary key of the table. This field have to be a serial.
        this name field can to be in the registro parameter. In that case will be deleted before
        to send the insert to the database.
    @type registro: string 
    @param registro: is a string which have inside a dictionary key:value. 
        This string ins converted into a dictionary: dic_campos=json.loads(campos)
        Between the fields of the dictionary have to be the pk_name parameter, in
        order to be deleted and no send it to the database in the insert sentence. That is done
        because this field is serial y have to be calculated by the database. The value
        of the pk_name field can not be specified by the user.
        If the table has geometry column, two key-values pairs have to be founded in the
        dictionary:
            coordinates: 'x,y,x,y,.....x,y'
            type: Point, LineString or Polygon
        The table geometry field name has to be 'geom'
    @type as_json: boolean
    @param as_json: if true returns a json, else a dictionary with the same content 

    @return: a string json, or dictionary, depending on the as_json value
        If all ok  --> {"ok":True, 'mensaje':'Regisro insertado', pk_name:pk_value, 'tabla':tabla}
        If some fail: --> {"ok":False, 'mensaje':e.message}
    """
    dic_registro=json.loads(registro)
    pk=dic_registro.get(pk_name,'')
    if pk<>'':
        del dic_registro[pk_name]#the primary key must be a serial
    
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
        cons= 'INSERT INTO {tabla} ({cadena_claves}) VALUES ({cadena_valores}) returning {pk_name};'.format(tabla=tabla,cadena_claves=cadena_claves,cadena_valores=cadena_valores, pk_name=pk_name)
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
        cons= 'INSERT INTO {tabla} ({cadena_claves}) VALUES ({cadena_valores}) returning {pk_name};'.format(tabla=tabla,cadena_claves=cadena_claves,cadena_valores=cadena_valores, pk_name=pk_name)
        #lista_valores.append(coords_geom)
    
    #it is necessary to append the pk_value to the list of values
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
    l=cursor.fetchall()#gracias al returnig se puede saber el gid o el id del nuevo regitro
    pk_value=l[0][0]
    if as_json:
        json_resp=json.dumps({"ok":True, 'mensaje':'Regisro insertado', pk_name:pk_value, 'tabla':tabla})
    else:
        json_resp={"ok":True, 'mensaje':'Regisro insertado', pk_name:pk_value, 'tabla':tabla}        
    return json_resp

