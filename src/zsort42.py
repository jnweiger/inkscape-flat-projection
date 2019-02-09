ZCMP_EPS = 0.000001

def _zcmp_f(a, b):
    " comparing floating point is hideous. "
    d = a - b
    if d > ZCMP_EPS: return 1
    if d < -ZCMP_EPS: return -1
    return 0

class ZSort():
    def _zcmp_22(self, oth):
        return _zcmp_f(self.zmin+self.zmax, oth.zmin+oth.zmax)

    def _zcmp_24(self, oth):

    def __init__(self, data):
        if len(data) == 2:
            """ A line.
                We place the zcmp_22() and zcmp_24() methods into the slots.
                We don't compute a normal.
            """
            zcmp_2 = _zcmp_22
            zcmp_4 = _zcmp_24
            xmin = min(data[0][0],data[1][0])
            xmax = max(data[0][0],data[1][0])
            ymin = min(data[0][1],data[1][1])
            ymax = max(data[0][1],data[1][1])
            zmin = min(data[0][2],data[1][2])
            zmax = max(data[0][2],data[1][2])

