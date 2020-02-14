import qgis.core as qgis
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
import gdal
import ogr
from PyQt5.QtCore import *
import os
import argparse
import sys
import csv
from subprocess import call
import shutil
from joblib import Parallel, delayed
import tempfile
from qgis.PyQt.QtCore import QVariant
os.environ['QT_QPA_PLATFORM']='offscreen'

qgis_prefix="/usr"    
qgis.QgsApplication.setPrefixPath(qgis_prefix, True) 
qgs = qgis.QgsApplication([], False)
qgs.initQgis()


def main():

    from random import shuffle

    # do stuff
    parser = argparse.ArgumentParser(
         prog="area_calculation",
         description="Uses supplied threshold to workout area occupied by a species from SDM probabilityt map.",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            help="Your TIFF (or other raster) with probabilities"
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            help="The output shapefile."
            )
    parser.add_argument(
            'threshold', 
            metavar='threshold',
            type=float,
            help="The value to use as a threshold. Values in the prob map > than this will be where species is found."
            )


    args = parser.parse_args()
    verbose = args.verbose
    input_file = args.input_file
    output_file = args.output_file
    threshold = args.threshold

    area_from_raster(threshold, input_file, output_file)

    return


def area_from_raster(threshold, in_file, out_file):

        # load raster produced by r
        MaxEnt_prediction = qgis.QgsRasterLayer(in_file)
        temp_dir = "/tmp"

        # work out the threshold part
        entries = []
        # Define band1
        me_pred = QgsRasterCalculatorEntry()
        me_pred.ref = 'temp@1'
        me_pred.raster = MaxEnt_prediction
        me_pred.bandNumber = 1
        entries.append( me_pred )
        # Process calculation with input extent and resolution
        calc = QgsRasterCalculator( 'temp@1 > '+str(threshold), os.path.join(temp_dir, "temp2.tif"), 'GTiff', MaxEnt_prediction.extent(), MaxEnt_prediction.width(), MaxEnt_prediction.height(), entries )
        calc.processCalculation()

        # here we switch to using gdal so we can polygonize the raster
        sourceRaster = gdal.Open(os.path.join(temp_dir, "temp2.tif"))
        band = sourceRaster.GetRasterBand(1)
        raster_field = ogr.FieldDefn('presence', ogr.OFTInteger)
        outShapefile = "polygonized"
        dest_srs = ogr.osr.SpatialReference()
        dest_srs.ImportFromEPSG(32630)
        driver = ogr.GetDriverByName("ESRI Shapefile")
        if os.path.exists(os.path.join( out_file)):
            driver.DeleteDataSource( out_file)
        outDatasource = driver.CreateDataSource( out_file)
        outLayer = outDatasource.CreateLayer("polygonized", srs=dest_srs)
        outLayer.CreateField(raster_field)
        gdal.Polygonize( band, None, outLayer, 0, [], callback=None )
        outDatasource.Destroy()
        sourceRaster = None

        # we now have a polygon version of the raster.
        # load this in using Q and then delete the zero-parts (1 is where the critter lives)
        polygon = qgis.QgsVectorLayer(os.path.join( out_file), "Shapefile", "ogr")
        # check this is valid
        if not polygon.isValid():
            print("Error loading file ", os.path.join(out_file))
        # build a request to filter the features based on an attribute
        request = qgis.QgsFeatureRequest().setFilterExpression('"presence" != 1')
        polygon.startEditing()
        # loop over the features and delete
        for f in polygon.getFeatures(request):
            polygon.deleteFeature(f.id())

        # now calculate the areas
        lProvider = polygon.dataProvider()
        lProvider.addAttributes( [ qgis.QgsField("Area",QVariant.Double) ] )
        #lProvider.setFields()
        

        sum_area = 0
        # set up the calculator
        elps_crs = qgis.QgsCoordinateReferenceSystem()
        elps_crs.createFromUserInput("WGS84")
        lyr_crs = polygon.crs()
        trans_context = qgis.QgsCoordinateTransformContext()
        trans_context.calculateDatumTransforms(lyr_crs, elps_crs)
        calculator = qgis.QgsDistanceArea()
        calculator.setEllipsoid('WGS84')
        calculator.setSourceCrs(lyr_crs, trans_context)

        for gFeat in polygon.getFeatures():
            geom = gFeat.geometry()
            area = calculator.measureArea(geom)
            gFeat
            sum_area += area
        polygon.commitChanges()
        
        sum_area = sum_area / 1000000. # convert to sq km
        print(str(sum_area)+"km2")



if __name__ == "__main__":
    main()
    qgs.exitQgis()

