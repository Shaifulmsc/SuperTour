# -*- coding: utf-8 -*-
'''
Created on 22 mar. 2017

@author: joamona
'''

import pg_update
import pg_delete
import pg_connect
import pg_select
import pg_insert

d_conn=pg_connect.pg_connect('pozossan','postgres','postgres','localhost',5432)

def check_consultar(all_rows=False):
    campos='{"gid":"","descripcion":"","id_trabajo":"","z_tapa":"","profundidad":"","diametro":"","type":"","coordinates":""}'
    if all_rows:
        resp=pg_select.pg_select(d_conn=d_conn, tabla="d.pozos", pk_name="", pk_value="", campos=campos)
    else:
        resp=pg_select.pg_select(d_conn=d_conn, tabla="d.pozos", pk_name="gid", pk_value="1", campos=campos)
    print resp

def check_delete(gid):
    resp=pg_delete.pg_delete(d_conn=d_conn, tabla="d.pozos", pk_name="gid", pk_value=gid)
    print resp
    
def check_update():
    campos='{"z_tapa":"50"}'
    resp=pg_update.pg_update(d_conn=d_conn, tabla="d.pozos", pk_name="gid", pk_value="10", registro=campos)
    print resp

def check_insert_pozo():
    campos='{"gid":"10","descripcion":"Hola","id_trabajo":"1","z_tapa":"10","profundidad":"10","diametro":"10","type":"Point","coordinates":"727763.05556,4372987.48466"}'
    resp=pg_insert.pg_insert(d_conn=d_conn, tabla="d.pozos", pk_name="gid", registro=campos)
    print resp
def check_insert_edificio():
    """
    create table d.edificios (gid serial primary key, descripcion varchar);
    select addgeometrycolumn('d','edificios','geom',25830,'POLYGON',2, true);
    """
    #coords="727900.21697,4372978.67737,727963.98177,4373016.61882,727987.19904,4373089.36627,727981.00777,4373155.92244,727910.95135,4373194.55751, 727900.21697,4372978.67737"
    campos='{"gid":"10","descripcion":"Hola","type":"Polygon","coordinates":"727900.21697,4372978.67737,727963.98177,4373016.61882,727987.19904,4373089.36627,727981.00777,4373155.92244,727910.95135,4373194.55751, 727900.21697,4372978.67737"}'
    resp=pg_insert.pg_insert(d_conn=d_conn, tabla="d.edificios", pk_name="gid", registro=campos)
    print resp


#check_consultar()
#check_consultar(all=True)
#check_delete("9")
#check_update()
#check_insert_pozo()
#check_insert_edificio()

d_conn['cursor'].close()
d_conn['conn'].close()
