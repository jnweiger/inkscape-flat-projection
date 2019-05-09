#! /usr/bin/python
#
# Zsort is only done for the rim.
# - the general 3d face sorting problem can be reduced to a 2d problem as all faces span between two parallel planes.
# - Each quad-face can be represented by a two-point line in 2d.
# - We need to find a 2d rotation that so that the eye vector is exactly downwards in 2d.
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

test_zsort = [
  ((1,1), (5,3), "near" ),
  ((2,4), (10,2), "far" ),
  ((3,3), (4,3), "mid" ),
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


def cmp2d(g1, g2):
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
    if g1[0][1]-eps < y: return -1
    if g1[0][1]+eps > y: return 1
  # 
  y = y_at_x(g2p, g2v, g1[1][0])
  if y is not None:
    if g1[1][1]-eps < y: return -1
    if g1[1][1]+eps > y: return 1
  #
  return 0

k = functools.cmp_to_key(cmp2d)

print(sorted(test_zsort, key=k))

