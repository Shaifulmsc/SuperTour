<?xml version="1.0" encoding="ISO-8859-1"?>
<!--Instancia de ejemplo de edificio.-->
<gml:FeatureCollection gml:id="ES.SDGC.BU" xmlns:ad="urn:x-inspire:specification:gmlas:Addresses:3.0" xmlns:base="urn:x-inspire:specification:gmlas:BaseTypes:3.2" xmlns:bu-base="http://inspire.jrc.ec.europa.eu/schemas/bu-base/3.0" xmlns:bu-core2d="http://inspire.jrc.ec.europa.eu/schemas/bu-core2d/2.0" xmlns:bu-ext2d="http://inspire.jrc.ec.europa.eu/schemas/bu-ext2d/2.0" xmlns:cp="urn:x-inspire:specification:gmlas:CadastralParcels:3.0" xmlns:el-bas="http://inspire.jrc.ec.europa.eu/schemas/el-bas/2.0" xmlns:el-cov="http://inspire.jrc.ec.europa.eu/schemas/el-cov/2.0" xmlns:el-tin="http://inspire.jrc.ec.europa.eu/schemas/el-tin/2.0" xmlns:el-vec="http://inspire.jrc.ec.europa.eu/schemas/el-vec/2.0" xmlns:gco="http://www.isotc211.org/2005/gco" xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:gmlcov="http://www.opengis.net/gmlcov/1.0" xmlns:gn="urn:x-inspire:specification:gmlas:GeographicalNames:3.0" xmlns:gsr="http://www.isotc211.org/2005/gsr" xmlns:gss="http://www.isotc211.org/2005/gss" xmlns:gts="http://www.isotc211.org/2005/gts" xmlns:swe="http://www.opengis.net/swe/2.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://inspire.jrc.ec.europa.eu/schemas/bu-ext2d/2.0 http://inspire.ec.europa.eu/draft-schemas/bu-ext2d/2.0/BuildingExtended2D.xsd">
	<gml:featureMember>
		<bu-ext2d:Building gml:id="ES.LOCAL.1">
			<bu-core2d:beginLifespanVersion xsi:nil="true" nilReason="other:unpopulated"/>
<!--PONER AQUI SI ES FUNCIONAL O EN CONSTRUCCION.-->
			<bu-core2d:conditionOfConstruction>{{condicion_construccion}}</bu-core2d:conditionOfConstruction>
			<bu-core2d:dateOfConstruction>
<!--FECHA DE CONSTRUCCION SI ES FUNCIONAL.-->
				<bu-core2d:DateOfEvent>
					<bu-core2d:beginning>{{fecha_inicio_construc}}</bu-core2d:beginning>
					<bu-core2d:end>{{fecha_fin_construc}}</bu-core2d:end>
				</bu-core2d:DateOfEvent>
			</bu-core2d:dateOfConstruction>
			<bu-core2d:endLifespanVersion xsi:nil="true" nilReason="other:unpopulated"/>
			<bu-core2d:inspireId>
				<base:Identifier>
<!--IDENTIFICATIVO DE LA FINCA Y EDIFICIO.-->
					<base:localId>{{localid_edificio}}</base:localId>
					<base:namespace>{{namespace_edificio}}</base:namespace>
				</base:Identifier>
			</bu-core2d:inspireId>
			<bu-ext2d:geometry>
				<bu-core2d:BuildingGeometry>
					<bu-core2d:geometry>
						<gml:Surface gml:id="surface_ES.LOCAL.{{gid}}" srsName="urn:ogc:def:crs:EPSG::{{epsg}}">
							<gml:patches>
							<gml:PolygonPatch>
							<gml:exterior>
								<gml:LinearRing>
<!--LISTA DE COORDENADAS-->			<gml:posList>
										{{coordenadas}}
									</gml:posList>
								</gml:LinearRing>
							</gml:exterior>
							</gml:PolygonPatch>
							</gml:patches>
						</gml:Surface>
					</bu-core2d:geometry>
<!--AQUI HAY QUE PONER LA PRECISION REAL DE LAS COORDENADAS-->
					<bu-core2d:horizontalGeometryEstimatedAccuracy uom="m">{{precision_m}}</bu-core2d:horizontalGeometryEstimatedAccuracy>
					<bu-core2d:horizontalGeometryReference>footPrint</bu-core2d:horizontalGeometryReference>
					<bu-core2d:referenceGeometry>true</bu-core2d:referenceGeometry>
				</bu-core2d:BuildingGeometry>
			</bu-ext2d:geometry>
<!-- USO PRINCIPAL, SI ES CONOCIDO-->
			<bu-ext2d:currentUse>{{uso_edificio}}</bu-ext2d:currentUse>
<!-- NUMERO DE INMUEBLES-->
			<bu-ext2d:numberOfBuildingUnits>{{numero_inmuebles}}</bu-ext2d:numberOfBuildingUnits>
<!-- NUMERO DE VIVIENDAS-->
			<bu-ext2d:numberOfDwellings>{{numero_viviendas}}</bu-ext2d:numberOfDwellings>
<!-- NUMERO DE PLANTAS SOBRE RASANTE-->
			<bu-ext2d:numberOfFloorsAboveGround>{{n_plant_sobre_ras}}</bu-ext2d:numberOfFloorsAboveGround>
			<bu-ext2d:officialArea>
				<bu-ext2d:OfficialArea>
					<bu-ext2d:officialAreaReference>grossFloorArea</bu-ext2d:officialAreaReference>
<!-- SUPERFICIE CONSTRUIDA TOTAL EN M2-->
					<bu-ext2d:value uom="m2">{{area_utm}}</bu-ext2d:value>
				</bu-ext2d:OfficialArea>
			</bu-ext2d:officialArea>
		</bu-ext2d:Building>
	</gml:featureMember>
</gml:FeatureCollection>
