import vtk
import glob
import sys
import os
import scipy.stats
import math
import vtktools
from lxml import etree
from pylab import *
from fluidity_tools import stat_parser
import numpy as np
import math
import argparse
import fileinput
import pickle
from scipy.interpolate import interp1d

colours_g = ['k-',
            'k--',
            'k:',
            'k.-',
            '0.75',
            '0.5',
            '0.25']
col = ['r',
       'b',
       'g',
       'k',
       'DarkBlue',
       'Olive',
       'DarkGoldenRod']
params = {
  'legend.fontsize': 26,
  'xtick.labelsize': 26,
  'ytick.labelsize': 26,
  'font.size' : 26,
  'axes.labelsize' : 26,
  'text.fontsize' : 26,
  'figure.subplot.hspace' : 0.5,
  'text.usetex'        : True
}


def main():

    parser = argparse.ArgumentParser(
         prog="plot free surface",
         description="""Plot free surface height of a 2D simulation using either FreeSurface or multimaterial"""
    )
    parser.add_argument(
        '-v', 
        '--verbose', 
        action='store_true', 
        help="Verbose output: mainly progress reports.",
        default=False
    )
    parser.add_argument(
        '--data',
        '-d',
        metavar='data',
        help='CSV file contining data from experiments. Label is taken from column header.'
    )
    parser.add_argument(
        'output_file',
        metavar='output_file',
        help='The output file. Either PDF, SVG or PNG. CSV for saving data'
    )
    parser.add_argument(
        '--offsety',
        metavar="offsety",
        nargs="*",
        type=float,
        help="Offset of freesurface. Default is 0",
    )
    parser.add_argument(
        '--offsetx',
        metavar="offsetx",
        nargs="*",
        type=float,
        help="Offset of distance. Default is 0",
    )
    parser.add_argument(
        '-g', 
        '--grey', 
        action='store_true', 
        help="Greyscale output",
        default=False
    )
    parser.add_argument(
        '--tol',
        default=1e-4,
        type=float,
        help="Tolerance when chaining points for multimat",
    )
    parser.add_argument(
        '--cont_val',
        default=0.9,
        type=float,
        help="Contour value to use",
    )
    parser.add_argument(
        '-l',
        '--lab',
        nargs="+",
        help="Labels for the fluidity runs",
    )
    parser.add_argument(
        'twod_file',
        nargs="+",
        metavar='twod_file',
        help='The 2D (p)vtu input files'
    )

    args = parser.parse_args()
    verbose = args.verbose    
    output_file = args.output_file
    vtu_files = args.twod_file
    data_file = args.data
    offsetx = args.offsetx
    offsety = args.offsety
    cont_val = args.cont_val
    tol = args.tol
    grey = args.grey
    labels = args.lab

    if (offsetx == None):
        offsetx = []
        for f in vtu_files:
            offsetx.append(0.0)
    if (offsety == None):
        offsety = []
        for f in vtu_files:
            offsety.append(0.0)

    if grey:
        colours = colours_g
    else:
        colours = col
    if (not len(labels) == len(vtu_files)):
        print "Number of labels does not match number of inputs"
        return
    if (len(offsetx) > 0 and len(offsetx) != len(vtu_files)):
        print "Number of offset in x does not match number of inputs"
        return
    if (len(offsety) > 0 and len(offsety) != len(vtu_files)):
        print "Number of offset in y does not match number of inputs"
        return


    xs = []
    ys = []
    multimat = False
    count = 0
    for vtu_file in vtu_files:
        try:
            # check if free surface or multi-material
            # and grab free surface
            u=vtktools.vtu(vtu_file)
            fs = u.GetScalarField('FreeSurface')
        except Exception as e:
            multimat = True
            if (verbose):
                print "Detected possible Multi-Material output. Trying that"
            # first try  
            try:
                fs = u.GetScalarField('Water::FreeSurface')
                multimat = False
            except:
                x,y = getFreeSurfaceMultiMaterial(vtu_file,verbose,cont_val=cont_val,tol=tol)
                x = x - offsetx[count]
                y = y - offsety[count]

        if (not multimat):
            coords = u.GetLocations()
            x = []
            y = []
            for i in range(0,len(fs)):
                 x.append(coords[i,0])
            x = _uniquify(x)
            new_x = []
            x = sort(x)
            for cur_x in x:
                for i in range(0,len(fs)):
                    if (abs(coords[i,0] - cur_x) < 1e-8):
                        new_x.append(cur_x)
                        y.append(fs[i])
                        break
            y = np.array(y)
            x = np.array(x)
            x = x - offsetx[count]
            y = y - offsety[count]
        xs.append(x)
        ys.append(y)
        count += 1

    # load in CSV experiment/other model data
    if (not data_file == None):
        data_x,data_y,headers = load_data(data_file)

    # plot
    fig_summary = figure(figsize=(20,12),dpi=90)
    rcParams.update(params)    
    ax = fig_summary.add_subplot(111)
    i = 0
    if (not data_file == None):
        for i in range(0,len(headers)):
            if headers[i] == "Experiment":
                plot(data_x[i],data_y[i],colours[i],linestyle='',label=headers[i],marker="o",alpha='0.75')            
            else:
                f = interp1d(data_x[i], data_y[i], kind='cubic', bounds_error=False)
                plot(x,f(x),colours[i],label=headers[i],lw=4,alpha='0.75')
    if (i > 0):
        i += 1
    for data in range(len(xs)):
        plot(xs[data],ys[data],colours[i],lw=3,label=labels[data])
        i+=1
    ax.legend(loc='lower right',ncol=1, fancybox=True, shadow=True)
    xlabel('Distance (m)')
    ylabel("Free surface height (m)")
    savefig(output_file, dpi=90)


def length(x0, x1):
  return sqrt((x0[0]-x1[0])**2+(x0[1]-x1[1])**2)

time = []
t0 = 0
dt = 0.1

def getFreeSurfaceMultiMaterial(vtu_file,verbose=False,cont_val=0.9,tol=1e-4):

   data = vtktools.vtu(vtu_file)
   data.ugrid.GetPointData().SetActiveScalars('Water::MaterialVolumeFraction')
   data = data.ugrid
   contour = vtk.vtkContourFilter()
   contour.SetInput(data)
   contour.SetValue(0, cont_val)
   contour.Update()
   polydata = contour.GetOutput()

   # Find the leftmost cell and associated point.
   leftmost_cell = (0, 0, polydata.GetCell(0).GetPoints().GetPoint(0)[0])
   for cid in range(polydata.GetNumberOfCells()):
     cell = polydata.GetCell(cid)

     if(cell.GetPoints().GetPoint(0)[0]<leftmost_cell[2]):
       leftmost_cell = (cid, 0, cell.GetPoints().GetPoint(0)[0])
     elif(cell.GetPoints().GetPoint(1)[0]<leftmost_cell[2]):
       leftmost_cell = (cid, 1, cell.GetPoints().GetPoint(1)[0])

   if (verbose):
       print "\tCreating chains"
   # Create chain of lines.
   chain = [leftmost_cell[0:2], ] # list will contain all the lines both orientated and in order.
   worklist = range(polydata.GetNumberOfCells()) # this is our worklist - cells that we have to compare against.
   worklist.remove(leftmost_cell[0])

   while len(worklist)>0:
     last_line = chain[len(chain)-1]
     last_pnt = (last_line[1]+1)%2
     hitcnt = 0
     for cid in worklist:
       if length(polydata.GetCell(cid).GetPoints().GetPoint(0), polydata.GetCell(last_line[0]).GetPoints().GetPoint(last_pnt))<tol:
         chain.append((cid, 0))
         worklist.remove(cid)
         hitcnt = hitcnt+1
         break
       elif length(polydata.GetCell(cid).GetPoints().GetPoint(1), polydata.GetCell(last_line[0]).GetPoints().GetPoint(last_pnt))<tol:
         chain.append((cid, 1))
         worklist.remove(cid)
         hitcnt = hitcnt+1
         break

     if hitcnt==0 and verbose:
       print "INFO: leaving because of no more hits", len(worklist)
       break

   x = []
   y = []
   for link in chain:
     x.append(polydata.GetCell(link[0]).GetPoints().GetPoint(link[1])[0])
     y.append(polydata.GetCell(link[0]).GetPoints().GetPoint(link[1])[1])
   x.append(polydata.GetCell(chain[-1][0]).GetPoints().GetPoint((chain[-1][1]+1)%2)[0])
   y.append(polydata.GetCell(chain[-1][0]).GetPoints().GetPoint((chain[-1][1]+1)%2)[1])
 
   return np.array(x), np.array(y)

def load_data(filename):
    """ Load in a tab-sep file where each column pair represents a dataset
    """
    import csv

    data_matrix = []
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in csvreader:
            if (i == 0): #header
                headers = row[1::2]
                i += 1
    x = []
    y = []
    for j in range(0,len(headers)*2,2): 
        temp_x = []
        temp_y = []
        with open(filename, 'r') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in csvreader:
                if (i == 0):
                    i +=1
                    continue
                try:
                    temp_x.append(float(row[j]))
                    temp_y.append(float(row[j+1]))
                except ValueError:
                    pass
                i+=1
        x.append(temp_x)
        y.append(temp_y)

    return x,y,headers

def _uniquify(l):
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()

if __name__ == "__main__":
    main()
