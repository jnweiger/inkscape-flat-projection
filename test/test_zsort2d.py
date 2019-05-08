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

test_zsort = [
  ((1,1), (5,3), "near" ),
  ((2,4), (10,2), "far" ),
  ((3,3), (4,3)), "mid" ),
]
