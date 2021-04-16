import numpy as np
import qgis.core
import sys
import qmesh

shp_file = "../gbr_45m/mesh/45_preholocene_smooth.shp"
output_mask = "../gbr_45m/mesh/mask.shp"

#Initialising qgis API
qmesh.initialise()
#Reading in the shapefile describing the domain boundaries, and creating a gmsh file.
boundaries = qmesh.vector.Shapes()
boundaries.fromFile(shp_file)
loopShapes = qmesh.vector.identifyLoops(boundaries,
          isGlobal=False, defaultPhysID=1000,
          fixOpenLoops=True)
polygonShapes = qmesh.vector.identifyPolygons(loopShapes, smallestNotMeshedArea=50000, 
                                                                 meshedAreaPhysID = 1)
polygonShapes.writeFile(output_mask)
