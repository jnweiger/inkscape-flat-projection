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
  # non-overlapping. keep the index order.
  if g1[2] == g2[2]: return 0
  if g1[2] <  g2[2]: return -1
  return 1


def genRx(theta):
  "A rotation matrix about the X axis. Example: Rx = genRx(np.radians(30))"
  c, s = np.cos(theta), np.sin(theta)
  return np.array( ((1, 0, 0), (0, c, s), (0, -s, c)) )


def genRy(theta):
  "A rotation matrix about the Y axis. Example: Ry = genRy(np.radians(30))"
  c, s = np.cos(theta), np.sin(theta)
  return np.array( ((c, 0, -s), (0, 1, 0), (s, 0, c)) )


def genRz2D(theta):
  "A 2D rotation matrix about the Z axis. Example: Rz2D = genRz2D(np.radians(30))"
  c, s = np.cos(theta), np.sin(theta)
  return np.array( ((c, s), (-s, c)) )


def phi2D(R):
  """
  Given a 3D rotation matrix R, we compute the angle phi projected in the
  x-y plane of point 0,0,1 relative to the negative Y axis.
  """
  (x2d_vec, y2d_vec, dummy) = np.matmul( [0,0,-1], R )
  if abs(x2d_vec) < eps:
    if abs(y2d_vec) < eps: return 0.0
    phi = 0.5*np.pi
    if y2d_vec < 0:
      phi = -0.5*np.pi
    else:
      phi = 0.5*np.pi
  else:
    phi = np.arctan(y2d_vec/x2d_vec)
  if x2d_vec < 0:       # adjustment for quadrant II and III
    phi += np.pi
  elif y2d_vec < 0:     # adjustment for quadrant IV
    phi += 2*np.pi
  phi += 0.5*np.pi      # adjustment for starting with 0 deg at neg Y-axis.
  if phi >= 2*np.pi:
    phi -= 2*np.pi      # adjustment to remain within 0..359.9999 deg
  return phi


def dphi2D(x2d_vec, y2d_vec):
  """ testing code only """
  if abs(x2d_vec) < eps:
    if abs(y2d_vec) < eps: return 0.0
    if y2d_vec < 0:
      phi = -0.5*np.pi
    else:
      phi = 0.5*np.pi
  else:
    phi = np.arctan(y2d_vec/x2d_vec)
  if x2d_vec < 0:       # adjustment for quadrant II and III
    phi += np.pi
  elif y2d_vec < 0:     # adjustment for quadrant IV
    phi += 2*np.pi
  phi += 0.5*np.pi      # adjustment for starting with 0 deg at neg Y-axis.
  if phi >= 2*np.pi:
    phi -= 2*np.pi      # adjustment to remain within 0..359.9999 deg
  return np.degrees(phi)


# Dimetric 7,42 transformation
Ry = genRy(np.radians(69.7))
Rx = genRx(np.radians(19.4))

## Isometric transformation
# Ry = genRy(np.radians(45))
# Rx = genRx(np.radians(35.26439))

R = np.matmul(Ry, Rx)

# prepare a rotated version of the original two-D line set,
# so that cmp2D can sort towards negaive Y-Axis
Rz2D = genRz2D(phi2D(R))
rotated = []
for i in range(len(test_zsort)):
  l = test_zsort[i]
  rotated.append((np.matmul(l[0], Rz2D), np.matmul(l[1], Rz2D), i)+l[2:])

k = functools.cmp_to_key(cmp2D)

print(test_zsort)
print(np.degrees(phi2D(R)))
print(rotated, "\n\n")
print(sorted(rotated, key=k))

