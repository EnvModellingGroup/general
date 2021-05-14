#!/usr/bin/env python

from optparse import OptionParser
import re
import sys
import os.path
import numpy
import shapefile

#####################################################################
# Script starts here.
optparser=OptionParser(usage='usage: %prog [options] <filename>',
                       add_help_option=True,
                       description="""This takes a Gmsh 2.0 .msh ascii file """ + 
                       """and produces .node, .ele and .edge or .face files.""")

(options, argv) = optparser.parse_args()

if len(argv)<1:
    optparser.print_help()
    sys.exit(1)

if argv[0][-4:]!=".msh":
    sys.stderr.write("Mesh filename must end in .msh\n")
    optparser.print_help()
    sys.exit(1)
    

basename=os.path.basename(argv[0][:-4])

mshfile=file(argv[0], 'r')

# Header section
assert(mshfile.readline().strip()=="$MeshFormat")
assert(mshfile.readline().strip()in["2 0 8", "2.1 0 8", "2.2 0 8"])
assert(mshfile.readline().strip()=="$EndMeshFormat")

# Nodes section
while mshfile.readline().strip() !="$Nodes":
    pass
nodecount=int(mshfile.readline())

if nodecount==0:
  sys.stderr.write("ERROR: No nodes found in mesh.\n")
  sys.exit(1)

if nodecount<0:
  sys.stderr.write("ERROR: Negative number of nodes found in mesh.\n")
  sys.exit(1)

positions = []
for i in range(nodecount):
    # Node syntax
    line = mshfile.readline().split()
    # compare node id assigned by gmsh to consecutive node id (assumed by fluidity)
    if eval(line[0])!=i+1:
      print line[0], i+1
      sys.stderr.write("ERROR: Nodes in gmsh .msh file must be numbered consecutively.")
    positions.append( map(float,line[1:3]) )
positions = numpy.array(positions)

assert(mshfile.readline().strip()=="$EndNodes")

# Elements section
assert(mshfile.readline().strip()=="$Elements")
elementcount=int(mshfile.readline())

# Now loop over the elements placing them in the appropriate buckets.
edges=[]
triangles=[]
tets=[]
quads=[]
hexes=[]

for i in range(elementcount):
    
    element=mshfile.readline().split()

    if (element[1]=="1"):
        edges.append(map(int,element[-2:]+[element[3]]))
    elif (element[1]=="2"):
        triangles.append(map(int,element[-3:]+[element[3]]))
    elif(element[1]=="15"):
        # Ignore point elements
        pass
    else:
        sys.stderr.write("Unknown element type "+`element[1]`+'\n')
        sys.exit(1)
def add_to_multiline(multiline, v1, v2):
   multiline.append((positions[v1-1], positions[v2-1]))

shf = shapefile.Writer(shapefile.POLYLINE)
multiline=[]
for triangle in triangles:
  add_to_multiline(multiline, triangle[0], triangle[1])
  add_to_multiline(multiline, triangle[1], triangle[2])
  add_to_multiline(multiline, triangle[2], triangle[0])
shf.line(multiline)
# for some reason qgis insists on having at least one field
shf.field('id')
shf.record([1])
shf.save( basename )
