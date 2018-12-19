# -*- coding: utf-8 -*-
'''
Created on 25 feb. 2017
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
joamona@cgf.upv.es
'''

import json

def pg_select(d_conn, tabla,pk_name, pk_value,campos, as_json=True):
    '''
    Recovers rows from a table. One or all.
    
    campos is a dictionary key:value, where the values does not matter. This param
    is used to know the fields that must be asked to the database.
    
    If you want to retrieve the geometry as geojson, must to give the fields 'coordinates' and 'type'
    in the dictionary of the parameter 'campos'
    
    To retrieve all rows, do not specify pk_name and pk_value, or do not specify pk_value.
    If pk_values is gave, pk_name have to be gave too.
    
    To retrieve all rows of a table:
    url? 
    operacion=select&
    tabla=d.pozos&
    campos={"gid":"","descripcion":"","id_trabajo":"","z_tapa":"","profundidad":"","diametro":"","type":"","coordinates":""}
    
    To retrieve only one row:
    url? 
    operacion=select&
    tabla=d.pozos&
    pk_name=gid &            (name of a name field. Usualy gid or id)
    pk_value=8&               (value of the name field)
    campos={"gid":"","descripcion":"","id_trabajo":"","z_tapa":"","profundidad":"","diametro":"","type":"","coordinates":""}
    
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
    @type campos: string 
    @param campos: is a string which have inside a dictionary key:value, where the values does not matter. 
        This string ins converted into a dictionary: dic_campos=json.loads(campos)
        This param is used to know the fields that must be asked to the database. The fileds name to retrieve
        are the keys of this dictionary. 
    @type as_json: boolean
    @param as_json: if true returns a json, else a dictionary with the same content 
    @return: Return a json string or a dictionary, depending on the value as_json
        if ok --> {"ok":True, 'tabla': tabla, 'registros':lista_dict, 'mensaje': 'Se han recuperado {n} registros'.format(n=len(lista_dict)}
            lista_dict is a list with all records recovered. Each record is represented by a dictionary key: value
        if some fail --> {"ok":False, "mensaje": mensaje}
    '''
    dic_campos=json.loads(campos)
    
    has_geom=False 
    if 'coordinates' in dic_campos:
        #the form has the fields coordinates and type, but the table does not have that fields
        del dic_campos['coordinates']
        del dic_campos['type']
        has_geom=True
        
    claves=dic_campos.keys()
    
    if pk_value <>'':
        cond_where='where t.{pk_name}=%s'.format(pk_name=pk_name)
    else:
        cond_where=''
        
    
    #we need a string with all the fields: 'field1, field2, ...'
    cadena_claves=''
    for clave in claves:
        cadena_claves=cadena_claves + ',' + clave
    cadena_claves=cadena_claves[1:]#elimitate the first charácter -->','  
    
    if has_geom: #has to ask for the geometry
        cons='SELECT array_to_json(array_agg(registros)) FROM (select {cadena_claves}, st_asgeojson(geom) from {tabla} as t {cond_where} limit 100) as registros;'.format(cadena_claves=cadena_claves,tabla=tabla,cond_where=cond_where)      
    else:
        cons='SELECT array_to_json(array_agg(registros)) FROM (select {cadena_claves} from {tabla} as t {cond_where} limit 100) as registros;'.format(cadena_claves=cadena_claves,tabla=tabla,cond_where=cond_where)      

    cursor=d_conn['cursor']    
    try:
        if pk_name =='':
            cursor.execute(cons)
        else:
            cursor.execute(cons,[pk_value])
    except Exception as e:
        if as_json:
            json_resp=json.dumps({"ok":False, 'mensaje':e.message})
        else:
            json_resp={"ok":False, 'mensaje':e.message}
        return json_resp
    
    v=cursor.fetchall()

    if len(v) < 1 or v[0][0] is None:
        if pk_name =='':
            mensaje= 'No existen registros en la tabla {tabla}'.format(tabla=tabla)
        else:
            mensaje= 'No existe registro en la tabla {tabla} con el {pk_name}={pk_value}'.format(tabla=tabla, pk_name=pk_name,pk_value=pk_value)
        json_resp=json.dumps({"ok":False, "mensaje": mensaje})
        return json_resp
    js=v[0][0]#js is a list of reccords each reccord is a dictionary
              #[dict, dict2, ...]
              
    if isinstance(js, basestring):#I do not know why but ubuntu 16.04 returns directly a dict
        js=json.loads(js)         #but ubuntu 14.04 returns a string, then we need to convert it
                                  #into a dictionary
    
    #each dictioanry has the following content
        #{'field1':value1,'field2':value2, ....,'st_asgeojson': "['type':Point, 'coordinates': '[x,y]']"}
    #the st_asgeojson key has a geojson string as value
    #the geojson string has the 'type' and 'coordinates' fields
    #we need to delete the st_geojson key and add the 'type' and 'coodinates' fields
    #as simple fields. This is done in the following code:
    if has_geom:
        lista_dict=[]#the new list that will have the correct dictionary
        for fila in js:

            valores=fila
            str_geojson= valores['st_asgeojson']#retrieve the geojson string
            del valores['st_asgeojson']#deletes the st_geojson key
            dic_geojson=json.loads(str_geojson)#transform the geojson string into a dictionary
            valores['type']=dic_geojson['type']#adds the type to the valores dictionary
            valores['coordinates']=dic_geojson['coordinates']#adds the coordinates to the valores dictionary
            lista_dict.append(valores)
    else:
        lista_dict=js

    #lista_dict now has the following content:
        #[dict1, dict2, ....]
    #and each dict has the following content
        ##{'field1':value1,'field2':value2, ....,'type':'Point', 'coordinates': [x,y]}
    
    if as_json:
        json_resp=json.dumps({"ok":True, 'tabla': tabla, 'registros':lista_dict, 'mensaje': 'Se han recuperado {n} registros'.format(n=len(lista_dict))})
    else:
        json_resp={"ok":True, 'tabla': tabla, 'registros':lista_dict, 'mensaje': 'Se han recuperado {n} registros'.format(n=len(lista_dict))}
    #the table name is retourned to render the appropiate form int the javascript function 
    #the table name includes the schema name: d.pozos, d.tubosaneamiento, ...
    return json_resp