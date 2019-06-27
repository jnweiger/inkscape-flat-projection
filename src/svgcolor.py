#! /usr/bin/python
#
# 'yellowgreen': '#9acd32'

from __future__ import print_function
import simplestyle

class SvgColor:
    """ Manipulate color strings for svg style attributes """
    def __init__(self, str):
        if type(str) == list or type(str) == tuple:
           self._rgb = list(str)
        else:
           self._rgb = list(simplestyle.parseColor(str))

    def _rgb_to_hsl(self, rgb):
        (r, g, b) = (float(rgb[0]), float(rgb[1]), float(rgb[2]))
        rgb_max = max (max (r, g), b)
        rgb_min = min (min (r, g), b)
        delta = rgb_max - rgb_min
        hsl = [0.0, 0.0, 0.0]
        hsl[2] = (rgb_max + rgb_min)/2.0
        if delta == 0:
            hsl[0] = 0.0
            hsl[1] = 0.0
        else:
            if hsl[2] <= 0.5:
                hsl[1] = delta / (rgb_max + rgb_min)
            else:
                hsl[1] = delta / (2 - rgb_max - rgb_min)
            if r == rgb_max:
                hsl[0] = (g - b) / delta
            else:
                if g == rgb_max:
                    hsl[0] = 2.0 + (b - r) / delta
                else:
                    if b == rgb_max:
                        hsl[0] = 4.0 + (r - g) / delta
            hsl[0] = hsl[0] / 6.0
            if hsl[0] < 0:
                hsl[0] = hsl[0] + 1
            if hsl[0] > 1:
                hsl[0] = hsl[0] - 1
        return hsl

    def _hue_2_rgb(self, v1, v2, h):
        if h < 0:
            h += 6.0
        if h > 6:
            h -= 6.0
        if h < 1:
            return v1 + (v2 - v1) * h
        if h < 3:
            return v2
        if h < 4:
            return v1 + (v2 - v1) * (4 - h)
        return v1

    def _hsl_to_rgb(self, hsl):
        (h, s, l) = (hsl[0], hsl[1], hsl[2])
        rgb = [0, 0, 0]
        if s == 0:
            rgb[0] = l
            rgb[1] = l
            rgb[2] = l
        else:
            if l < 0.5:
                v2 = l * (1 + s)
            else:
                v2 = l + s - l*s
            v1 = 2*l - v2
            rgb[0] = self._hue_2_rgb (v1, v2, h*6 + 2.0)
            rgb[1] = self._hue_2_rgb (v1, v2, h*6)
            rgb[2] = self._hue_2_rgb (v1, v2, h*6 - 2.0)
        return rgb

    def _clamp_rgb(self, rgb):
        rgb[0] = min(max(rgb[0], 0), 255)
        rgb[1] = min(max(rgb[1], 0), 255)
        rgb[2] = min(max(rgb[2], 0), 255)
        return rgb

    def rgb(self):
        return self._rgb

    def hsl(self):
        return self._rgb_to_hsl(self._rgb)

    def adjust_light(self, adjust):
        """ visible adjustments are +/- 10, adust=255 produces white, adjust=-255 produces black """
        hsl = self._rgb_to_hsl(self._rgb)
        hsl[2] += adjust
        self._rgb = self._hsl_to_rgb(hsl)
        return self._rgb

    def __repr__(self):
        rgb = self._clamp_rgb(self._rgb)
        return "#%02x%02x%02x" % (int(rgb[0]+.5), int(rgb[1]+.5), int(rgb[2]+.5))

    def __str__(self):
        return self.__repr__()


if __name__ == '__main__':
  str = '#9acd32'
  c = simplestyle.parseColor(str)

  for i in range(16):
    rgb=(8*i+i, 16*i+i, 16*i+i)
    c = SvgColor(rgb)
    print('color: ', c, c.rgb(), c.hsl())
    c.adjust_light(+20)
    print('                       l+20 -> ', c, c.rgb())
