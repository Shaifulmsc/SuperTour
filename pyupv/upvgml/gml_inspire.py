# -*- coding: utf-8 -*-
"""
Created on 22/11/2015

@author: joamona

* Todos los nombres de campo deben estar en unicode, incluido el de las geometrias
* Los nombres de los campos inspire deben mantener mayúsculas y minúsculas, según la norma, pero
    los nombres de los campos en postgis deben llamarse igual pero todo en minúscula
* Obligatorio el campo beginLifespanVersion y de tipo timestamp
"""
import os
from dweb import dweb

def as_gml_inspire_cp_lista(nombreClavePrincipal,nombreCampoGeometriaTransformado, listaDic):
    """
    Esta función devuelve un fichero GML para cada geometría en una lista.
    Devuelve una lista de cadenas independientes de ficheros GML independientes. Una por cada diccionario listadic.
    Lo que hace la función es llamar repetidamente a la función as_gml_inspire_cp.
    La documentación de los parámetros es la de la función as_gml_inspire_cp
    La diferencia entre esta función y as_gml_inspire_cp es que esta función devuelve un gml
    @return: list
    """
    lista_gmls_independientes=[]
    for dic in listaDic:
        gml= as_gml_inspire_cp(nombreClavePrincipal,nombreCampoGeometriaTransformado, listaDic=[dic])
        lista_gmls_independientes.append(gml)
    return lista_gmls_independientes

def as_gml_inspire_cp(nombreClavePrincipal,nombreCampoGeometriaTransformado, listaDic):
    """
    Esta función devuelve un fichero GML para todas las geometrías
    Genera un gml adecuado para el Catastro español. Tema CadastralParcel. Para hacerlo, necesita una carpeta con dos gml
    que hacen de plantilla. En las plantillas deben estar los nombres de los campos inspire entre dobles llaves.
    
    Los ficheros son:
        nom_arch_base=dir_base + "/gmltemplate/base.gml"
        nom_arch_featuremember=dir_base + "/gmltemplate/featuremember.gml"
        dir_base es la carpeta donde se encuentra el módulo que contiene esta función
    @param nombreCampoGeometriaTransformado: Nombre del campo de la geometría transformada a gml
        que se pone en la consulta del objeto oConsutasPg para obtener la geometría en gml
        Ejemplo: u"st_asgml(3,'geom',15,1,'gml',concat('Surface_ES.LOCAL.CP',gid::text))"
        Este nombre debe ir como clave del diccionario dicValores. Tambien debe ser un elemento
        de la lista listaCampos. El valor de la clave debe
        ser la geometría en gml. El nombre Surface_ES.LOCAL.CP, se pone local porque es el identificador
        interno del elemento gml. Creo que puede ser cualquier cosa mientras no se repita en el fichero,
        es decir, puede no poner surface, ni multisurface
    @type nombreCampoGeometriaTransformado: unicode
    @param nombreClavePrincipal: Nombre del campo gid. Debe ser la clave de un elemento de listaDic
    @type nombreClavePrincipal: unicode
    @param listaDic: lista de diccionarios. Cada diccionario debe tener como claves los nombres de los campos inspire,
        conservando mayúsculas y minusculas. Estos nombres se deben repetir igual entre llaves en la plantilla "/gmltemplate/featuremember.gml".
        La función las claves del diciconario en el fichero y las sustituye por sus valores.
        Entre las claves debe estar obligatoriamente beginLifespanVersion. Este debe ser un campo de tipo timestamp en postgis, que en Python se 
        convierte a un objeto de la clase Date, del paquete dateTime.
        Para obtener esta lista de diccionarios, se procede como sigue:
        
        nombreCampoGeometria=u'geom'
        nombreClavePrincipal=u'gid'
        #lista de campos que se van a solicitar. IMPORTANTE, aunque la lista tiene letras en mayusculas, los nombres
        de los campos en la base de datos no deben tener ninguna mayuscula
        listaCamposCaps=[u'localId',u'nameSpace',u'label',u'beginLifespanVersion',u'endLifespanVersion',u'areaValue', u'nationalCadastralReference']#lista de campos tal y como serán nombrados en el gml. Respetar mayusculas y minúsculas
                    #en la base de datos los nombres de los campos deben estar todos en minúscula

        oCons=pyPgGas.ConsultasPg(oConectaPg=oCon)
        nombreTabla=u'ed_src25830.cadastralparcel'
        
        #se añade la solicitud del campo de la geometría transformada a gml
        nombreCampoGeometriaTransformado=u"st_asgml(3," + nombreCampoGeometria + u",15,1,'gml',concat('Surface_ES.LOCAL.CP',gid::text))"
        listaCamposCaps.append(nombreCampoGeometriaTransformado)#se solicita la clave principal
        
        listaCamposCaps.append(nombreClavePrincipal)#se solicita la clave principal

        cond_where='id_trabajo=%s'
        lista_valores_condwhere=[1]
        listaDic=oCons.recuperaDatosTablaByteaDic(nombreTabla=nombreTabla, listaCampos=listaCamposCaps,condicionWhere=cond_where,listaValoresCondWhere=lista_valores_condwhere)
    @type listaDic: list
    @return: Devuelve un string con el fichero en gml. Si listaDic tiene varios diccionarios. Mete todos los valores en el mismo gml
    @raise exception: En el caso de que listaDic no tenga ningún elemento
    """ 

    listaCamposCaps=listaDic[0].keys()
    listaCamposCaps.remove(nombreCampoGeometriaTransformado)#quito el gml para recorrer el resto de campos
    listaCamposCaps.remove(nombreClavePrincipal)#quito el gid para recorrer el resto de campos
    listaCamposCaps.remove('beginLifespanVersion')#quito este para recorrer el resto de campos

    dir_base=os.path.dirname(__file__) #ruta al archivo actual.
    nom_arch_base=dir_base + "/gmltemplate/base.gml"
    nom_arch_featuremember=dir_base + "/gmltemplate/featuremember.gml"
    
    template_base_gml=dweb.leer_archivo(nom_arch_base)
    template_featuremember_gml=dweb.leer_archivo(nom_arch_featuremember)
    
    todos_featuremember=''
    for dic in listaDic:
        dic_replace={}
        geometry=str(dic[nombreCampoGeometriaTransformado])
        geometry=geometry.replace('gml:id="Surface', 'gml:id="MultiSurface',1)
        gid=dic[nombreClavePrincipal]
        
        ti=dic['beginLifespanVersion']
        dia=ti.strftime('%Y-%m-%d')
        hora=ti.strftime('%H:%M:%S')
        
        dic_replace[nombreClavePrincipal]=str(gid)
        dic_replace['geometry']=str(geometry)
        dic_replace['beginLifespanVersion']=dia+'T'+hora
        for campo in listaCamposCaps:
            valor=str(dic[campo])
            if valor==None:
                valor=u''
            dic_replace[str(campo)]=str(valor)
        featuremember=dweb.reemplazar(cadena=template_featuremember_gml, diccionario=dic_replace)
        todos_featuremember+=featuremember
    
    dic_replace2={}
    dic_replace2['feature_members']=todos_featuremember
    gmlfin=dweb.reemplazar(cadena=template_base_gml, diccionario=dic_replace2)
    
    return gmlfin


def as_gml_inspire_edificio(nombreClavePrincipal,nombreCampoGeometriaTransformado, listaDic):
    """
    Esta función devuelve un fichero GML para todas las geometrías
    Genera un gml adecuado para el Catastro español. Tema Buildings. Para hacerlo, necesita una carpeta con un fichero gml
    
    Los campos de partida son:
    condicion_construccion, fecha_inicio_construc, fecha_fin_construc, localid_edificio, namespace_edificio, uso_edificio, numero_inmuebles, numero_viviendas, n_plant_sobre_ras
    Los ficheros son:
        nom_arch_base=dir_base + "/gmltemplate/edificio.gml"
        dir_base es la carpeta donde se encuentra el módulo que contiene esta función
    @param nombreCampoGeometriaTransformado: Nombre del campo de la geometría transformada a gml
        que se pone en la consulta del objeto oConsutasPg para obtener la geometría en gml
        Ejemplo: u"st_asgml(3,'geom',15,1,'gml',concat('Surface_ES.LOCAL.CP',gid::text))"
        Este nombre debe ir como clave del diccionario dicValores. Tambien debe ser un elemento
        de la lista listaCampos. El valor de la clave debe
        ser la geometría en gml. El nombre Surface_ES.LOCAL.BU, se pone local porque es el identificador
        interno del elemento gml. Creo que puede ser cualquier cosa mientras no se repita en el fichero,
        es decir, puede no poner surface, ni multisurface
    @type nombreCampoGeometriaTransformado: unicode
    @param nombreClavePrincipal: Nombre del campo gid. Debe ser la clave de un elemento de listaDic
    @type nombreClavePrincipal: unicode
    @param listaDic: lista de diccionarios con un solo diccionario. Cada diccionario debe tener como claves los nombres de los campos inspire,
        conservando mayúsculas y minusculas. Estos nombres se deben repetir igual entre llaves en la plantilla "/gmltemplate/featuremember.gml".
        La función las claves del diciconario en el fichero y las sustituye por sus valores.
        Entre las claves debe estar obligatoriamente beginLifespanVersion. Este debe ser un campo de tipo timestamp en postgis, que en Python se 
        convierte a un objeto de la clase Date, del paquete dateTime.
        Para obtener esta lista de diccionarios, se procede como sigue:
        
        nombreCampoGeometria=u'geom'
        nombreClavePrincipal=u'gid'
        #lista de campos que se van a solicitar. IMPORTANTE, aunque la lista tiene letras en mayusculas, los nombres
        de los campos en la base de datos no deben tener ninguna mayuscula
        listaCamposCaps=[u'localId',u'nameSpace',u'label',u'beginLifespanVersion',u'endLifespanVersion',u'areaValue', u'nationalCadastralReference']#lista de campos tal y como serán nombrados en el gml. Respetar mayusculas y minúsculas
                    #en la base de datos los nombres de los campos deben estar todos en minúscula

        oCons=pyPgGas.ConsultasPg(oConectaPg=oCon)
        nombreTabla=u'ed_src25830.cadastralparcel'
        
        #se añade la solicitud del campo de la geometría transformada a gml
        nombreCampoGeometriaTransformado=u"st_asgml(3," + nombreCampoGeometria + u",15,1,'gml',concat('Surface_ES.LOCAL.CP',gid::text))"
        listaCamposCaps.append(nombreCampoGeometriaTransformado)#se solicita la clave principal
        
        listaCamposCaps.append(nombreClavePrincipal)#se solicita la clave principal

        cond_where='id_trabajo=%s'
        lista_valores_condwhere=[1]
        listaDic=oCons.recuperaDatosTablaByteaDic(nombreTabla=nombreTabla, listaCampos=listaCamposCaps,condicionWhere=cond_where,listaValoresCondWhere=lista_valores_condwhere)
    @type listaDic: list
    @return: Devuelve un string con el fichero en gml. Si listaDic tiene varios diccionarios. Mete todos los valores en el mismo gml
    @raise exception: En el caso de que listaDic no tenga ningún elemento
    """ 

    dic=listaDic[0]
    dir_base=os.path.dirname(__file__)
    nom_arch_base=dir_base + "/gmltemplate/edificio.gml"
    template_base_gml=dweb.leer_archivo(nom_arch_base)
    
    dic_replace={}

    #condicion_construccion, fecha_inicio_construc, fecha_fin_construc, localid_edificio, namespace_edificio, uso_edificio, numero_inmuebles, numero_viviendas, n_plant_sobre_ras
 
    condicion_construccion=dic['condicion_construccion']
    if condicion_construccion is None:
        dic_replace['condicion_construccion']=''
    else:
        dic_replace['condicion_construccion']=condicion_construccion
    
    ti=dic['fecha_inicio_construc']
    if not(ti is None):
        dia=ti.strftime('%Y-%m-%d')
        hora=ti.strftime('%H:%M:%S')
        dic_replace['fecha_inicio_construc']=dia+'T'+hora
    else:
        dic_replace['fecha_inicio_construc']=''

    ti=dic['fecha_fin_construc']
    if not(ti is None):
        dia=ti.strftime('%Y-%m-%d')
        hora=ti.strftime('%H:%M:%S')
        dic_replace['fecha_fin_construc']=dia+'T'+hora
    else:
        dic_replace['fecha_fin_construc']=''    
        
    localid_edificio=dic['localid_edificio']
    if localid_edificio is None:
        dic_replace['localid_edificio']=''
    else:
        dic_replace['localid_edificio']=localid_edificio
        
    namespace_edificio=dic['namespace_edificio']
    if namespace_edificio is None:
        dic_replace['namespace_edificio']=''
    else:
        dic_replace['namespace_edificio']=namespace_edificio
    
    #uso_edificio, numero_inmuebles, numero_viviendas, n_plant_sobre_ras
    uso_edificio=dic['uso_edificio']
    if uso_edificio is None:
        dic_replace['uso_edificio']=''
    else:
        dic_replace['uso_edificio']=uso_edificio
    
    numero_inmuebles=dic['numero_inmuebles']
    if numero_inmuebles is None:
        dic_replace['numero_inmuebles']=''
    else:
        dic_replace['numero_inmuebles']=str(numero_inmuebles)
    
    numero_viviendas=dic['numero_viviendas']
    if numero_viviendas is None:
        dic_replace['numero_viviendas']=''
    else:
        dic_replace['numero_viviendas']=str(numero_viviendas)
        
    n_plant_sobre_ras=dic['n_plant_sobre_ras']
    if n_plant_sobre_ras is None:
        dic_replace['n_plant_sobre_ras']=''
    else:
        dic_replace['n_plant_sobre_ras']=str(n_plant_sobre_ras)
    
    precision_cm=dic['precision_cm']
    if precision_cm is None:
        dic_replace['precision_m']=''
    else:
        dic_replace['precision_m']=str(precision_cm/100)

    area_utm=dic['area_utm']
    if area_utm is None:
        dic_replace['area_utm']=''
    else:
        dic_replace['area_utm']=str(area_utm)

    gid=dic[nombreClavePrincipal]
    dic_replace[nombreClavePrincipal]=str(gid)
    
    geometry=str(dic[nombreCampoGeometriaTransformado])#cojo solo las coordenadas
    cad_inicio='<gml:posList srsDimension="2">'
    cad_fin='</gml:posList>'

    pos_ini=geometry.find(cad_inicio)+ 30 #hay 30 caracteres
    pos_fin=geometry.find(cad_fin)

    coordenadas=geometry[pos_ini:pos_fin]
    dic_replace['coordenadas']=coordenadas
    
    cad_inicio='srsName="urn:ogc:def:crs:EPSG::'#hay 31 caracteres
    pos_inicio=geometry.find(cad_inicio)+31
    epsg=geometry[pos_inicio:pos_inicio+5]
    dic_replace['epsg']=epsg
    
    gmlfin=dweb.reemplazar(cadena=template_base_gml, diccionario=dic_replace)
    
    return gmlfin


