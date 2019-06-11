#! /usr/bin/python
#
# Zsort is only done for the rim.
# - the general 3d face sorting problem can be reduced to a 2D problem as all faces span between two parallel planes.
# - Each quad-face can be represented by a two-point line in 2D.
# - We need to find a 2D rotation that so that the eye vector is exactly downwards in 2D.
# - rotate all faces.
# - comparison:
#   test all 4 endpoints:
#     - if an eye-vector from an end-point pierces the other line. We have a sort criteria.
#     - if all 4 eye vectors are unobstructed, keep sort order as is.
# - lines:
#   * Each quad-face starts with having 4 lines attached.
#   * no sorting is done for these lines. They are drawn when the face is drawn (exactly before the face)
#   * lines in Z direction can be eliminated as duplicate lines:
#     - if faces share an endpoint, there is a duplicate line at this end point.
#     - we remove the line from the face that is sorted below.
#
# References: https://docs.python.org/3.3/howto/sorting.html
#
# We only have a partial ordering. Thus Schwarzian transform cannot be used.
#
# For best compatibility with python2 and python3 we choose the method using
# functools.cmp_to_key() with an old style cmp parameter function.

from __future__ import print_function
import functools
import numpy as np

test_zsort =[
 [np.array([-226.00871524, -259.85624955]), np.array([-101.37448199, -345.03852612]), 0],
 [np.array([-101.37448199, -345.03852612]), np.array([-112.40988062, -218.46637541]), 1],
 [np.array([-112.40988062, -218.46637541]), np.array([-107.44083619, -217.98201708]), 2],
 [np.array([-107.44083619, -217.98201708]), np.array([ -53.10920854, -331.13263256]), 3],
 [np.array([ -53.10920854, -331.13263256]), np.array([ -14.86458452, -250.7629054 ]), 4],
 [np.array([ -14.86458452, -250.7629054 ]), np.array([  12.65268772, -254.9439152 ]), 5],
 [np.array([  12.65268772, -254.9439152 ]), np.array([  -4.35756492, -343.22291411]), 6],
 [np.array([  -4.35756492, -343.22291411]), np.array([ 117.00115031, -253.43573836]), 7],
 [np.array([ 117.00115031, -253.43573836]), np.array([ -42.77635704, -423.45178387]), 8],
 [np.array([ -42.77635704, -423.45178387]), np.array([ 181.81204591, -360.99010602]), 9],
 [np.array([ 181.81204591, -360.99010602]), np.array([  45.72476476, -426.33524789]), 10],
 [np.array([  45.72476476, -426.33524789]), np.array([ 184.16334766, -486.54123274]), 11],
 [np.array([ 184.16334766, -486.54123274]), np.array([  33.63447578, -475.08688483]), 12],
 [np.array([  33.63447578, -475.08688483]), np.array([ 123.42310986, -596.44690958]), 13],
 [np.array([ 123.42310986, -596.44690958]), np.array([  -1.21257712, -511.26332764]), 14],
 [np.array([  -1.21257712, -511.26332764]), np.array([  15.8672913 , -661.25650234]), 15],
 [np.array([  15.8672913 , -661.25650234]), np.array([ -49.47785057, -525.16922119]), 16],
 [np.array([ -49.47785057, -525.16922119]), np.array([-109.68384285, -663.60779741]), 17],
 [np.array([-109.68384285, -663.60779741]), np.array([ -98.2294875 , -513.07893221]), 18],
 [np.array([ -98.2294875 , -513.07893221]), np.array([-219.58951226, -602.86756629]), 19],
 [np.array([-219.58951226, -602.86756629]), np.array([-134.40447941, -478.23318215]), 20],
 [np.array([-134.40447941, -478.23318215]), np.array([-284.39910502, -495.31174773]), 21],
 [np.array([-284.39910502, -495.31174773]), np.array([-148.31182387, -429.96660586]), 22],
 [np.array([-148.31182387, -429.96660586]), np.array([-286.74894769, -369.76191775]), 23],
 [np.array([-286.74894769, -369.76191775]), np.array([-136.2215282 , -381.21496149]), 24],
 [np.array([-136.2215282 , -381.21496149]), np.array([-226.00871524, -259.85624955]), 25],
 [np.array([ -40.12165267, -336.57095179]), np.array([ -64.34233908, -363.54431832]), 26],
 [np.array([ -64.34233908, -363.54431832]), np.array([ -32.33208449, -392.28786938]), 27],
 [np.array([ -32.33208449, -392.28786938]), np.array([  -8.11139808, -365.31450285]), 28],
 [np.array([  -8.11139808, -365.31450285]), np.array([ -40.12165267, -336.57095179]), 29],
# [np.array([-106.65184449, -409.53274542]), np.array([-130.87212346, -436.50565821]), 30],
# [np.array([-130.87212346, -436.50565821]), np.array([ -61.82953137, -498.50233074]), 31],
# [np.array([ -61.82953137, -498.50233074]), np.array([ -37.60925239, -471.52941796]), 32],
# [np.array([ -37.60925239, -471.52941796]), np.array([-106.65184449, -409.53274542]), 33],
# [np.array([ -73.14606261, -373.34773047]), np.array([ -97.36634158, -400.32064325]), 34],
# [np.array([ -97.36634158, -400.32064325]), np.array([ -65.35569453, -429.06454673]), 35],
# [np.array([ -65.35569453, -429.06454673]), np.array([ -41.13541555, -402.09163395]), 36],
# [np.array([ -41.13541555, -402.09163395]), np.array([ -73.14606261, -373.34773047]), 37]
]


eps = 1e-100

def y_at_x(gp, gv, x):
  dx = x-gp[0]
  if abs(gv[0]) < eps:
    return None
  s = dx/gv[0]
  if s < 0.0 or s > 1.0:
    return None
  return gp[1]+s*gv[1]


def cmp2D(g1, g2):
  """
  returns -1 if g1 sorts in front of g2
  returns 1  if g1 sorts in behind g2
  returns 0  if there was no clear decision
  """
  # convert g1 into point and vector:
  g1p = g1[0]
  g1v = (g1[1][0] - g1[0][0], g1[1][1] - g1[0][1])
  #
  y = y_at_x(g1p, g1v, g2[0][0])
  if y is not None:
    if y < g2[0][1]-eps: return -1
    if y > g2[0][1]+eps: return 1
  #
  y = y_at_x(g1p, g1v, g2[1][0])
  if y is not None:
    if y < g2[1][1]-eps: return -1
    if y > g2[1][1]+eps: return 1
  #
  g2p = g2[0]
  g2v = (g2[1][0] - g2[0][0], g2[1][1] - g2[0][1])
  y = y_at_x(g2p, g2v, g1[0][0])
  if y is not None:
    if g1[0][1]+eps < y: return -1
    if g1[0][1]-eps > y: return 1
  #
  y = y_at_x(g2p, g2v, g1[1][0])
  if y is not None:
    if g1[1][1]+eps < y: return -1
    if g1[1][1]-eps > y: return 1
  #
  ## non-overlapping. keep the index order.
  #if g1[2] == g2[2]: return 0
  #if g1[2] <  g2[2]: return -1
  #return 1
  return None   # non-comparable pair in the poset. sorted() would take that as less than aka -1


k = functools.cmp_to_key(cmp2D)

for p in test_zsort:
  print(p)

print("sorted:")

for p in sorted(test_zsort, key=k):
  print(p)

