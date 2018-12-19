# -*- coding: utf-8 -*-
'''
Created on 12 Mar 2018
@author: Gaspar Mora-Navarro
Department of Cartographic Engineering Geodesy and Photogrammetry
Higher Technical School of Geodetic, Cartographic and Topographical Engineering
@email: joamona@cgf.upv.es
'''
import os, sys

DESWEB_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(DESWEB_DIR)
print DESWEB_DIR

from pyupv.pg_operations2 import pg_operations2

def extractFieldValueFromGml(gmlString, labelInit,labelFin):
    """
    Returns the value between two labels in a gml.
    Eliminates spaces at start and end of the returned value
    """
    g=gmlString
    s1=labelInit
    s2=labelFin
    i=g.find(s1)
    f=g.find(s2)
    g2= g[i:f]
    s1=g2.find('>')+1
    g3=g2[s1:]
    return g3.strip()


if __name__=='__main__':
    cadastralGML="""
<?xml version="1.0" encoding="ISO-8859-1"?>

<!--Parcela Catastral de la D.G. del Catastro.-->

<!--La precisión es la que corresponde nominalmente a la escala de captura de la cartografía-->

<FeatureCollection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0" xmlns:gmd="http://www.isotc211.org/2005/gmd" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://inspire.ec.europa.eu/schemas/cp/4.0 http://inspire.ec.europa.eu/schemas/cp/4.0/CadastralParcels.xsd" xmlns="http://www.opengis.net/wfs/2.0" timeStamp="2018-04-01T02:08:45" numberMatched="1" numberReturned="1">

  <member>

    <cp:CadastralParcel gml:id="ES.SDGC.CP.3662001TF3136S">

      <cp:areaValue uom="m2">930</cp:areaValue>

      <cp:beginLifespanVersion>2005-08-16T00:00:00</cp:beginLifespanVersion>

      <cp:endLifespanVersion xsi:nil="true" nilReason="http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"></cp:endLifespanVersion>

      <cp:geometry>

        <gml:MultiSurface gml:id="MultiSurface_ES.SDGC.CP.3662001TF3136S" srsName="http://www.opengis.net/def/crs/EPSG/0/4258">

          <gml:surfaceMember>

            <gml:Surface gml:id="Surface_ES.SDGC.CP.3662001TF3136S.1" srsName="http://www.opengis.net/def/crs/EPSG/0/4258">

              <gml:patches>

                <gml:PolygonPatch>

                <gml:exterior>

                    <gml:LinearRing>

                      <gml:posList srsDimension="2" count="16">36.252591 -5.965154 36.252575 -5.96518 36.252553 -5.965232 36.252539 -5.965287 36.252532 -5.965345 36.252534 -5.965404 36.252546 -5.965465 36.252563 -5.965515 36.252523 -5.965584 36.252385 -5.965661 36.252504 -5.965644 36.252789 -5.965526 36.252827 -5.965434 36.252746 -5.965299 36.252634 -5.965168 36.252591 -5.965154</gml:posList>

                    </gml:LinearRing>

                </gml:exterior>

                </gml:PolygonPatch>

              </gml:patches>

            </gml:Surface>

          </gml:surfaceMember>

        </gml:MultiSurface>

      </cp:geometry>

      <cp:inspireId>

        <Identifier xmlns="http://inspire.ec.europa.eu/schemas/base/3.3">

          <localId>3662001TF3136S</localId>

          <namespace>ES.SDGC.CP</namespace>

        </Identifier>

      </cp:inspireId>

      <cp:label>01</cp:label>

      <cp:nationalCadastralReference>3662001TF3136S</cp:nationalCadastralReference>

      <cp:referencePoint>

        <gml:Point gml:id="ReferencePoint_ES.SDGC.CP.3662001TF3136S" srsName="http://www.opengis.net/def/crs/EPSG/0/4258"> 

          <gml:pos>36.252645 -5.965413</gml:pos>

        </gml:Point>

      </cp:referencePoint>

    </cp:CadastralParcel>

  </member>

</FeatureCollection>
    """
    
    landRegistryGML="""
<corpme:publicfinca xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:gml="http://www.opengis.net/gml" xmlns:corpme="http://www.registradores.org/" xsi:schemaLocation="http://www.registradores.org/CORPME_GML.xsd"><gml:name>publicfinca</gml:name><gml:boundedBy><gml:Box gml:srsName="http://www.opengis.net/gml/srs/epsg.xml#25830"><gml:coord><gml:X>738231.783969023</gml:X><gml:Y>4414345.54629909</gml:Y></gml:coord><gml:coord><gml:X>755254.033805427</gml:X><gml:Y>4424170.90609409</gml:Y></gml:coord></gml:Box></gml:boundedBy><gml:featureMember><corpme:Feature gml:fid="8087"><gml:MultiPolygon gml:srsName="http://www.opengis.net/gml/srs/epsg.xml#25830">
  <gml:polygonMember>
    <gml:Polygon>
      <gml:outerBoundaryIs>
        <gml:LinearRing>
          <gml:coordinates>
            746903.58 4416281.57 746905.75 4416281.89 746936.29 4416286.0 746940.26 4416286.53 746944.31 4416282.59 746949.19,4416287.73 746952.98 4416288.24 746968.12,4416290.29 747009.83 4416295.9 747013.17 4416296.35 
          </gml:coordinates>
        </gml:LinearRing>
      </gml:outerBoundaryIs>
    </gml:Polygon>
  </gml:polygonMember>
</gml:MultiPolygon>
<gid>8087</gid><idreg>0102151500000000</idreg><supf>1377.8849999849044</supf><estado>2</estado><idufir>12015000403398</idufir></corpme:Feature></gml:featureMember></corpme:publicfinca>

"""


  

    cooCP=extractFieldValueFromGml(cadastralGML,'<gml:posList srsDimension="2"','</gml:posList>')
    print cooCP
    print pg_operations2.transform_coords_ol_to_postgis(coords_geom=cooCP, splitString=' ')
    
    cooLR=extractFieldValueFromGml(landRegistryGML,'<gml:coordinates>','</gml:coordinates>')
    print cooLR
    print pg_operations2.transform_coords_land_registry_gml_to_postgis(cooLR)
        
    idufir=extractFieldValueFromGml(landRegistryGML,'<idufir>','</idufir>')
    print idufir
    



