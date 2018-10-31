<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- From Steven Kay: https://gis.stackexchange.com/questions/243392/circular-color-map-in-qgis -->
<qgis version="2.18.7" minimumScale="inf" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" classificationMax="360" classificationMinMaxOrigin="MinMaxFullExtentEstimated" band="1" classificationMin="0" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" clip="0">
          <item alpha="255" value="-3.141592654" label="-pi" color="#2250fe"/>
          <item alpha="255" value="-1.570796327" label="-pi/2" color="#00a83b"/>
          <item alpha="255" value="0" label="0" color="#fdd248"/>
          <item alpha="255" value="1.570796327" label="pi/2" color="#b3507e"/>
          <item alpha="255" value="3.141592654" label="pi" color="#2250fe"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
