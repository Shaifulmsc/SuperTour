# -*- coding: utf-8 -*-
'''
Created on 16 feb. 2018
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
joamona@cgf.upv.es
'''
import psycopg2
import psycopg2.extensions

import json

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

def pgInsert2(d_conn, nom_tabla, d_str, str_fields_returning=None):
    str_field_names=d_str['str_field_names']
    list_field_values=d_str['list_field_values']
    str_s_values=d_str['str_s_values']
    r=pg_insert2(d_conn, nom_tabla, str_field_names,list_field_values,str_s_values, str_fields_returning)
    return r
 
def pg_insert2(d_conn, nom_tabla, str_field_names, list_field_values, str_s_values, str_fields_returning=None):
    """
    The queries ,where there are field values, are generated with the same system, using strings, 
    but you NEVER have to specify the values inside the string. 
    You have to put '%s' instead the real field value. 
    The field values are specified in a vector as a second parameter of the execute function
    
    returns:
        if str_fields_returning is None, returns None
        if str_fields_returning is 'gid, date' returns a list with a tuple wirth the gid and date
            gid and date have to be fields of the table.
            This is used to know the gid of the new row inserted
    
    
    p1='POLYGON((727844 4373183,727896 4373187,727893 4373028,727873 4373018,727858 4372987,727796 4372988,727782 4373008,727844 4373183, 727844 4373183))'   
    p2='POLYGON((727988 4373188,728054 4373192,728051 4373093,727983 4373093,727988 4373188))'

    nom_tabla='d.buildings'
    str_field_names='descripcion, geom'
    str_s_values='%s,st_geometryfromtext(%s,25830)'
    
    list_field_values=['First description',p1]
    pg_insert2(d_conn, nom_tabla, str_field_names, list_field_values,str_s_values)
    
    list_field_values=['Second description',p2]
    pg_insert2(d_conn, nom_tabla, str_field_names, list_field_values,str_s_values)
    
    
    #THIS EXAMPLE TRANSFORM THE OpenLayers COORDENATES STYLE TO POSTGIS STYLE
    
    #add to python_path variable the folder /home/desweb/www/apps/desweb
    #so my_python_libs is importable
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(BASE_DIR)


    p3_ol='727988,4373188,728054,4373192,728051,4373093,727983,4373093,727988,4373188'
    print 'original: {0}'.format(p3_ol)
    coords_p3=transform_coords_ol_to_postgis.transform_coords_ol_to_postgis(coords_geom=p3_ol)
    p3 = 'POLYGON(({coords_p3}))'.format(coords_p3=coords_p3)
    print 'Transformado: {0}'.format(p3)
    
    nom_tabla='d.buildings'
    string_fields_to_set='descripcion, geom'
    
    list_field_values=['Third description',p3]
    pg_insert2(d_conn, nom_tabla, str_field_names, list_field_values,str_s_values)
    
    The results of the examples are:
        Inserting polygon
        insert into d.buildings (descripcion, geom) values (%s,st_geometryfromtext(%s,25830))
        Inserting polygon
        insert into d.buildings (descripcion, geom) values (%s,st_geometryfromtext(%s,25830))
        original: 727988,4373188,728054,4373192,728051,4373093,727983,4373093,727988,4373188
        Transformado: POLYGON((727988 4373188,728054 4373192,728051 4373093,727983 4373093,727988 4373188))
        Inserting polygon
        insert into d.buildings (descripcion, geom) values (%s,st_geometryfromtext(%s,25830))
    """
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    #cons_ins='insert into {0} ({1}) values (%s,st_geometryfromtext(%s,25830))'.format(nom_tabla, string_fields_to_set)
    cons_ins='insert into {0} ({1}) values ({2})'.format(nom_tabla, str_field_names, str_s_values)
    
    if str_fields_returning <> None:
        cons_ins =cons_ins + ' returning ' + str_fields_returning
    print 'Inserting'
    print cons_ins
    cursor.execute(cons_ins,list_field_values)
    conn.commit()
    if str_fields_returning <> None:
        returning=cursor.fetchall()
        return returning

def pgUpdate2(d_conn, table_name, d_str, cond_where=None, list_values_cond_where=None):
    str_field_names=d_str['str_field_names']
    list_field_values=d_str['list_field_values']
    str_s_values=d_str['str_s_values']
    r=pg_update2(d_conn, table_name, str_field_names, str_s_values, list_field_values, cond_where, list_values_cond_where)
    return r


def pg_update2(d_conn, table_name, str_field_names, str_s_values, list_field_values, cond_where=None, list_values_cond_where=None):
    """
    Updates any table. Example of use:
    Returns the number of updated rows
    
    #update only the rows which gid > 5. With geometry
    p1='POLYGON((727844 4373183,727896 4373187,727893 4373028,727873 4373018,727858 4372987,727796 4372988,727782 4373008,727844 4373183, 727844 4373183))'   
    table_name='d.buildings'
    str_field_names='area, descripcion, geom'
    list_field_values=[300,'Nueva descripcion3',p1]
    str_s_values='%s,%s,st_geometryfromtext(%s,25830)'
    cond_where='where gid > %s'
    list_values_cond_where=[5]
    pg_update2(d_conn, table_name, str_field_names, str_s_values, list_field_values,cond_where,list_values_cond_where)
    
    #The executed select in this example is:
    #update d.buildings 
    #    set (area, descripcion, geom) = (%s,%s,st_geometryfromtext(%s,25830)) 
    #    where gid > %s

    #Retuns: true  
    
    #Other examples of use:
        #update all rows. Without geometry
    table_name='d.buildings'
    str_field_names='area, descripcion'
    list_field_values=[100,'Nueva descripcion']
    str_s_values='%s,%s'
    pg_update2(d_conn, table_name, str_field_names, str_s_values, list_field_values)
    
    #update only the rows which gid < 4. Without geometry
    table_name='d.buildings'
    str_field_names='area, descripcion'
    list_field_values=[200,'Nueva descripcion2']
    str_s_values='%s,%s'
    cond_where='where gid < %s'
    list_values_cond_where=[4]
    pg_update2(d_conn, table_name, str_field_names, str_s_values, list_field_values,cond_where,list_values_cond_where)
 
    The results are:
    Query: update d.buildings set (area, descripcion, geom) = (%s,%s,st_geometryfromtext(%s,25830)) where gid > %s
    Query: update d.buildings set (area, descripcion) = (%s,%s)
    Query: update d.buildings set (area, descripcion) = (%s,%s) where gid < %s

    """
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    cons='update {table_name} set ({str_field_names}) = ({str_s_values})'.format(table_name=table_name,str_field_names=str_field_names,str_s_values=str_s_values)
    if cond_where <> None:
        cons += ' ' + cond_where
        print 'Query: ' + cons
        cursor.execute(cons,list_field_values + list_values_cond_where)
    else:
        print 'Query: ' + cons
        cursor.execute(cons,list_field_values)
    conn.commit()
    return cursor.rowcount

def pg_delete2(d_conn, table_name, cond_where=None, list_values_cond_where=None):
    """
    Deletes any row from any table. Example of use:
    Examples of use:
        #deletes the rows which gid < 4
        pg_delete2(d_conn, table_name='d.buildings', cond_where='where gid < %s', list_values_cond_where=[4])
        #deletes all rows
        pg_delete2(d_conn, table_name='d.buildings')
    Retuns: The number of deleted rows  
    """
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    cons='delete from {table_name}'.format(table_name=table_name)
    if cond_where <> None:
        cons += ' ' + cond_where
        print 'Query: ' + cons
        cursor.execute(cons, list_values_cond_where)
    else:
        print 'Query: ' + cons
        cursor.execute(cons)
    conn.commit()
    return cursor.rowcount

        
def pg_select2(d_conn, table_name, string_fields_to_select, cond_where='', list_val_cond_where=[]):
    """
    Select any field from any table with any condition.
    Return: 
        * None if there is not any selected row
        * a list of dictionaries. Each dictionary is a selected row
          to get the fist dictionary: lista[0]
          to get the seconf dictionary: lista[1]
          ... and so on
    
    Example of use:
        #field names to retrieve separated by comma
        string_fields_to_select = 'gid, descripcion, area, st_asgeojson(geom)'
        #where condition without values. Instead of values you have to use %s
        cond_where='where gid>%s'
        #table name to select rows
        list_val_cond_where=[0]#will select all the rows
        table_name='d.buildings'
        lista=select_to_json(d_conn, table_name, string_fields_to_select, cond_where, list_val_cond_where)
        print lista
        
        print ''
        print 'First row lista[0], wich is a dictionary'
        #gets the first row, wich is a dictionary
        print lista[0]
        
        print ''
        print 'Second row lista[1], wich is a dictionary'
        #gets the second row, wich is a dictionary
        print lista[1]
    """
    cursor=d_conn['cursor']
    
    #forms the select string
    cons='SELECT array_to_json(array_agg(registros)) FROM (select {string_fields_to_select} from {table_name} as t {cond_where} limit 100) as registros;'.format(string_fields_to_select=string_fields_to_select,table_name=table_name,cond_where=cond_where)      
    print cons
    
    #executes the string. The list_val_cond_where has the values of the %s in the select string by order
    if cond_where == '':
        cursor.execute(cons)
    else:
        cursor.execute(cons, list_val_cond_where)
    #gets all rows 
    lista = cursor.fetchall()
    r=lista[0][0]
    if r == None:
        return None #there wheren't selected rows
    else:
        #in ubuntu 14.04 r is a string, in 16.04 is a list
        #so if is string i convert it in list to return alwais a list
        if type(r) is str:
            r=json.loads(r)
        return r
    
def generateExpressions(d,list_fields_to_remove=None, geom_field_name='geom', epsg='25830', geometry_type='POLYGON', epsg_to_reproject=None):
    return dict_to_string_fields_and_vector_values2(d,list_fields_to_remove=None, geom_field_name='geom', epsg='25830', geometry_type='POLYGON', epsg_to_reproject=None)

def dict_to_string_fields_and_vector_values2(d,list_fields_to_remove=None, geom_field_name='geom', epsg='25830', geometry_type='POLYGON', epsg_to_reproject=None):
    """  
    Receives a dictionary and returns an other dictionary with tree things. 
        print d2['str_name_fields'] --> a string with the fields comma separated. Eg: 'geom,c,b,d'
        print d2['list_values'] --> A list with the values of each field. Eg: ['POINT(100 200)', 3, 2, 4]
        print d2['str_s_values'] --> A string with the %s necessary to use in a cursor.execute. eg:  'st_geometryfromtext(%s,25831),%s,%s,%s'
    
    If the table has a geometry field, in the dictionary you have to specify the name of the geometry field as a key and 
        the list of coordinates, space separated between x e y, and comma separated between points. eg:
            d['geom']='100 100, 200 100, 200 200, 100 100' 
    
    Whit this result you can form the expression to insert easily:
        q='insert into table_name ({0}) values ({1})'.format(d2['str_name_fields'],d2['str_s_values'])
    
    And later execute the query with the list of values
        cursor.execute(q,d2['list_values'])
    
    To insert you have the pg_insert2 function, in the my_python_libs.pg_insert2 module. This function uses exactly
    the expressions d2['str_name_fields'], print d2['list_values'] and d2['str_s_values']:
        pg_insert2(conn, cursor, nom_tabla, string_fields_to_set, list_values_to_set, str_s_values):
    
    To update you have the pg_insert2 function, in the my_python_libs.pg_insert2 module. This function uses also the same
        parameters:
        pg_update2(conn, cursor, table_name, string_fields_to_set, string_s_per_field, list_values_to_set, cond_where=None, list_values_cond_where=None):
        
    @type d: dictionary
    @param d: Dictionary key-value, where the keys are the name fields and the values the value fields of a table
    @type list_fields_to_remove: list of strings
    @param list_fields_to_remove: list with the filed names to exclude of the expression. For example ['gid']
        will remove the gid from the expressions and list of values, as this field value is usually 
        automatically assigned by the database
    @type geom_field_name: string
    @param geom_field_name: name of the geometry field in the table. Has to be a key in the dictionary d
    @type epsg: string
    @param epsg: epsg code to assign to the geometry
    @type geometry_type: string
    @param geometry_type: only POINT, LINESTRING or POLYGON. Multi geometries have not been tested
    @type epsg_to_reproject: string
    @param epsg_to_reproject: epsg code to reproject the geometry. If the list of coordinates are in 25830 and you
        you want the geometries in 25831, you can do it. See the latex example of use.

    Examples of use:
    
    d={}
    d['a']=1
    d['b']=2
    d['c']=3
    d['d']=4
    print 'Example 1'
    d2=dict_to_string_fields_and_vector_values2(d,['a'])
    print d2['str_field_names']
    print d2['list_field_values']
    print d2['str_s_values']

    d={}
    d['gid']=1
    d['b']=2
    d['c']=3
    d['d']=4
    d['geom']='100 200'  
    print 'Example 2'
    d2=dict_to_string_fields_and_vector_values2(d,['gid'],geom_field_name='geom', epsg='25831', geometry_type='POINT')
    print d2['str_field_names']
    print d2['list_field_values']
    print d2['str_s_values']
    
    d={}
    d['gid']=1
    d['b']=2
    d['c']=3
    d['d']=4
    d['geom']='100 200'  
    print 'Example 3'
    d2=dict_to_string_fields_and_vector_values2(d,['gid'],geom_field_name='geom', epsg='25830', geometry_type='POINT', epsg_to_reproject='25831')
    print d2['str_field_names']
    print d2['list_field_values']
    print d2['str_s_values']
    
    Results:
        Example 1
        c,b,d
        [3, 2, 4]
        %s,%s,%s
        
        Example 2
        geom,c,b,d
        ['POINT(100 200)', 3, 2, 4]
        st_geometryfromtext(%s,25831),%s,%s,%s
        
        Example 3
        geom,c,b,d
        ['POINT(100 200)', 3, 2, 4]
        st_transform(st_geometryfromtext(%s,25830),25831),%s,%s,%s
    
    """
    #remove the fileds to delete
    if list_fields_to_remove <> None:
        for i in range(len(list_fields_to_remove)):
            key=list_fields_to_remove[i]
            del d[key]
    
    #adds the geometry type and the paranthesis to the coordinates
    coords=d.get(geom_field_name,'')
    geometry_type=geometry_type.upper()
    if coords<>'':#hay geometrÃ­a
        if geometry_type=='POLYGON':
            coords='POLYGON(({coords}))'.format(coords=coords)
        elif geometry_type=='LINESTRING':
            coords='LINESTRING({coords})'.format(coords=coords)
        elif geometry_type=='POINT':
            coords='POINT({coords})'.format(coords=coords)
        elif geometry_type=='MULTIPOLYGON':
            coords='MULTIPOLYGON((({coords})))'.format(coords=coords)
        elif geometry_type=='MULTILINESTRING':
            coords='MULTILINESTRING(({coords}))'.format(coords=coords)
        elif geometry_type=='MULTIPOINT':
            coords='MULTIPOINT(({coords}))'.format(coords=coords)
        d[geom_field_name]=coords
    
    #forms the tree values returned in the dictionary
    it=d.items()
    str_name_fields=''
    list_values =[]     
    str_s_values=''
    for i in range(len(it)):
        str_name_fields = str_name_fields + it[i][0] + ','
        #change the '' values by None
        if it[i][1]=='':
            list_values.append(None) 
        else:
            list_values.append(it[i][1])  
            
        if it[i][0] <> geom_field_name:
            str_s_values=str_s_values + '%s,'
        else:
            if epsg_to_reproject is None:
                st='st_geometryfromtext(%s,{epsg}),'.format(epsg=epsg)
                str_s_values=str_s_values + st
            else:
                st='st_transform(st_geometryfromtext(%s,{epsg}),{epsg_to_reproject}),'.format(epsg=epsg, epsg_to_reproject=epsg_to_reproject)
                str_s_values=str_s_values + st             
            #(%s,st_geometryfromtext(%s,25830))           
    str_name_fields=str_name_fields[:-1]
    str_s_values=str_s_values[:-1]
    df={}
    df['str_field_names']=str_name_fields
    df['list_field_values']=list_values
    df['str_s_values']=str_s_values
    return df

def pg_connect2(database,user,password,host,port):
    """
    Connects with the database with the library psycopg2
    The credentials of the connection are imported from the file var_globales.py
    @return a dictionary wirh the connection and the cursor of the connection
        {'conn':conn, 'cursor':cursor}
    """
    #conexion
    conn=psycopg2.connect(database=database, user=user, password=password, host=host, port=port)
    cursor=conn.cursor()
    d={}
    d['conn']=conn
    d['cursor']=cursor
    return d

def pg_disconnect2(d_conn):
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    cursor.close()
    conn.close()
    
def transform_coords_ol_to_postgis(coords_geom, splitString=','):
    """
    Receives a string coordinate like 'x,y,x,y,x,y,....' from openlayers
    Returns a string like 'x y, x y, x y, ....'
    """
    lc=coords_geom.split(splitString)
    n=len(lc)
    sc=''
    for i in xrange(0,n,2):#starts in 0, stops in n, step 2
        #xrange(0,10,2)-->[0,2,4,6,8]
        x=lc[i]
        y=lc[i+1]
        sc=sc + ',' + x + ' ' + y
    return sc[1:]

def transform_coords_land_registry_gml_to_postgis(coords_geom, splitString=' '):
    """
    Receives a string coordinate like 'x,y x,y x,y,....' from land registry gml
    Returns a string like 'x y, x y, x y, ....'
    """
    
    coords_geom=coords_geom.replace(' ',',')
    return transform_coords_ol_to_postgis(coords_geom)

def reverseXY (coords_geom, separatorIn, separatorOut): 
    #formnato 1: 'x,y,x,y,....'
    #formnato 2:'x y x y x y'
    #formnato 3:'x y, x y, ...'
    #separator can be ' ' or  ','
    
    if separatorIn==',':
        coords=coords_geom.split(',')
    elif separatorIn==' ':
        coords=coords_geom.split(' ')
    
    n=len(coords)
    r=''
    for i in xrange(0,n,2):#starts in 0, stops in n, step 2
        x=coords[i]
        y=coords[i+1]
        r=r + y + separatorOut + x + separatorOut
    return r[:-1]

def transform_coords_cadastral_gml_to_ol(coords_geom, splitString=' '):
    """
    Receives a string coordinate like 'x,y x,y x,y,....' from land registry gml
    Returns a string like 'x y, x y, x y, ....'
    """
    
    coords_geom=coords_geom.replace(' ',',')
    return coords_geom

def insertFunc(nom_tabla, str_field_names, list_field_values, str_s_values2):
    d_conn= pg_connect2(database,user,password,host,port)
    pg_insert2(d_conn, nom_tabla, str_field_names, list_field_values, str_s_values2) 
    pg_disconnect2(d_conn)
    return 'True'




def getTableFieldNames(d_con,nomTable, changeGeomBySt_asgeojosonGeom=True, nomGeometryField='geom'):
    """
    Retuns a list with the table field names.
    @type  nomTabla: string
    @param nomTabla: table name included the schema. Ej. "d.linde". 
        Mandatory specify the shema name: public.tablename
    @type  changeGeomBySt_asgeojosonGeom: boolean
    @param changeGeomBySt_asgeojosonGeom: Specifies id the geom name field is changed by st_asgeojson(fieldName).     
    @type  nomGeometryField: string
    @param nomGeometryField: the geometry field name
    @return: A list with the table fiedl names

    Executes the sentence: 
    SELECT column_name FROM information_schema.columns WHERE table_schema='h30' and table_name = 'linde';
    
    Examples of use:
        listaCampos=getTableFieldNames(d_conn,'d.buildings')
            Returns: [u'gid', u'descripcion', u'area', 'st_asgeojson(geom)', u'fecha']
        listaCampos=getTableFieldNames(d_conn,'d.buildings', changeGeomBySt_asgeojosonGeom=False, nomGeometryField='geom')
            Returns: [u'gid', u'descripcion', u'area', u'geom', u'fecha']
    """
    
    consulta="SELECT column_name FROM information_schema.columns WHERE table_schema=%s and table_name = %s";
    
    lis=nomTable.split(".")
    
    cursor=d_conn['cursor']
    cursor.execute(consulta,lis)
    if cursor.rowcount==0:
        return None
        
    listaValores=cursor.fetchall()#es una lista de tuplas.
            #cada tupla es una fila. En este caso, la fila tiene un
            #unico elemento, que es el nombre del campo.
    listaNombreCampos=[]
    for fila2 in listaValores:
        valor=fila2[0]
        if changeGeomBySt_asgeojosonGeom:
            if valor==nomGeometryField:
                valor='st_asgeojson({0})'.format(nomGeometryField)
        listaNombreCampos.append(valor)
    return listaNombreCampos    


if __name__== '__main__':
    database='desweb'
    user='postgres'
    password='postgres'
    host='localhost'
    port=5432

    #conexion
    d_conn=pg_connect2(database=database, user=user, password=password, host=host, port=port)

    
    listaCampos=getTableFieldNames(d_conn,'d.buildings')
    print listaCampos
    

    listaCampos=getTableFieldNames(d_conn,'d.buildings', changeGeomBySt_asgeojosonGeom=False, nomGeometryField='geom')
    print listaCampos
    
    #close connection
    pg_disconnect2(d_conn=d_conn)