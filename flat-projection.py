#! /usr/bin/python3
#
# flatproj.py -- apply a transformation matrix to an svg object
#
# (C) 2019 Juergen Weigert <juergen@fabmail.org>
# Distribute under GPLv2 or ask.
#
# recursivelyTraverseSvg() is originally from eggbot. Thank!
# inkscape-paths2openscad and inkscape-silhouette contain copies of recursivelyTraverseSvg()
# with almost identical features, but different inmplementation details. The version used here is derived from
# inkscape-paths2openscad.
#
# Dimetric 7,42: Rotate(Y, 69,7 deg), Rotate(X, 19,4 deg)
# Isometric:     Rotate(Y, 45 deg),   Rotate(X, degrees(atan(1/sqrt2)))    # 35.26439 deg
#

# Isometric transformation example:
# Ry = genRy(np.radians(45))
# Rx = genRx(np.radians(35.26439))
# np.matmul( np.matmul( [[0,0,-1], [1,0,0], [0,-1,0]], Ry ), Rx)
#   array([[-0.70710678,  0.40824829, -0.57735027],
#          [ 0.70710678,  0.40824829, -0.57735027],
#          [ 0.        , -0.81649658, -0.57735027]])
# R = np.matmul(Ry, Rx)
# np.matmul( [[0,0,-1], [1,0,0], [0,-1,0]], R )
#  -> same as above :-)
#

# python2 compatibility:
from __future__ import print_function

import sys, time
import numpy as np            # Tav's perspective extension also uses numpy.

sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):
  sys.path.append('C:\Program Files\Inkscape\share\extensions')
elif sys_platform.startswith('darwin'):
  sys.path.append('~/.config/inkscape/extensions')
else:   # Linux
  sys.path.append('/usr/share/inkscape/extensions/')


#! /usr/bin/python
#
# inksvg.py - parse an svg file into a plain list of paths.
#
# (C) 2017 juergen@fabmail.org, authors of eggbot and others.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#################
# 2017-12-04 jw, v1.0  Refactored class InkSvg from cookiecutter extension
# 2017-12-07 jw, v1.1  Added roundedRectBezier()
# 2017-12-10 jw, v1.3  Added styleDasharray() with stroke-dashoffset
# 2017-12-14 jw, v1.4  Added matchStrokeColor()
# 2017-12-21 jw, v1.5  Changed getPathVertices() to construct a to self.paths list, instead of
#                      a dictionary. (Preserving native ordering)
# 2017-12-22 jw, v1.6  fixed "use" to avoid errors with unknown global symbal 'composeTransform'
# 2017-12-25 jw, v1.7  Added getNodeStyle(), cssDictAdd(), expanded matchStrokeColor() to use
#                      inline style defs. Added a warning message for not-implemented CSS styles.
#                v1.7a Added getNodeStyleOne() made getNodeStyle() recurse through parents.
# 2018-03-10 jw, v1.7b Added search paths to find inkex.
#                v1.7c Refactoring for simpler interface without subclassing.
#                      Added load(), getElementsByIds() methods.
# 2018-03-21 jw, v1.7d Added handleViewBox() to load().
#                      Added traverse().
# 2019-01-12 jw, v1.7e debug output to self.tty

import gettext
import re
import sys

sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):
  sys.path.append('C:\Program Files\Inkscape\share\extensions')
elif sys_platform.startswith('darwin'):
  sys.path.append('~/.config/inkscape/extensions')
else:   # Linux
  sys.path.append('/usr/share/inkscape/extensions/')

import inkex
import simplepath
import simplestyle
import simpletransform
import cubicsuperpath
import cspsubdiv
import bezmisc

from lxml import etree

class PathGenerator():
    """
    A PathGenerator has methods for different svg objects. It compiles an
    internal representation of them all, handling transformations and linear
    interpolation of curved path segments.

    The base class PathGenerator is dummy (abstract) class that raises an
    NotImplementedError() on each method entry point. It serves as documentation for
    the generator interface.
    """
    def __init__(self):
        self._svg = None

    def registerSvg(self, svg):
        self._svg = svg
        # svg.stats = self.stats

    def pathString(self, d, node, mat):
        """
        d is expected formatted as an svg path string here.
        """
        raise NotImplementedError("See example inksvg.LinearPathGen.pathString()")

    def pathList(self, d, node, mat):
        """
        d is expected as an [[cmd, [args]], ...] arrray
        """
        raise NotImplementedError("See example inksvg.LinearPathGen.pathList()")

    def objRect(x, y, w, h, node, mat):
        raise NotImplementedError("See example inksvg.LinearPathGen.objRect()")

    def objRoundedRect(self, x, y, w, h, rx, ry, node, mat):
        raise NotImplementedError("See example inksvg.LinearPathGen.objRoundedRect()")

    def objEllipse(self, cx, cy, rx, ry, node, mat):
        raise NotImplementedError("See example inksvg.LinearPathGen.objEllipse()")

    def objArc(self, d, cx, cy, rx, ry, st, en, cl, node, mat):
        """
        SVG does not have an arc element. Inkscape creates officially a path element,
        but also (redundantly) provides the original arc values.
        Implementations can choose to work with the path d and ignore the rest,
        or work with the cx, cy, rx, ry, ... parameters and ignore d.
        Note: the parameter closed=True/False is actually derived from looking at the last
        command of path d. Hackish, but there is no 'sodipodi:closed' element, or similar.
        """
        raise NotImplementedError("See example inksvg.LinearPathGen.objArc()")



class LinearPathGen(PathGenerator):

    def __init__(self, smoothness=0.2):
        self.smoothness = max(0.0001, smoothness)

    def pathString(self, d, node, mat):
        """
        d is expected formatted as an svg path string here.
        """
        print("calling getPathVertices",  self.smoothness, file=self._svg.tty)
        self._svg.getPathVertices(d, node, mat, self.smoothness)

    def pathList(self, d, node, mat):
        """
        d is expected as an [[cmd, [args]], ...] arrray
        """
        return self.pathString(simplepath.formatPath(d), node, mat)

    def objRect(self, x, y, w, h, node, mat):
        """
        Manually transform

           <rect x="X" y="Y" width="W" height="H"/>

        into

           <path d="MX,Y lW,0 l0,H l-W,0 z"/>

        I.e., explicitly draw three sides of the rectangle and the
        fourth side implicitly
        """
        a = []
        a.append(['M ', [x, y]])
        a.append([' l ', [w, 0]])
        a.append([' l ', [0, h]])
        a.append([' l ', [-w, 0]])
        a.append([' Z', []])
        self.pathList(a, node, mat)

    def objRoundedRect(self, x, y, w, h, rx, ry, node, mat):
        print("calling roundedRectBezier", file=self.tty)
        d = self._svg.roundedRectBezier(x, y, w, h, rx, ry)
        self._svg.getPathVertices(d, node, mat, self.smoothness)

    def objEllipse(self, cx, cy, rx, ry, node, mat):
        """
        Convert circles and ellipses to a path with two 180 degree
        arcs. In general (an ellipse), we convert

          <ellipse rx="RX" ry="RY" cx="X" cy="Y"/>

        to

          <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/>

        where

          X1 = CX - RX
          X2 = CX + RX

        Note: ellipses or circles with a radius attribute of value 0
        are ignored
        """
        x1 = cx - rx
        x2 = cx + rx
        d = 'M %f,%f '     % (x1, cy) + \
            'A %f,%f '     % (rx, ry) + \
            '0 1 0 %f,%f ' % (x2, cy) + \
            'A %f,%f '     % (rx, ry) + \
            '0 1 0 %f,%f'  % (x1, cy)
        self.pathString(d, node, mat)

    def objArc(self, d, cx, cy, rx, ry, st, en, cl, node, mat):
        """
        We ignore the cx, cy, rx, ry data, and are happy that inkscape
        also provides the same information as a path.
        """
        self.pathString(d, node, mat)



class InkSvg():
    """
    Usage example with subclassing:

    #
    #    class ThunderLaser(inkex.Effect):
    #            def __init__(self):
    #                    inkex.localize()
    #                    inkex.Effect.__init__(self)
    #            def effect(self):
    #                    svg = InkSvg(document=self.document, pathgen=LinearPathGen(smoothness=0.2))
    #                    svg.handleViewBox()
    #                    svg.recursivelyTraverseSvg(self.document.getroot(), svg.docTransform)
    #                    for tup in svg.paths:
    #                            node = tup[0]
    #                            ...
    #    e = ThunderLaser()
    #    e.affect()
    #

    Simple usage example with method invocation:

    #    svg = InkSvg(pathgen=LinearPathGen(smoothness=0.01))
    #    svg.load(svgfile)
    #    svg.traverse([ids...])
    #    print(svg.paths)       # all coordinates in mm

    """
    __version__ = "1.7e"
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100

    # imports from inkex
    NSS = inkex.NSS

    def getElementsByIds(self, ids):
        """
        ids be a string of a comma seperated values, or a list of strings.
        Returns a list of xml nodes.
        """
        if not self.document:
          raise ValueError("no document loaded.")
        if isinstance(ids, (bytes, str)): ids = [ ids ]   # handle some scalars
        ids = ','.join(ids).split(',')                    # merge into a string and re-split

        ## OO-Fail:
        # cannot use inkex.getElementById() -- it returns only the first element of each hit.
        # cannot use inkex.getselected() -- it returns the last element of each hit only.
        """Collect selected nodes"""
        nodes = []
        for id in ids:
          if id != '':    # empty strings happen after splitting...
            path = '//*[@id="%s"]' % id
            el_list = self.document.xpath(path, namespaces=InkSvg.NSS)
            if el_list:
              for node in el_list:
                nodes.append(node)
            else:
              raise ValueError("id "+id+" not found in the svg document.")
        return nodes


    def load(self, filename):
        inkex.localize()
        # OO-Fail: cannot call inkex.Effect.parse(), Effect constructor has so many side-effects.
        stream = open(filename, 'r')
        p = etree.XMLParser(huge_tree=True)
        self.document = etree.parse(stream, parser=p)
        stream.close()
        # initialize a coordinate system that can be picked up by pathgen.
        self.handleViewBox()

    def traverse(self, ids=None):
        """
        Recursively traverse the SVG document. If ids are given, all matching nodes
        are taken as start positions for traversal. Otherwise traveral starts at
        the root node of the document.
        """
        selected = []
        if ids is not None:
          selected = self.getElementsByIds(ids)
        if len(selected):
          # Traverse the selected objects
          for node in selected:
            transform = self.recursivelyGetEnclosingTransform(node)
            self.recursivelyTraverseSvg([node], transform)
        else:
          # Traverse the entire document building new, transformed paths
          self.recursivelyTraverseSvg(self.document.getroot(), self.docTransform)


    def getNodeStyleOne(self, node):
        """
        Finds style declarations by .class, #id or by tag.class syntax,
        and of course by a direct style='...' attribute.
        """
        sheet = ''
        selectors = []
        classes = node.get('class', '')         # classes == None can happen here.
        if classes is not None and classes != '':
            selectors = ["."+cls for cls in re.split('[\s,]+', classes)]
            selectors += [node.tag+sel for sel in selectors]
        node_id = node.get('id', '')
        if node_id is not None and node_id != '':
            selectors += [ "#"+node_id ]
        for sel in selectors:
            if sel in self.css_dict:
                sheet += '; '+self.css_dict[sel]
        style = node.get('style', '')
        if style is not None and style != '':
            sheet += '; '+style
        return simplestyle.parseStyle(sheet)

    def getNodeStyle(self, node):
        """
        Recurse into parent group nodes, like simpletransform.ComposeParents
        Calling getNodeStyleOne() for each.
        """
        combined_style = {}
        parent = node.getparent()
        if parent.tag == inkex.addNS('g','svg') or parent.tag == 'g':
            combined_style = self.getNodeStyle(parent)
        style = self.getNodeStyleOne(node)
        for s in style:
            combined_style[s] = style[s]        # overwrite or add
        return combined_style


    def styleDasharray(self, path_d, node):
        """
        Check the style of node for a stroke-dasharray, and apply it to the
        path d returning the result.  d is returned unchanged, if no
        stroke-dasharray was found.

        ## Extracted from inkscape extension convert2dashes; original
        ## comments below.
        ## Added stroke-dashoffset handling, made it a universal operator
        ## on nodes and 'd' paths.

        This extension converts a path into a dashed line using 'stroke-dasharray'
        It is a modification of the file addnodes.py

        Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
        Copyright (C) 2009 Alvin Penner, penner@vaxxine.com
        """

        def tpoint((x1,y1), (x2,y2), t = 0.5):
            return [x1+t*(x2-x1),y1+t*(y2-y1)]
        def cspbezsplit(sp1, sp2, t = 0.5):
            m1=tpoint(sp1[1],sp1[2],t)
            m2=tpoint(sp1[2],sp2[0],t)
            m3=tpoint(sp2[0],sp2[1],t)
            m4=tpoint(m1,m2,t)
            m5=tpoint(m2,m3,t)
            m=tpoint(m4,m5,t)
            return [[sp1[0][:],sp1[1][:],m1], [m4,m,m5], [m3,sp2[1][:],sp2[2][:]]]
        def cspbezsplitatlength(sp1, sp2, l = 0.5, tolerance = 0.001):
            bez = (sp1[1][:],sp1[2][:],sp2[0][:],sp2[1][:])
            t = bezmisc.beziertatlength(bez, l, tolerance)
            return cspbezsplit(sp1, sp2, t)
        def cspseglength(sp1,sp2, tolerance = 0.001):
            bez = (sp1[1][:],sp1[2][:],sp2[0][:],sp2[1][:])
            return bezmisc.bezierlength(bez, tolerance)

        style = self.getNodeStyle(node)
        if not style.has_key('stroke-dasharray'):
            return path_d
        dashes = []
        if style['stroke-dasharray'].find(',') > 0:
            dashes = [float (dash) for dash in style['stroke-dasharray'].split(',') if dash]
        if not dashes:
            return path_d

        dashoffset = 0.0
        if style.has_key('stroke-dashoffset'):
            dashoffset = float(style['stroke-dashoffset'])
            if dashoffset < 0.0: dashoffset = 0.0
            if dashoffset > dashes[0]: dashoffset = dashes[0]   # avoids a busy-loop below!

        p = cubicsuperpath.parsePath(path_d)
        new = []
        for sub in p:
            idash = 0
            dash = dashes[0]
            # print("initial dash length: ", dash, dashoffset, file=self.tty)
            dash = dash - dashoffset
            length = 0
            new.append([sub[0][:]])
            i = 1
            while i < len(sub):
                dash = dash - length
                length = cspseglength(new[-1][-1], sub[i])
                while dash < length:
                    new[-1][-1], next, sub[i] = cspbezsplitatlength(new[-1][-1], sub[i], dash/length)
                    if idash % 2:           # create a gap
                        new.append([next[:]])
                    else:                   # splice the curve
                        new[-1].append(next[:])
                    length = length - dash
                    idash = (idash + 1) % len(dashes)
                    dash = dashes[idash]
                if idash % 2:
                    new.append([sub[i]])
                else:
                    new[-1].append(sub[i])
                i+=1
        return cubicsuperpath.formatPath(new)

    def matchStrokeColor(self, node, rgb, eps=None, avg=True):
        """
        Return True if the line color found in the style attribute of elem
        does not differ from rgb in any of the components more than eps.
        The default eps with avg=True is 64.
        With avg=False the default is eps=85 (33% on a 0..255 scale).

        In avg mode, the average of all three color channel differences is
        compared against eps. Otherwise each color channel difference is
        compared individually.

        The special cases None, False, True for rgb are interpreted logically.
        Otherwise rgb is expected as a list of three integers in 0..255 range.
        Missing style attribute or no stroke element is interpreted as False.
        Unparseable stroke elements are interpreted as 'black' (0,0,0).
        Hexadecimal stroke formats of '#RRGGBB' or '#RGB' are understood
        as well as 'rgb(100%, 0%, 0%) or 'red' relying on simplestyle.
        """
        if eps is None:
          eps = 64 if avg == True else 85
        if rgb is None or rgb is False: return False
        if rgb is True: return True
        style = self.getNodeStyle(node)
        s = style.get('stroke', '')
        if s == '': return False
        c = simplestyle.parseColor(s)
        if sum:
           s = abs(rgb[0]-c[0]) + abs(rgb[1]-c[1]) + abs(rgb[2]-c[2])
           if s < 3*eps:
             return True
           return False
        if abs(rgb[0]-c[0]) > eps: return False
        if abs(rgb[1]-c[1]) > eps: return False
        if abs(rgb[2]-c[2]) > eps: return False
        return True

    def cssDictAdd(self, text):
        """
        Represent css cdata as a hash in css_dict.
        Implements what is seen on: http://www.blooberry.com/indexdot/css/examples/cssembedded.htm
        """
        text=re.sub('^\s*(<!--)?\s*', '', text)
        while True:
            try:
                (keys, rest) = text.split('{', 1)
            except:
                break
            keys = re.sub('/\*.*?\*/', ' ', keys)   # replace comments with whitespace
            keys = re.split('[\s,]+', keys)         # convert to list
            while '' in keys:
                keys.remove('')                     # remove empty elements (at start or end)
            (val,text) = rest.split('}', 1)
            val = re.sub('/\*.*?\*/', '', val)      # replace comments nothing in values
            val = re.sub('\s+', ' ', val).strip()   # normalize whitespace
            for k in keys:
                if not k in self.css_dict:
                    self.css_dict[k] = val
                else:
                    self.css_dict[k] += '; '+val


    def roundedRectBezier(self, x, y, w, h, rx, ry=0):
        """
        Draw a rectangle of size w x h, at start point x, y with the corners rounded by radius
        rx and ry. Each corner is a quarter of an ellipsis, where rx and ry are the horizontal
        and vertical dimenstion.
        A pathspec according to https://www.w3.org/TR/SVG/paths.html#PathDataEllipticalArcCommands
        is returned. Very similar to what inkscape would do when converting object to path.
        Inkscape seems to use a kappa value of 0.553, higher precision is used here.

        x=0, y=0, w=200, h=100, rx=50, ry=30 produces in inkscape
        d="m 50,0 h 100 c 27.7,0 50,13.38 50,30 v 40 c 0,16.62 -22.3,30 -50,30
           H 50 C 22.3,100 0,86.62 0,70 V 30 C 0,13.38 22.3,0 50,0 Z"
        It is unclear, why there is a Z, the last point is identical with the first already.
        It is unclear, why half of the commands use relative and half use absolute coordinates.
        We do it all in relative coords, except for the initial M, and we ommit the Z.
        """
        if rx < 0: rx = 0
        if rx > 0.5*w: rx = 0.5*w
        if ry < 0: ry = 0
        if ry > 0.5*h: ry = 0.5*h
        if ry < 0.0000001: ry = rx
        k = 0.5522847498307933984022516322796     # kappa, handle length for a 4-point-circle.
        d  = "M %f,%f h %f " % (x+rx, y, w-rx-rx)                      # top horizontal to right
        d += "c %f,%f %f,%f %f,%f " % (rx*k,0, rx,ry*(1-k), rx,ry)     # top right ellipse
        d += "v %f " % (h-ry-ry)                                       # right vertical down
        d += "c %f,%f %f,%f %f,%f " % (0,ry*k, rx*(k-1),ry, -rx,ry)    # bottom right ellipse
        d += "h %f " % (-w+rx+rx)                                      # bottom horizontal to left
        d += "c %f,%f %f,%f %f,%f " % (-rx*k,0, -rx,ry*(k-1), -rx,-ry) # bottom left ellipse
        d += "v %f " % (-h+ry+ry)                                      # left vertical up
        d += "c %f,%f %f,%f %f,%f" % (0,-ry*k, rx*(1-k),-ry, rx,-ry)   # top left ellipse
        return d


    def subdivideCubicPath(self, sp, flat, i=1):
        '''
        [ Lifted from eggbot.py with impunity ]

        Break up a bezier curve into smaller curves, each of which
        is approximately a straight line within a given tolerance
        (the "smoothness" defined by [flat]).

        This is a modified version of cspsubdiv.cspsubdiv(): rewritten
        because recursion-depth errors on complicated line segments
        could occur with cspsubdiv.cspsubdiv().
        '''

        while True:
            while True:
                if i >= len(sp):
                    return

                p0 = sp[i - 1][1]
                p1 = sp[i - 1][2]
                p2 = sp[i][0]
                p3 = sp[i][1]

                b = (p0, p1, p2, p3)

                if cspsubdiv.maxdist(b) > flat:
                    break

                i += 1

            one, two = bezmisc.beziersplitatt(b, 0.5)
            sp[i - 1][2] = one[1]
            sp[i][0] = two[2]
            p = [one[2], one[3], two[1]]
            sp[i:1] = [p]

    def parseLengthWithUnits(self, str, default_unit='px'):
        '''
        Parse an SVG value which may or may not have units attached
        This version is greatly simplified in that it only allows: no units,
        units of px, and units of %.  Everything else, it returns None for.
        There is a more general routine to consider in scour.py if more
        generality is ever needed.
        With inkscape 0.91 we need other units too: e.g. svg:width="400mm"
        '''

        u = default_unit
        s = str.strip()
        if s[-2:] in ('px', 'pt', 'pc', 'mm', 'cm', 'in', 'ft'):
            u = s[-2:]
            s = s[:-2]
        elif s[-1:] in ('m', '%'):
            u = s[-1:]
            s = s[:-1]

        try:
            v = float(s)
        except:
            return None, None

        return v, u


    def __init__(self, document=None, svgfile=None, smoothness=0.2, debug=False, pathgen=LinearPathGen(smoothness=0.2)):
        """
        Usage: ...
        """
        self.dpi = 90.0                 # factored out for inkscape-0.92
        self.px_used = False            # raw px unit depends on correct dpi.
        self.xmin, self.xmax = (1.0E70, -1.0E70)
        self.ymin, self.ymax = (1.0E70, -1.0E70)

        try:
            if debug == False: raise ValueError('intentional exception')
            self.tty = open("/dev/tty", 'w')
        except:
            from os import devnull
            self.tty = open(devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.

        # CAUTION: smoothness here is deprecated. it belongs into pathgen, if.
        # CAUTION: smoothness == 0.0 leads to a busy-loop.
        self.smoothness = max(0.0001, smoothness)    # 0.0001 .. 5.0
        self.pathgen = pathgen
        pathgen.registerSvg(self)

        # List of paths we will construct.  Path lists are paired with the SVG node
        # they came from.  Such pairing can be useful when you actually want
        # to go back and update the SVG document, or retrieve e.g. style information.
        self.paths = []

        # cssDictAdd collects style definitions here:
        self.css_dict = {}

        # For handling an SVG viewbox attribute, we will need to know the
        # values of the document's <svg> width and height attributes as well
        # as establishing a transform from the viewbox to the display.

        self.docWidth = float(self.DEFAULT_WIDTH)
        self.docHeight = float(self.DEFAULT_HEIGHT)
        self.docTransform = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

        # Dictionary of warnings issued.  This to prevent from warning
        # multiple times about the same problem
        self.warnings = {}

        if document:
            self.document = document
            if svgfile:
                inkex.errormsg('Warning: ignoring svgfile. document given too.')
        elif svgfile:
            self.document = self.load(svgfile)

    def getLength(self, name, default):

        '''
        Get the <svg> attribute with name "name" and default value "default"
        Parse the attribute into a value and associated units.  Then, accept
        units of cm, ft, in, m, mm, pc, or pt.  Convert to pixels.

        Note that SVG defines 90 px = 1 in = 25.4 mm.
        Note: Since inkscape 0.92 we use the CSS standard of 96 px = 1 in.
        '''
        str = self.document.getroot().get(name)
        if str:
            return self.lengthWithUnit(str)
        else:
            # No width specified; assume the default value
            return float(default)

    def lengthWithUnit(self, strn, default_unit='px'):
        v, u = self.parseLengthWithUnits(strn, default_unit)
        if v is None:
            # Couldn't parse the value
            return None
        elif (u == 'mm'):
            return float(v) * (self.dpi / 25.4)
        elif (u == 'cm'):
            return float(v) * (self.dpi * 10.0 / 25.4)
        elif (u == 'm'):
            return float(v) * (self.dpi * 1000.0 / 25.4)
        elif (u == 'in'):
            return float(v) * self.dpi
        elif (u == 'ft'):
            return float(v) * 12.0 * self.dpi
        elif (u == 'pt'):
            # Use modern "Postscript" points of 72 pt = 1 in instead
            # of the traditional 72.27 pt = 1 in
            return float(v) * (self.dpi / 72.0)
        elif (u == 'pc'):
            return float(v) * (self.dpi / 6.0)
        elif (u == 'px'):
            self.px_used = True
            return float(v)
        else:
            # Unsupported units
            return None

    def getDocProps(self):

        '''
        Get the document's height and width attributes from the <svg> tag.
        Use a default value in case the property is not present or is
        expressed in units of percentages.

        This initializes:
        * self.basename
        * self.docWidth
        * self.docHeight
        * self.dpi
        '''

        inkscape_version = self.document.getroot().get(
            "{http://www.inkscape.org/namespaces/inkscape}version")
        sodipodi_docname = self.document.getroot().get(
            "{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docname")
        if sodipodi_docname is None:
            sodipodi_docname = "inkscape"
        self.basename = re.sub(r"\.SVG", "", sodipodi_docname, flags=re.I)
        # a simple 'inkscape:version' does not work here. sigh....
        #
        # BUG:
        # inkscape 0.92 uses 96 dpi, inkscape 0.91 uses 90 dpi.
        # From inkscape 0.92 we receive an svg document that has
        # both inkscape:version and sodipodi:docname if the document
        # was ever saved before. If not, both elements are missing.
        #
        import lxml.etree
        # inkex.errormsg(lxml.etree.tostring(self.document.getroot()))
        if inkscape_version:
            '''
            inkscape:version="0.91 r"
            inkscape:version="0.92.0 ..."
           See also https://github.com/fablabnbg/paths2openscad/issues/1
            '''
            # inkex.errormsg("inkscape:version="+inkscape_version)
            m = re.match(r"(\d+)\.(\d+)", inkscape_version)
            if m:
                if int(m.group(1)) > 0 or int(m.group(2)) > 91:
                    self.dpi = 96                # 96dpi since inkscape 0.92
                    # inkex.errormsg("switching to 96 dpi")

        # BUGFIX https://github.com/fablabnbg/inkscape-paths2openscad/issues/1
        # get height and width after dpi. This is needed for e.g. mm units.
        self.docHeight = self.getLength('height', self.DEFAULT_HEIGHT)
        self.docWidth = self.getLength('width', self.DEFAULT_WIDTH)

        if (self.docHeight is None) or (self.docWidth is None):
            return False
        else:
            return True

    def handleViewBox(self):

        '''
        Set up the document-wide transform in the event that the document has
        an SVG viewbox

        This initializes:
        * self.basename
        * self.docWidth
        * self.docHeight
        * self.dpi
        * self.docTransform
        '''

        if self.getDocProps():
            viewbox = self.document.getroot().get('viewBox')
            if viewbox:
                vinfo = viewbox.strip().replace(',', ' ').split(' ')
                if (vinfo[2] != 0) and (vinfo[3] != 0):
                    sx = self.docWidth  / float(vinfo[2])
                    sy = self.docHeight / float(vinfo[3])
                    self.docTransform = simpletransform.parseTransform('scale(%f,%f)' % (sx, sy))

    def getPathVertices(self, path, node=None, transform=None, smoothness=None):

        '''
        Decompose the path data from an SVG element into individual
        subpaths, each subpath consisting of absolute move to and line
        to coordinates.  Place these coordinates into a list of polygon
        vertices.

        The result is appended to self.paths as a two-element tuple of the
        form (node, path_list). This preserves the native ordering of
        the SVG file as much as possible, while still making all attributes
        if the node available when processing the path list.
        '''

        if not smoothness:
            smoothness = self.smoothness        # self.smoothness is deprecated.

        if (not path) or (len(path) == 0):
            # Nothing to do
            return None

        if node is not None:
            path = self.styleDasharray(path, node)

        # parsePath() may raise an exception.  This is okay
        sp = simplepath.parsePath(path)
        if (not sp) or (len(sp) == 0):
            # Path must have been devoid of any real content
            return None

        # Get a cubic super path
        p = cubicsuperpath.CubicSuperPath(sp)
        if (not p) or (len(p) == 0):
            # Probably never happens, but...
            return None

        if transform:
            simpletransform.applyTransformToPath(transform, p)

        # Now traverse the cubic super path
        subpath_list = []
        subpath_vertices = []

        for sp in p:

            # We've started a new subpath
            # See if there is a prior subpath and whether we should keep it
            if len(subpath_vertices):
                subpath_list.append([subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]])

            subpath_vertices = []
            self.subdivideCubicPath(sp, float(smoothness))

            # Note the first point of the subpath
            first_point = sp[0][1]
            subpath_vertices.append(first_point)
            sp_xmin = first_point[0]
            sp_xmax = first_point[0]
            sp_ymin = first_point[1]
            sp_ymax = first_point[1]

            n = len(sp)

            # Traverse each point of the subpath
            for csp in sp[1:n]:

                # Append the vertex to our list of vertices
                pt = csp[1]
                subpath_vertices.append(pt)

                # Track the bounding box of this subpath
                if pt[0] < sp_xmin:
                    sp_xmin = pt[0]
                elif pt[0] > sp_xmax:
                    sp_xmax = pt[0]
                if pt[1] < sp_ymin:
                    sp_ymin = pt[1]
                elif pt[1] > sp_ymax:
                    sp_ymax = pt[1]

            # Track the bounding box of the overall drawing
            # This is used for centering the polygons in OpenSCAD around the
            # (x,y) origin
            if sp_xmin < self.xmin:
                self.xmin = sp_xmin
            if sp_xmax > self.xmax:
                self.xmax = sp_xmax
            if sp_ymin < self.ymin:
                self.ymin = sp_ymin
            if sp_ymax > self.ymax:
                self.ymax = sp_ymax

        # Handle the final subpath
        if len(subpath_vertices):
            subpath_list.append([subpath_vertices, [sp_xmin, sp_xmax, sp_ymin, sp_ymax]])

        if len(subpath_list) > 0:
            self.paths.append( (node, subpath_list) )


    def recursivelyTraverseSvg(self, aNodeList, matCurrent=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                               parent_visibility='visible'):

        '''
        [ This too is largely lifted from eggbot.py ]

        Recursively walk the SVG document aNodeList, building polygon vertex lists
        for each graphical element we support. The list is generated in self.paths
        as a list of tuples [ (node, path_list), (node, path_list), ...] ordered
        natively by their order of appearance in the SVG document.

        Rendered SVG elements:
            <circle>, <ellipse>, <line>, <path>, <polygon>, <polyline>, <rect>

        Supported SVG elements:
            <group>, <use>

        Ignored SVG elements:
            <defs>, <eggbot>, <metadata>, <namedview>, <pattern>,
            processing directives

        All other SVG elements trigger an error (including <text>)
        '''

        for node in aNodeList:

            # Ignore invisible nodes
            visibility = node.get('visibility', parent_visibility)
            if visibility == 'inherit':
                visibility = parent_visibility
            if visibility == 'hidden' or visibility == 'collapse':
                continue

            # FIXME: should we inherit styles from parents?
            s = self.getNodeStyle(node)
            if s.get('display', '') == 'none': continue

            # First apply the current matrix transform to this node's tranform
            matNew = simpletransform.composeTransform(
                matCurrent, simpletransform.parseTransform(node.get("transform")))

            if node.tag == inkex.addNS('g', 'svg') or node.tag == 'g':

                self.recursivelyTraverseSvg(node, matNew, visibility)

            elif node.tag == inkex.addNS('use', 'svg') or node.tag == 'use':

                # A <use> element refers to another SVG element via an
                # xlink:href="#blah" attribute.  We will handle the element by
                # doing an XPath search through the document, looking for the
                # element with the matching id="blah" attribute.  We then
                # recursively process that element after applying any necessary
                # (x,y) translation.
                #
                # Notes:
                #  1. We ignore the height and width attributes as they do not
                #     apply to path-like elements, and
                #  2. Even if the use element has visibility="hidden", SVG
                #     still calls for processing the referenced element.  The
                #     referenced element is hidden only if its visibility is
                #     "inherit" or "hidden".

                refid = node.get(inkex.addNS('href', 'xlink'))
                if not refid:
                    continue

                # [1:] to ignore leading '#' in reference
                path = '//*[@id="%s"]' % refid[1:]
                refnode = node.xpath(path)
                if refnode:
                    x = float(node.get('x', '0'))
                    y = float(node.get('y', '0'))
                    # Note: the transform has already been applied
                    if (x != 0) or (y != 0):
                        matNew2 = simpletransform.composeTransform(matNew, simpletransform.parseTransform('translate(%f,%f)' % (x, y)))
                    else:
                        matNew2 = matNew
                    visibility = node.get('visibility', visibility)
                    self.recursivelyTraverseSvg(refnode, matNew2, visibility)

            elif node.tag == inkex.addNS('path', 'svg'):

                path_data = node.get('d', '')
                if node.get(inkex.addNS('type', 'sodipodi'), '') == 'arc':
                    cx = float(node.get(inkex.addNS('cx', 'sodipodi'), '0'))
                    cy = float(node.get(inkex.addNS('cy', 'sodipodi'), '0'))
                    rx = float(node.get(inkex.addNS('rx', 'sodipodi'), '0'))
                    ry = float(node.get(inkex.addNS('ry', 'sodipodi'), '0'))
                    st = float(node.get(inkex.addNS('start', 'sodipodi'), '0'))
                    en = float(node.get(inkex.addNS('end', 'sodipodi'), '0'))
                    cl = path_data.strip()[-1] in ('z', 'Z')
                    self.pathgen.objArc(path_data, cx, cy, rx, ry, st, en, cl, node, matNew)
                else:
                    ### sodipodi:type="star" also comes here. TBD later, if need be.
                    self.pathgen.pathString(path_data, node, matNew)

            elif node.tag == inkex.addNS('rect', 'svg') or node.tag == 'rect':

                # Create a path with the outline of the rectangle
                # Adobe Illustrator leaves out 'x'='0'.
                x = float(node.get('x', '0'))
                y = float(node.get('y', '0'))
                w = float(node.get('width', '0'))
                h = float(node.get('height', '0'))
                rx = float(node.get('rx', '0'))
                ry = float(node.get('ry', '0'))

                if rx > 0.0 or ry > 0.0:
                    if   ry < 0.0000001: ry = rx
                    elif rx < 0.0000001: rx = ry
                    self.pathgen.objRoundedRect(x, y, w, h, rx, ry, node, matNew)
                else:
                    self.pathgen.objRect(x, y, w, h, node, matNew)

            elif node.tag == inkex.addNS('line', 'svg') or node.tag == 'line':

                # Convert
                #
                #   <line x1="X1" y1="Y1" x2="X2" y2="Y2/>
                #
                # to
                #
                #   <path d="MX1,Y1 LX2,Y2"/>

                x1 = float(node.get('x1'))
                y1 = float(node.get('y1'))
                x2 = float(node.get('x2'))
                y2 = float(node.get('y2'))
                if (not x1) or (not y1) or (not x2) or (not y2):
                    continue
                a = []
                a.append(['M ', [x1, y1]])
                a.append([' L ', [x2, y2]])
                self.pathgen.pathList(a, node, matNew)

            elif node.tag == inkex.addNS('polyline', 'svg') or node.tag == 'polyline':

                # Convert
                #
                #  <polyline points="x1,y1 x2,y2 x3,y3 [...]"/>
                #
                # to
                #
                #   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...]"/>
                #
                # Note: we ignore polylines with no points

                pl = node.get('points', '').strip()
                if pl == '':
                    continue

                pa = pl.split()
                d = "".join(["M " + pa[i] if i == 0 else " L " + pa[i] for i in range(0, len(pa))])
                self.pathgen.pathString(d, node, matNew)

            elif node.tag == inkex.addNS('polygon', 'svg') or node.tag == 'polygon':

                # Convert
                #
                #  <polygon points="x1,y1 x2,y2 x3,y3 [...]"/>
                #
                # to
                #
                #   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...] Z"/>
                #
                # Note: we ignore polygons with no points

                pl = node.get('points', '').strip()
                if pl == '':
                    continue

                pa = pl.split()
                d = "".join(["M " + pa[i] if i == 0 else " L " + pa[i] for i in range(0, len(pa))])
                d += " Z"
                self.pathgen.pathString(d, node, matNew)

            elif node.tag == inkex.addNS('ellipse', 'svg') or node.tag == 'ellipse' or \
                 node.tag == inkex.addNS('circle', 'svg')  or node.tag == 'circle':

                if node.tag == inkex.addNS('ellipse', 'svg') or node.tag == 'ellipse':
                    rx = float(node.get('rx', '0'))
                    ry = float(node.get('ry', '0'))
                else:
                    rx = float(node.get('r', '0'))
                    ry = rx
                if rx == 0 or ry == 0:
                    continue

                cx = float(node.get('cx', '0'))
                cy = float(node.get('cy', '0'))
                self.pathgen.objEllipse(cx, cy, rx, ry, node, matNew)

            elif node.tag == inkex.addNS('pattern', 'svg') or node.tag == 'pattern':
                pass

            elif node.tag == inkex.addNS('metadata', 'svg') or node.tag == 'metadata':
                pass

            elif node.tag == inkex.addNS('defs', 'svg') or node.tag == 'defs':
                self.recursivelyTraverseSvg(node, matNew, visibility)

            elif node.tag == inkex.addNS('desc', 'svg') or node.tag == 'desc':
                pass

            elif node.tag == inkex.addNS('namedview', 'sodipodi') or node.tag == 'namedview':
                pass

            elif node.tag == inkex.addNS('eggbot', 'svg') or node.tag == 'eggbot':
                pass

            elif node.tag == inkex.addNS('text', 'svg') or node.tag == 'text':
                texts = []
                plaintext = ''
                for tnode in node.iterfind('.//'):  # all subtree
                    if tnode is not None and tnode.text is not None:
                        texts.append(tnode.text)
                if len(texts):
                    plaintext = "', '".join(texts).encode('latin-1')
                    inkex.errormsg('Warning: text "%s"' % plaintext)
                    inkex.errormsg('Warning: unable to draw text, please convert it to a path first.')

            elif node.tag == inkex.addNS('title', 'svg') or node.tag == 'title':
                pass

            elif node.tag == inkex.addNS('image', 'svg') or node.tag == 'image':
                if 'image' not in self.warnings:
                    inkex.errormsg(
                        gettext.gettext(
                            'Warning: unable to draw bitmap images; please convert them to line art first.  '
                            'Consider using the "Trace bitmap..." tool of the "Path" menu.  Mac users please '
                            'note that some X11 settings may cause cut-and-paste operations to paste in bitmap copies.'))
                    self.warnings['image'] = 1

            elif node.tag == inkex.addNS('pattern', 'svg') or node.tag == 'pattern':
                pass

            elif node.tag == inkex.addNS('radialGradient', 'svg') or node.tag == 'radialGradient':
                # Similar to pattern
                pass

            elif node.tag == inkex.addNS('linearGradient', 'svg') or node.tag == 'linearGradient':
                # Similar in pattern
                pass

            elif node.tag == inkex.addNS('style', 'svg') or node.tag == 'style':
                # This is a reference to an external style sheet and not the
                # value of a style attribute to be inherited by child elements
                #
                #   <style type="text/css">
                #    <![CDATA[
                #     .str0 {stroke:red;stroke-width:20}
                #     .fil0 {fill:none}
                #    ]]>
                #
                # FIXME: test/test_styles.sh fails without this.
                # This is input for self.getNodeStyle()
                if node.get('type', '') == "text/css":
                    self.cssDictAdd(node.text)
                else:
                    inkex.errormsg("Warning: Corel-style CSS definitions ignored. Parsing element 'style' with type='%s' not implemented." % node.get('type', ''))

            elif node.tag == inkex.addNS('cursor', 'svg') or node.tag == 'cursor':
                pass

            elif node.tag == inkex.addNS('color-profile', 'svg') or node.tag == 'color-profile':
                # Gamma curves, color temp, etc. are not relevant to single
                # color output
                pass

            elif not isinstance(node.tag, basestring):
                # This is likely an XML processing instruction such as an XML
                # comment.  lxml uses a function reference for such node tags
                # and as such the node tag is likely not a printable string.
                # Further, converting it to a printable string likely won't
                # be very useful.
                pass

            else:
                inkex.errormsg('Warning: unable to draw object <%s>, please convert it to a path first.' % node.tag)
                pass

    def recursivelyGetEnclosingTransform(self, node):

        '''
        Determine the cumulative transform which node inherits from
        its chain of ancestors.
        '''
        node = node.getparent()
        if node is not None:
            parent_transform = self.recursivelyGetEnclosingTransform(node)
            node_transform = node.get('transform', None)
            if node_transform is None:
                return parent_transform
            else:
                tr = simpletransform.parseTransform(node_transform)
                if parent_transform is None:
                    return tr
                else:
                    return simpletransform.composeTransform(parent_transform, tr)
        else:
            return self.docTransform


import json
import inkex
import gettext


# python2 compatibility. Inkscape runs us with python2!
if sys.version_info.major < 3:
        def bytes(tupl):
                return "".join(map(chr, tupl))


class FlatProjection(inkex.Effect):

    # CAUTION: Keep in sync with flat-projection.inx and flat-projection_de.inx
    __version__ = '0.3'         # >= max(src/proj.py:__version__, src/inksvg.py:__version__)

    def __init__(self):
        """
Option parser example:

'flat-projection.py', '--id=g20151', '--tab=settings', '--rotation-type=standard_rotation', '--standard-rotation=x-90', '--manual_rotation_x=90', '--manual_rotation_y=0', '--manual_rotation_z=0', '--projection-type=standard_projection', '--standard-projection=7,42', '--standard-projection-autoscale=true', '--trimetric-projection-x=7', '--trimetric-projection-y=42', '--depth=3.2', '--apply-depth=red_black', '--dest-layer=3d-proj', '--smoothness=0.2', '/tmp/ink_ext_XXXXXX.svgDTI8AZ']

        """
        # above example generated with inkex.errormsg(repr(sys.argv))
        #
        inkex.localize()    # does not help for localizing my *.inx file
        inkex.Effect.__init__(self)
        try:
            self.tty = open("/dev/tty", 'w')
        except:
            from os import devnull
            self.tty = open(devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
        print("FlatProjection " + self.__version__, file=self.tty)

        self.OptionParser.add_option(
            "--tab",  # NOTE: value is not used.
            action="store", type="string", dest="tab", default="settings",
            help="The active tab when Apply was pressed. One of settings, advanced, about")

        self.OptionParser.add_option(
            "--rotation_type", action="store", type="string", dest="rotation_type", default="standard_rotation",
            help="The active rotation type tab when Apply was pressed. Oneof standard_rotation, manual_rotation")

        self.OptionParser.add_option(
            "--projection_type", action="store", type="string", dest="projection_type", default="standard_projection",
            help="The active projection type tab when Apply was pressed. One of standard_projection, trimetric_projection")

        self.OptionParser.add_option(
            "--standard_rotation", action="store", type="string", dest="standard_rotation", default="None",
            help="one of None, x-90, x+90, y-90, y+90, z-90, z+90. Used when rotation_type=standard_rotation")


        self.OptionParser.add_option(
            "--manual_rotation_x", action="store", type="float", dest="manual_rotation_x", default=float(90.0),
            help="Rotation angle about X-Axis. Used when rotation_type=manual_rotation")

        self.OptionParser.add_option(
            "--manual_rotation_y", action="store", type="float", dest="manual_rotation_y", default=float(0.0),
            help="Rotation angle about Y-Axis. Used when rotation_type=manual_rotation")

        self.OptionParser.add_option(
            "--manual_rotation_z", action="store", type="float", dest="manual_rotation_z", default=float(0.0),
            help="Rotation angle about Z-Axis. Used when rotation_type=manual_rotation")

        self.OptionParser.add_option(
            "--standard_projection", action="store", type="string", dest="standard_projection", default="7,42",
            help="One of the DIN ISO 128-30 axonometric projections: '7,42' (dimetric left), '42,7' (dimetric right), '30,30' (isometric). Used when projection_type=standard_projection.")

        self.OptionParser.add_option(
            "--standard_projection_autoscale", action="store", type="inkbool", dest="standard_projection_autoscale", default=True,
            help="scale isometric and dimetric projection so that apparent lengths are original lengths. Used when projection_type=standard_projection")


        self.OptionParser.add_option(
            '--trimetric_projection_y', dest='trimetric_projection_y', type='float', default=float(19.4), action='store',
            help='Manally define a projection, by first(!) rotating about the y-axis. Used when projection_type=trimetric_projection')

        self.OptionParser.add_option(
            '--trimetric_projection_x', dest='trimetric_projection_x', type='float', default=float(69.7), action='store',
            help='Manally define a projection, by second(!) rotating about the x-axis. Used when projection_type=trimetric_projection')


        self.OptionParser.add_option(
            "--depth", action="store", type="float", dest="depth", default=float(10.0),
            help="Extrusion length along the Z-axis. Applied to some, all, or none paths of the svg object, to convert it to a 3D object.")

        self.OptionParser.add_option(
            "--apply_depth", action="store", type="string", dest="apply_depth", default="red",
            help="Stroke color where depth is applied. One of red, red_black, green, green_blue, not_red, not_red_black, not_green, not_green_blue, any, none")

        self.OptionParser.add_option(
            '--dest_layer', dest='dest_layer', type='string', default='3d-proj', action='store',
            help='Place transformed objects into a specific svg document layer. Empty preserves layer.')

        self.OptionParser.add_option(
            '--smoothness', dest='smoothness', type='float', default=float(0.2), action='store',
            help='Curve smoothing (less for more [0.0001 .. 5]). Default: 0.2')


        self.OptionParser.add_option('-V', '--version',
          action = 'store_const', const=True, dest = 'version', default = False,
          help='Just print version number ("'+self.__version__+'") and exit.')


    def colorname2rgb(self, name):
        if name is None:      return None
        if name == 'none':    return False
        if name == 'any':     return True
        if name == 'red':     return [ 255, 0, 0]
        if name == 'green':   return [ 0, 255, 0]
        if name == 'blue':    return [ 0, 0, 255]
        if name == 'black':   return [ 0, 0, 0]
        if name == 'white':   return [ 255, 255, 255]
        if name == 'cyan':    return [ 0, 255, 255]
        if name == 'magenta': return [ 255, 0, 255]
        if name == 'yellow':  return [ 255, 255, 0]
        raise ValueError("unknown colorname: "+name)


    def is_extrude_color(self, svg, node, apply_color):
        """
        apply_color is one of the option values defined for the --apply_depth option
        """
        apply_color = re.split('[ _-]', apply_color.lower())
        nomatch = False
        if apply_color[0] == 'not':
          nomatch = True
          apply_color = apply_color[1:]
        for c in apply_color:
          if svg.matchStrokeColor(node, self.colorname2rgb(c)):
            return(not nomatch)
        return nomatch

    def find_selected_id(self, node):
        while node is not None:
          id = node.attrib.get('id', '')
          if id in self.selected: return id
          node = node.getparent()
        return None


    def effect(self):
        smooth = float(self.options.smoothness) # svg.smoothness to be deprecated!
        pg = LinearPathGen(smoothness=smooth)
        svg = InkSvg(document=self.document, pathgen=pg, smoothness=smooth)

        # Viewbox handling
        svg.handleViewBox()

        if self.options.version:
            print("Version "+self.__version__)
            sys.exit(0)

        ## First find or create find the destination layer
        ns = { 'svg': 'http://www.w3.org/2000/svg',
               'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
               'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd' }
        dest_layer = None
        for i in self.current_layer.findall("../*[@inkscape:groupmode='layer']", ns):        # all potential layers
            if self.options.dest_layer in (i.attrib.get('id', ''), i.attrib.get('label', ''), i.attrib.get('name', '')):
                dest_layer = i
        if dest_layer is None:
            # print('Creating dest_layer', self.options.dest_layer, file=self.tty)
            dest_layer = inkex.etree.SubElement(self.current_layer.find('..'), 'g', {
              inkex.addNS('label','inkscape'): self.options.dest_layer,
              inkex.addNS('groupmode','inkscape'): 'layer',
              'id': self.options.dest_layer })
        print('dest_layer', dest_layer, dest_layer.attrib, file=self.tty)

        # Second traverse the document (or selected items), reducing
        # everything to line segments.  If working on a selection,
        # then determine the selection's bounding box in the process.
        # (Actually, we just need to know it's extrema on the x-axis.)

        if self.options.ids:
            # Traverse the selected objects
            for id in self.options.ids:
                transform = svg.recursivelyGetEnclosingTransform(self.selected[id])
                svg.recursivelyTraverseSvg([self.selected[id]], transform)
        else:
            # Traverse the entire document building new, transformed paths
            svg.recursivelyTraverseSvg(self.document.getroot(), svg.docTransform)


        ## First simplification: paths_tupls[]
        ## Remove the bounding boxes from paths
        ## from (<Element {http://www.w3.org/2000/svg}path at 0x7fc446a583b0>,
        ##                  [[[[207, 744], [264, 801]], [207, 264, 744, 801]], [[[207, 801], [264, 744]], [207, 264, 744, 801]], ...])
        ## to   (<Element {http://www.w3.org/2000/svg}path at 0x7fc446a583b0>,
        ##                  [[[207, 744], [264, 801]],                         [[207, 801], [264, 744]]], ... ]
        ##
        paths_tupls = []
        for tup in svg.paths:
            node = tup[0]
            ll = []
            for e in tup[1]:
                ll.append(e[0])
            paths_tupls.append( (node, ll) )
        self.paths = None       # free some memory

        print(repr(paths_tupls), self.selected, svg.dpi, self.current_layer, file=self.tty)

        depth = self.options.depth * 25.4 / svg.dpi         # convert from mm to svg units

        dest_ids = {}    # map from src_id to dest_id, so that we know if we already have one, or if we need to create one.
        dest_g = {}      # map from dest_id to (group element, suffix)
        def find_dest_g(node, dest_layer):
            src_id = self.find_selected_id(node)
            if src_id in dest_ids:
              return dest_g[dest_ids[src_id]]
            existing_ids = map(lambda x: x.attrib.get('id', ''), list(dest_layer))
            n = 0;
            id = src_id+'_'+str(n)
            while id in existing_ids:
              n = n+1
              id = src_id+'_'+str(n)
            dest_ids[src_id] = id
            src_path = self.current_layer.attrib.get('id','')+'/'+src_id
            g = inkex.etree.SubElement(dest_layer, 'g', { 'id': id, 'src': src_path })
            # created in reverse order, so that g1 sits on top of the visibility stack
            g3 = inkex.etree.SubElement(g, 'g', { 'id': id+'_3', 'src': src_path })
            g2 = inkex.etree.SubElement(g, 'g', { 'id': id+'_2', 'src': src_path })
            g1 = inkex.etree.SubElement(g, 'g', { 'id': id+'_1', 'src': src_path })
            dest_g[id] = ( g1, g2, g3, '_'+str(n)+'_' )
            return dest_g[id]


        def points_to_svgd(p, scale=1.0):
          " convert list of points into a closed SVG path list"
          f = p[0]
          p = p[1:]
          closed = False
          if abs(p[-1][0]-f[0]) < 0.000001 and abs(p[-1][1]-f[1]) < 0.000001:
            p = p[:-1]
            closed = True
          svgd = 'M%.6f,%.6f' % (f[0]*scale, f[1]*scale)
          for x in p:
            svgd += 'L%.6f,%.6f' % (x[0]*scale, x[1]*scale)
          if closed:
            svgd += 'z'
          return svgd

        def paths_to_svgd(paths, scale=1.0):
          " multiple disconnected lists of points can exist in one svg path"
          d = ''
          for p in paths:
            d += points_to_svgd(p, scale) + ' '
          return d[:-1]

        # shapes from http://mathworld.wolfram.com/RotationMatrix.html
        def genRx(theta):
          "A rotation matrix about the X axis. Example: Rx = genRx(np.radians(30))"
          c, s = np.cos(theta), np.sin(theta)
          return np.array( ((1, 0, 0), (0, c, s), (0, -s, c)) )

        def genRy(theta):
          "A rotation matrix about the Y axis. Example: Ry = genRy(np.radians(30))"
          c, s = np.cos(theta), np.sin(theta)
          return np.array( ((c, 0, -s), (0, 1, 0), (s, 0, c)) )

        def genRz(theta):
          "A rotation matrix about the Z axis. Example: Rz = genRz(np.radians(30))"
          c, s = np.cos(theta), np.sin(theta)
          return np.array( ((c, s, 0), (-s, c, 0), (0, 0, 1)) )

        missing_id = int(10000*time.time())     # use a timestamp, in case there are objects without id.
        for tupl in paths_tupls:
            (elem,paths) = tupl
            for path in paths:
                (g1, g2, g3, suf) = find_dest_g(elem, dest_layer)
                path_id = elem.attrib.get('id', '')+suf
                style = elem.attrib.get('style', '')
                if path_id == suf:
                  path_id = 'pathx'+str(missing_id)+suf
                  missing_id += 1

                # populate g1 with all colors
                inkex.etree.SubElement(g1, 'path', { 'id': path_id+'1', 'style': style, 'd': paths_to_svgd(paths, 25.4/svg.dpi) })

                if self.is_extrude_color(svg, elem, self.options.apply_depth):
                  # populate also g2 and g3, with selected colors only
                  inkex.etree.SubElement(g2, 'path', { 'id': path_id+'2', 'style': style, 'd': paths_to_svgd(paths, 25.4/svg.dpi) })
                  inkex.etree.SubElement(g3, 'path', { 'id': path_id+'3', 'style': style, 'd': paths_to_svgd(paths, 25.4/svg.dpi) })


if __name__ == '__main__':
    e = FlatProjection()
    e.affect()
