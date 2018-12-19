<gml:featureMember>
	<cp:CadastralParcel gml:id="ES.LOCAL.CP.{{gid}}">
	   <gml:boundedBy>
        <gml:Envelope srsName="urn:ogc:def:crs:EPSG::{{epsg}}">
          <gml:lowerCorner>{{esquina_inf_izq}}</gml:lowerCorner>
          <gml:upperCorner>{{esquina_sup_derecha}}</gml:upperCorner>
        </gml:Envelope>
        </gml:boundedBy>
		<cp:areaValue uom="m2">{{areaValue}}</cp:areaValue>
		<cp:beginLifespanVersion>{{beginLifespanVersion}}</cp:beginLifespanVersion>
		<cp:endLifespanVersion xsi:nil="true" nilReason="other:unpopulated"></cp:endLifespanVersion>
		<cp:geometry>
			{{geometry}}
		</cp:geometry>
		<cp:inspireId xmlns:base="urn:x-inspire:specification:gmlas:BaseTypes:3.2">
			<base:Identifier>
			  <base:localId>{{localId}}</base:localId>
			  <base:namespace>{{nameSpace}}</base:namespace>
			</base:Identifier>
		</cp:inspireId>
		<cp:label>{{label}}</cp:label>
		<cp:nationalCadastralReference>{{nationalCadastralReference}}</cp:nationalCadastralReference>
		<cp:referencePoint>
            <gml:Point gml:id="ReferencePoint_ES.LOCAL.CP.{{gid}}" srsName="urn:ogc:def:crs:EPSG::{{epsg}}">
              <gml:pos>{{reference_point}}</gml:pos>
            </gml:Point>
        </cp:referencePoint>
	</cp:CadastralParcel>
</gml:featureMember>
