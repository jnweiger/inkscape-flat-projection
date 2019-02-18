#! /usr/bin/python3
#
# CAUTION: test with python2 and python3!
#

from __future__ import print_function
import sys
import numpy as np

sys.path.append('../src/')
sys.path.append('src/')
from zsort42 import ZSort

paths3d_2 = [[[np.array([-49.45913639, -12.99941199,  36.91383111]), np.array([-49.45913639, -50.80199365,  23.60144065])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:#000000;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00'], [[np.array([-49.45913639, -12.99941199,  36.91383111]), np.array([-49.45913639, -50.80199365,  23.60144065]), np.array([ 13.95112475, -63.64655184,  60.07554057]), np.array([ 13.95112475, -25.84397017,  73.38793103]), np.array([-49.45913639, -12.99941199,  36.91383111])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:none;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00'], [[np.array([ 13.95112475, -25.84397017,  73.38793103]), np.array([ 13.95112475, -63.64655184,  60.07554057])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:#000000;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00'], [[np.array([ 13.95112475, -25.84397017,  73.38793103]), np.array([ 13.95112475, -63.64655184,  60.07554057]), np.array([ 41.41345232, -56.50231555,  39.78838205]), np.array([ 41.41345232, -18.69973389,  53.10077251]), np.array([ 13.95112475, -25.84397017,  73.38793103])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:none;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00'], [[np.array([ 41.41345232, -18.69973389,  53.10077251]), np.array([ 41.41345232, -56.50231555,  39.78838205])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:#000000;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00'], [[np.array([ 41.41345232, -18.69973389,  53.10077251]), np.array([ 41.41345232, -56.50231555,  39.78838205]), np.array([  5.69245127, -74.44521652,  90.740011  ]), np.array([  5.69245127, -36.64263486, 104.05240146]), np.array([ 41.41345232, -18.69973389,  53.10077251])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:none;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00'], [[np.array([  5.69245127, -36.64263486, 104.05240146]), np.array([  5.69245127, -74.44521652,  90.740011  ])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:#000000;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00'], [[np.array([  5.69245127, -36.64263486, 104.05240146]), np.array([  5.69245127, -74.44521652,  90.740011  ]), np.array([-49.45913639, -50.80199365,  23.60144065]), np.array([-49.45913639, -12.99941199,  36.91383111]), np.array([  5.69245127, -36.64263486, 104.05240146])], 'opacity:1;stroke-linejoin:round;vector-effect:none;stroke-opacity:1;fill-rule:nonzero;fill-opacity:1;stroke-dashoffset:0;stroke:none;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-width:0.2;fill:#ffff00']]

zspaths=[]
for i in paths3d_2:
  zspaths.append(ZSort(data=i[0], attr=i[1]))
  print('* ', zspaths[-1].data)
  print('  ', zspaths[-1].attr)
