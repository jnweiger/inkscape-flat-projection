#! /usr/bin/python3
#
# FROM:
# - https://stackoverflow.com/questions/5666222/3d-line-plane-intersection
# Based on http://geomalgorithms.com/a05-_intersect-1.html

from __future__ import print_function
import numpy as np

ZCMP_EPS = 0.000001

zcmp_out = open('/dev/tty', 'w')

def _zcmp_f(a, b):
    " comparing floating point is hideous. "
    d = a - b
    if d > ZCMP_EPS: return 1
    if d < -ZCMP_EPS: return -1
    return 0


def _xyz_eq(a, b):
    " Returns True, if all three coordinates are within ZCMP_EPS "
    if abs(a[0]-b[0]) > ZCMP_EPS: return False
    if abs(a[1]-b[1]) > ZCMP_EPS: return False
    if abs(a[2]-b[2]) > ZCMP_EPS: return False
    return True


def _xy_cdiff(a,b):
   "Returns the cartesian length of the difference of two 2d vectors. "
   return abs(a[0]-b[0]) + abs(a[1]-b[1])


class ZSort():
    """ Higher Z coordinates point away from the camera. We draw them first, as we call sort with reverse=True. """


    ray_direction = np.array([0,0,1])


    def _z_point_in_face(self, pt):
        """ check if pt is inside the face.
            If the vector from a known point on the face to the pt has a zero dot product with the normal,
            then pt is on the plane.
        """
        d = np.dot(self.face_normal, pt-self.face_point)
        if abs(d) < ZCMP_EPS: return True
        return False


    def _z_ray_hit_face(self, xyz):
        """ project a ray along the global ray_direction (z-axis) from point xyz. Compute where the ray intersects with the face. """
        pt = np.array(xyz)
        if abs(self.face_ndotu) < ZCMP_EPS:
            print ("z-ray is parallel to face or within.")
            if self._z_point_in_face(pt):
              return pt
            return None
        w = pt - self.face_point
        si = -self.face_normal.dot(w) / self.face_ndotu
        psi = w + si * self.ray_direction + self.face_point
        return psi


    def _zcmp_22(self, oth):
        """ simple z-average comparison. We return -1 for the larger z, so that this is drawn first. """
        return _zcmp_f(self.bbmin[2]+self.bbmax[2], oth.bbmin[2]+oth.bbmax[2])


    def _zcmp_24(self, oth):
        """ A line is an edge of the face, it is technically of equal depth, but we put it in front for visibility.
            A line is an edge of a face, if bbmin or bbmax of face and line are identical.
            Otherwise we take the first point of the line, and use the face normal to decide stacking.
        """
        if _xyz_eq(self.bbmin, oth.bbmin): return 1
        if _xyz_eq(self.bbmax, oth.bbmax): return 1
        psi = oth._z_ray_hit_face(self.data[0])
        if (psi is None or
            psi[0] < oth.bbmin[0] or psi[0] > oth.bbmax[0] or
            psi[1] < oth.bbmin[1] or psi[1] > oth.bbmax[1]):
            return self._zcmp_22(oth)
        return _zcmp_f(psi[2], self.data[0][2])


    def _zcmp_42(self, oth):
        return oth._zcmp_24(self)


    def _zcmp_44(self, oth):
        """ Compare face with face.
            If (x,y) bounding boxes overlap, find one corner of one face with (x,y) inside the other face.
            We implement this, by finding a corner point of one face that is closest to the center of the other.
            Compute the z-distance at this corner using normals.
            If bounding boxes do not overlap,  return _zcmp_22() instead.
        """
        # sort all x coordinates, sort all y coordinates

        min_idx_in_self = True
        min_idx = -1
        min_dist = 1e999        # inf
        print("_zcmp_44: len: ", len(self.data), len(oth.data), oth, file=zcmp_out)

        other_center = oth.xy_center
        other_cartesian_radius = oth.yx_crad
        for i in range(4):
            d = _xy_cdiff(self.data[i], other_center)
            if d < min_dist and d < other_cartesian_radius:
                min_dist = d;
                min_idx = i;
        other_center = self.xy_center
        other_cartesian_radius = self.xy_crad
        for i in range(4):
            d = _xy_cdiff(oth.data[i], other_center)
            if d < min_dist and d < other_cartesian_radius:
                min_dist = d;
                min_idx = i;
                min_idx_in_self = False

        if min_idx == -1:
            # No overlap found. Return a dummy.
            return self._zcmp_22(oth)

        if min_idx_in_self == True:
            # our best point is self.data[min_idx]
            psi = oth._z_ray_hit_face(self.data[min_idx])
            if psi is None: return self._zcmp_22(oth)
            return _zcmp_f(psi[2], self.data[min_idx][2])
        else:
            # our best point is oth.data[min_idx]
            psi = self._z_ray_hit_face(oth.data[min_idx])
            if psi is None: return self._zcmp_22(oth)
            return _zcmp_f(psi[2], oth.data[min_idx][2])

    def __repr__(self):
        s = "{ bbmin=%s, bbmax=%s, xy_crad=%s, xy_center=%s, face_normal=%s, face_ndotu=%s, data=%s, attr=%s }" % (
          self.bbmin, self.bbmax, 
          getattr(self, 'xy_crad', None),
          getattr(self, 'xy_center', None),
          getattr(self, 'face_normal', None),
          getattr(self, 'face_ndotu', None),
          self.data, getattr(self, 'attr', None) )
        return s

    def __init__(self, data, attr=None):
        self.xy_crad = "ZCMP_EPS + 0.5 *_xy_cdiff(self.bbmax, self.bbmin)"
        if len(data) == 2:
            """ A line of two points.
                We place the zcmp_22() and zcmp_24() methods into the slots.
                We don't compute a normal.
            """
            self.zcmp_2 = self._zcmp_22
            self.zcmp_4 = self._zcmp_24
            self.bbmin = ( min(data[0][0], data[1][0]),
                           min(data[0][1], data[1][1]),
                           min(data[0][2], data[1][2]) )
            self.bbmax = ( max(data[0][0], data[1][0]),
                           max(data[0][1], data[1][1]),
                           max(data[0][2], data[1][2]) )
        else:
            """ A face of four corners """
            self.zcmp_2 = self._zcmp_42
            self.zcmp_4 = self._zcmp_44
            self.bbmin = ( min(data[0][0], data[1][0], data[2][0], data[3][0]),
                           min(data[0][1], data[1][1], data[2][1], data[3][1]),
                           min(data[0][2], data[1][2], data[2][2], data[3][2]) )
            self.bbmax = ( max(data[0][0], data[1][0], data[2][0], data[3][0]),
                           max(data[0][1], data[1][1], data[2][1], data[3][1]),
                           max(data[0][2], data[1][2], data[2][2], data[3][2]) )
            self.xy_center = [ 0.5 * (self.bbmax[0] + self.bbmin[0]), 0.5 * (self.bbmax[1] + self.bbmin[1]) ]
            self.xy_crad = ZCMP_EPS + 0.5 *_xy_cdiff(self.bbmax, self.bbmin)
            self.face_point = np.array(data[0])
            self.face_normal = np.cross(np.array(data[1])-self.face_point, np.array(data[2])-self.face_point)
            self.face_ndotu = self.face_normal.dot(self.ray_direction)
        self.data = data
        self.attr = attr
        print("__init__", self, "xy_crad", self.xy_crad, file=zcmp_out)


    # https://wiki.python.org/moin/HowTo/Sorting#The_Old_Way_Using_the_cmp_Parameter
    # In python3, the simple cmp operator was banned in favour of a silly code repetition
    # interface of six almost identical operators.
    def __lt__(self, oth):
        if len(oth.data) > 2: return self.zcmp_4(oth) < 0
        else:                 return self.zcmp_2(oth) < 0
    def __gt__(self, oth):
        if len(oth.data) > 2: return self.zcmp_4(oth) > 0
        else:                 return self.zcmp_2(oth) > 0
    def __eq__(self, oth):
        if len(oth.data) > 2: return self.zcmp_4(oth) == 0
        else:                 return self.zcmp_2(oth) == 0
    def __le__(self, oth):
        if len(oth.data) > 2: return self.zcmp_4(oth) <= 0
        else:                 return self.zcmp_2(oth) <= 0
    def __ge__(self, oth):
        if len(oth.data) > 2: return self.zcmp_4(oth) >= 0
        else:                 return self.zcmp_2(oth) >= 0
    def __ne__(self, oth):
        if len(oth.data) > 2: return self.zcmp_4(oth) != 0
        else:                 return self.zcmp_2(oth) != 0

    @staticmethod
    def cmp(a,b):
        print("cmp ", len(a.data), a.data[:2], len(b.data), b.data[:2], file=zcmp_out)
        if len(b.data) > 2:
            r = a.zcmp_4(b)
            print(" ----> ", r, file=zcmp_out)
            return r 
        else:
            r = a.zcmp_2(b)
            print(" --> ", r, file=zcmp_out)
            return r

