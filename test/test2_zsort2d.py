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
# - There is no way, we can extend the poset to a total ordered set. E.g. given a line and its mirror image about the y-axis. Their order depends only on how they are connected.
#
# ------------------------------------------------
# References: https://en.wikipedia.org/wiki/Topological_sorting
#
# Sorting algorithm ideas:
#  * X-coordinates.
#    - Put all x-coordinates in a list, sort them.
#    - Scan through the list from left to right. For each x-position,
#      - record how lines start and end, creating the set of overlapping lines for each x-position.
#      - in every overlap-set, compute the corresponding y-coordinate. Sort the set by this y-coordinate.
#    - merge overlap sets with their neighbours.
#      - if no line spans between the two, just concatenate.
#      - if lines span across them, things get messy here. toposort?
#
#  * Insert sort.
#    - maintain a set of sorted lists, where each list remembers its last insert index.
#    - for each line:
#      - try all lists in the set:
#        - compare with the element at the last insert index.
#        - if uncomparable, continue with the next list in the set.
#        - if larger or smaller, move the index up/down in the list.
#          - repeat until the relationship inverts, or an end of the list is reached.
#          - insert there. Continue with the next list.
#    - as soon as the same entry is added to a second list, merge the two lists.
#    - this may get messy again. toposort?
#
# The insert sort actually could use any sort algorithm within the list. (silly bubble sort specified here)
# It is critical to be able to specify the last insert index as a start point for the sort algorithm.
# We have a good reason to assume the next inserted line is very often directly before or after the last one.
# This assumption is based on the fact that the lines are presented in a certain order and form a closed outline.
# ------------------------------------------------
#
# For best compatibility with python2 and python3 we choose the method using
# functools.cmp_to_key() with an old style cmp parameter function.

from __future__ import print_function
import functools
import numpy as np
try:
  # a drop in replacement that does fast inserts and slices...
  from blist import blist as list
except:
  pass


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

class PoList():
  """
  A list object that remembers its last insert point and implements a merge sort
  using an old fashioned compare function.
  """
  def __init__(self, cmp_fn=None):
    self.cmp = cmp_fn
    self.pol = list([])
    self.idx = -1
#
#
  def merge(self, other):
    """
    Try to add elemente other to the list. Returns False if it could not be compared.
    """
    if len(self.pol) == 0:
      self.pol.append(other)
      self.idx = 0
      print("initial add\t#", other)
      return True
    oidx = self.idx
    idx = oidx
    r = self.cmp(self.pol[oidx], other)  
    print("oidx", oidx, "-> ", r, "\t#", other)
    if r == None:
      # try find a comparable start position.
      for i in range(len(self.pol)):
        r = self.cmp(self.pol[i], other)
        if r is not None:
          oidx = i
          break
      # if none found, return false.
      print("scan, givng up", "\t#", other)
      return False
    if r < 0:
      idx = 0
      # it sorts before the current entry
      for i in reversed(range(oidx)):
        r = self.cmp(self.pol[i], other)
        if r is None or r > 0:
          # insert after i
          idx = i + 1
          break
      print("before\t##", self.pol[idx], "\ninsert\t#", other)
      self.pol[idx:idx] = list([other])
      self.idx = idx
    else:
      idx = len(self.pol)
      # it sorts after the current entry.
      for i in range(oidx+1, len(self.pol)):
        r = self.cmp(self.pol[i], other)
        if r is None or r < 0:
          # insert before i
          idx = i
          break
      print("after\t##", idx-1, len(self.pol))
      print("after\t##", self.pol[idx-1], "\ninsert\t#", other)
      self.pol[idx:idx] = list([other])
      self.idx = idx
 


# END of class PoList
# -------------------------------------------



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
  returns None  if there was no clear decision
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

# for p in sorted(test_zsort, key=k):
#  print(p)

a = PoList(cmp2D)
for p in test_zsort:
  a.merge(p)

for p in a.pol:
  print(p)
