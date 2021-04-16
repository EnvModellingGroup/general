#!/usr/bin/env python
import vtk
import numpy as np
import argparse
from lxml import etree
xml_parser = etree.XMLParser(remove_blank_text=True)
import os
from scipy.interpolate import griddata
import sys
#import gdal
#from gdalconst import *
#from osgeo import osr
from subprocess import call
import tempfile
import csv


def main():

    def coords(s):
        try:
            x, y, z = map(int, s.split(','))
            return x, y, z
        except:
            raise argparse.ArgumentTypeError("Origin and/or normal must be x,y,z")


    parser = argparse.ArgumentParser(
         prog="create_raster",
         description="""Create a raster file on a structured grid from vtu data on unstructured grid."""
         ) 
    parser.add_argument(
            '--resolution',
            help="Set the resolution of the XY. Default is 100m",
            type=float,
            default=100
            )
    parser.add_argument(
             '--mask_file',
             metavar='mask_file',
             nargs=1,
             default=["no_mask"],
             help='A NETCDF mask. 1 is where you want data, 0 is where you dont'
             )
    parser.add_argument(
            '--format', 
            metavar='format',
            help='The output file format. Default GTiff. Use GDAL conventions.',
            default='GTiff'
            )
    parser.add_argument(
            '--epsg',
            metavar='epsg',
            help='EPSG code for output projection. Default is 32630 - UTM30 North',
            default="32630",
            )
    parser.add_argument(
            'variable', 
            metavar='variable',
            help='Variable name'
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            help='The input pvtu/vtu file'
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            help='The output raster file. Default is geotiff.'
            )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    args = parser.parse_args()
    verbose = args.verbose
    resolution = args.resolution
    file_format = args.format
    proj_code = args.epsg
    input_file = args.input_file
    output_file = args.output_file
    variable = args.variable
    
    xi = []
    yi = []
    zi = []
    index_1 = 0
    index_2 = 1
    x_axis = "X"
    y_axis = "Y"
    vtu_files = []
    path = os.path.dirname(input_file)
    # read in vtu
    if input_file.endswith("pvtu"):
        # get vtus from pvtu file. They are in lines such as:
        # <Piece Source="restratA-np64-adapt-C_99/restratA-np64-adapt-C_99_0.vtu" />
        # As PVTU is XML, parse as such and grab the Piece elements
        xml_root = etree.parse(input_file,xml_parser)
        find = etree.XPath("//Piece")
        peices = find(xml_root)
        for p in peices:
            name = p.attrib['Source']
            vtu_files.append(os.path.join(path,name))
    elif input_file.endswith("vtu"):
        vtu_files.append(input_file)
        
    #for each vtu, grab any slice data 
    # We could parallelise this bit and it saves memory for large runs
    i = 0
    for v in vtu_files:
        if (verbose):
            print v
        # grab the number
        num = i

        # Start by loading some data.
        reader=vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName(v)
        reader.Update()
        grid=reader.GetOutput()
        grid.GetPointData().SetActiveScalars(variable)
        d = grid.GetPointData().GetScalars()        
        d.GetNumberOfTuples()
        # extract x, y, z data
        slice_data = np.array([d.GetTuple(i) for i in range(d.GetNumberOfTuples())])
        coords = []
        for i in range(0,grid.GetNumberOfPoints()):
            coords.append(grid.GetPoint(i))
        coords = np.array(coords)
        xi.extend(coords[:,index_1])
        yi.extend(coords[:,index_2])
        zi.extend(slice_data[:,0])
        
    xi = np.array(xi)
    yi = np.array(yi)
    zi = np.array(zi)
    #print(xi)
    #print(yi)
    #print(zi)
    # use meshgrid and griddata to create a regular grid of the correct resolution
    X, Y = np.meshgrid(np.linspace( xi.min(), xi.max(), (xi.max()-xi.min())/resolution), 
                       np.linspace( yi.min(), yi.max(), (yi.max()-yi.min())/resolution)
                       )
    #Z = griddata((xi, yi), zi, (X, Y))



    # using gdal is not working, so calling gmt surface 
    # save to temp file
    tmpf, tmpfile = tempfile.mkstemp()
    with open(tmpfile,"w") as f:
        writer = csv.writer(f, delimiter=" ")
        for x,y,z in zip(xi,yi,zi):
            writer.writerow([str(x), str(y), str(z)])
        
    call(["gmt", "surface", "-G"+output_file, 
                            "-R"+str(X.min())+"/"+str(X.max())+"/"+str(Y.min())+"/"+str(Y.max()),
                            "-I"+str(resolution),
                            tmpfile,
                            ])



    # save as raster
    #driver = gdal.GetDriverByName(file_format)
    #metadata = driver.GetMetadata()
    #if not metadata.get(gdal.DCAP_CREATE) == "YES":
    #    print("Driver {} doesn't support Create() method. Use a different format".format(file_format))

    #dst_ds = driver.Create(output_file, xsize=X.size, ysize=Y.size,
    #                   bands=1, eType=gdal.GDT_Float32)
    #dst_ds.SetGeoTransform([X.min(), resolution, 0, Y.min(), 0, resolution])
    #srs = osr.SpatialReference()
    #srs.SetWellKnownGeogCS(proj_code)
    #dst_ds.SetProjection(srs.ExportToWkt())
    #dst_ds.GetRasterBand(1).WriteArray(Z)
    ## Once we're done, close properly the dataset
    #dst_ds = None


if __name__ == "__main__":
    main()
