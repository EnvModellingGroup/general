#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import math
from fluidity_tools import stat_parser
import matplotlib
import argparse
import glob
import numpy

def main():

    parser = argparse.ArgumentParser(
         prog="plot wave gauges",
         description="""Plot detectors for multilpe fluidity runs"""
    )
    parser.add_argument(
        '-v', 
        '--verbose', 
        action='store_true', 
        help="Verbose output: mainly progress reports.",
        default=False
    )
    parser.add_argument(
        '-l', 
        '--labels', 
        help="What to call the Fluidity data",
        required=True,
        nargs='+'
    )
    parser.add_argument(
        '-g', 
        '--greyscale', 
        help="Produce greyscale plots",
        required=False,
        action='store_true',
        default=False
    )
    parser.add_argument(
        'output_file',
        metavar='output_file',
        help='The output file stub. A new figure will be created for each detector.'
    )
    parser.add_argument(
        'detector_files',
        nargs="+",
        metavar='detector_files',
        help='The detector input file stubs to take into account checkpointed detectors'
    )

    args = parser.parse_args()
    verbose = args.verbose    
    output_file = args.output_file
    det_files = args.detector_files
    labels = args.labels
    grey = args.greyscale

    if (grey):
        colours = [
            'k',
            '0.75',
            '0.5',
            'k-.',
            'k:',
            '0.25',
                ]
    else:
        colours = [
            'r',
            'b',
            'g',
            'k',
            'DarkBlue',
            'Olive',
            'DarkGoldenRod',
                ]
    params = {
      'legend.fontsize': 7,
      'xtick.labelsize': 7,
      'ytick.labelsize': 7,
      'axes.labelsize' : 7,
      'text.fontsize' : 7,
      'figure.subplot.left' : 0.18,
      'figure.subplot.top': 0.82,
      'figure.subplot.right': 0.95,
      'figure.subplot.bottom': 0.15,
      'text.usetex' : True
        }
    plt.rcParams.update(params)

    total_dets = 34
 
    free_surfaces = []
    times = []
    d = 0
    for dfile in det_files:
        filelist = glob.glob( dfile+"*.detectors")
        filelist.sort()
        i = 0
        for fl in filelist:
            stat=stat_parser( fl )
            d_no = 0
            for det in range(1,total_dets+1):
                det_str="WaveDetectors_%(#)02d" %{"#": det}
                fs = stat['Fields']['FreeSurface'][det_str]
                t = stat['ElapsedTime']['value']
                t = t/60.0/60.0
                if i == 0:
                    free_surfaces.append(fs)
                    times.append(t)
                else:
                    index = 0
                    for tt in t:
                        if tt > times[d_no+d*ndets][-1]:
                            break
                        index += 1
                    free_surfaces[d_no+d*ndets] = numpy.append(free_surfaces[d_no+d*ndets],fs[index:-1])
                    times[d_no+d*ndets] = numpy.append(times[d_no+d*ndets],t[index:-1])
                d_no += 1
            i += 1
        d += 1

    i = 0
    for det in range(1,total_dets+1):
        fig_summary = plt.figure(figsize=(3.0,2.5),dpi=180)
        fig_summary.figurePatch.set_alpha(0.5)
        ax = fig_summary.add_subplot(111)
        ax.axesPatch.set_alpha(1.0) 
        det_str="WaveDetectors_%(#)02d" %{"#": det}
        d = 0
        for dfile in det_files:
            plt.plot(times[i+d*ndets],free_surfaces[i+d*ndets], colours[d], lw=1,label=labels[d])
            d+=1
        plt.xlabel("Time (hrs)")
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.295),
          ncol=2, fancybox=True, shadow=True)
        plt.ylabel("Free Surface (m)")

        plt.savefig(output_file+"det_"+str(det)+".pdf", dpi=90)
        i+=1
    
    

if __name__ == "__main__":
    main()
