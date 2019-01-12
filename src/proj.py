#! /usr/bin/python3
#
# proj.py -- apply a transformation matrix to an svg object
#
# (C) 2019 Juergen Weigert <juergen@fabmail.org>
# Distribute under GPLv2 or ask.
#
# recursivelyTraverseSvg() is originally from eggbot. Thank!
# inkscape-paths2openscad and inkscape-silhouette contain copies of recursivelyTraverseSvg()
# with almost identical features, but different inmplementation details. The version used here is derived from
# inkscape-paths2openscad.
#
# python2 compatibility:
from __future__ import print_function

import sys

sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):
  sys.path.append('C:\Program Files\Inkscape\share\extensions')
elif sys_platform.startswith('darwin'):
  sys.path.append('~/.config/inkscape/extensions')
else:   # Linux
  sys.path.append('/usr/share/inkscape/extensions/')


## INLINE_BLOCK_START
# for easier distribution, our Makefile can inline these imports when generating 3d-projection.py from src/proj.py
from inksvg import InkSvg, LinearPathGen
## INLINE_BLOCK_END

import json
import inkex
import gettext


# python2 compatibility. Inkscape runs us with python2!
if sys.version_info.major < 3:
        def bytes(tupl):
                return "".join(map(chr, tupl))


class Projection3D(inkex.Effect):

    # CAUTION: Keep in sync with 3d-projection.inx and 3d-projection_de.inx
    __version__ = '0.2'         # >= max(src/proj.py:__version__, src/inksvg.py:__version__)

    def __init__(self):
        """
Option parser example:

'proj.py', '--tab=settings', '--rotation-type=standard_rotation', '--standard-rotation=x-90', '--manual_rotation_x=90', '--manual_rotation_y=0', '--manual_rotation_z=0', '--projection-type=standard_projection', '--standard-projection=7,42', '--standard-projection-autoscale=true', '--trimetric-projection-x=7', '--trimetric-projection-y=42', '--depth=3.2', '--apply-depth=red_black', '--dest-layer=3d-proj', '--smoothness=0.2', '/tmp/ink_ext_XXXXXX.svgDTI8AZ']

        """
        inkex.localize()    # does not help for localizing my *.inx file
        inkex.Effect.__init__(self)

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
            '--trimetric_projection_x', dest='trimetric_projection_x', type='float', default=float(7.0), action='store',
            help='apparent angle of the x-axis in free trimetric projection mode. Measured from the negative world x-axis. Used when projection_type=trimetric_projection')

        self.OptionParser.add_option(
            '--trimetric_projection_y', dest='trimetric_projection_y', type='float', default=float(42.0), action='store',
            help='apparent angle of the y-axis in free trimetric projection mode. Measured from the positive world x-axis. Used when projection_type=trimetric_projection')


        self.OptionParser.add_option(
            "--depth", action="store", type="float", dest="depth", default=float(10.0),
            help="Extrusion length along the Z-axis. Applied to some, all, or none paths of the svg object, to convert it to a 3d object.")

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


    def effect(self):
        smooth = float(self.options.smoothness) # svg.smoothness to be deprecated!
        pg = LinearPathGen(smoothness=smooth)
        svg = InkSvg(document=self.document, pathgen=pg, smoothness=smooth)

        # Viewbox handling
        svg.handleViewBox()

        if self.options.version:
            print("Version "+self.__version__)
            sys.exit(0)

        inkex.errormsg(gettext.gettext('ERROR: =================== Unfinsihed work here ============================'))
        sys.exit(1)

        cut_opt  = self.cut_options()
        mark_opt = self.mark_options()
        if cut_opt is None and mark_opt is None:
          inkex.errormsg(gettext.gettext('ERROR: Enable Cut or Mark or both.'))
          sys.exit(1)
        if cut_opt is not None and mark_opt is not None and cut_opt['color'] == mark_opt['color']:
          inkex.errormsg(gettext.gettext('ERROR: Choose different color settings for Cut and Mark. Both are "'+mark_opt['color']+'"'))
          sys.exit(1)
        mark_color = self.colorname2rgb(None if mark_opt is None else mark_opt['color'])
        cut_color  = self.colorname2rgb(None if  cut_opt is None else  cut_opt['color'])

        # First traverse the document (or selected items), reducing
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
        ## Remove the bounding boxes from paths. Replace the object with its id. We can still access color and style attributes through the id.
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

        ## Reposition the graphics, so that a corner or the center becomes origin [0,0]
        ## Convert from dots-per-inch to mm.
        ## Separate into Cut and Mark lists based on element style.
        paths_list = []
        paths_list_cut = []
        paths_list_mark = []
        dpi2mm = 25.4 / svg.dpi

        (xoff,yoff) = (svg.xmin, svg.ymin)                      # top left corner is origin
        # (xoff,yoff) = (svg.xmax, svg.ymax)                      # bottom right corner is origin
        # (xoff,yoff) = ((svg.xmax+svg.xmin)/2.0, (svg.ymax+svg.ymin)/2.0)       # center is origin

        for tupl in paths_tupls:
                (elem,paths) = tupl
                for path in paths:
                        newpath = []
                        for point in path:
                                newpath.append([(point[0]-xoff) * dpi2mm, (point[1]-yoff) * dpi2mm])
                        paths_list.append(newpath)
                        is_mark = svg.matchStrokeColor(elem, mark_color)
                        is_cut  = svg.matchStrokeColor(elem,  cut_color)
                        if is_cut and is_mark:          # never both. Named colors win over 'any'
                                if mark_opt['color'] == 'any':
                                        is_mark = False
                                else:                   # cut_opt['color'] == 'any'
                                        is_cut = False
                        if is_cut:  paths_list_cut.append(newpath)
                        if is_mark: paths_list_mark.append(newpath)
        paths_tupls = None      # save some memory
        bbox = [[(svg.xmin-xoff)*dpi2mm, (svg.ymin-yoff)*dpi2mm], [(svg.xmax-xoff)*dpi2mm, (svg.ymax-yoff)*dpi2mm]]

        rd = Ruida()
        # bbox = rd.boundingbox(paths_list)     # same as above.

        if self.options.bbox_only:
                paths_list = [[ [bbox[0][0],bbox[0][1]], [bbox[1][0],bbox[0][1]], [bbox[1][0],bbox[1][1]],
                                [bbox[0][0],bbox[1][1]], [bbox[0][0],bbox[0][1]] ]]
                paths_list_cut = paths_list
                paths_list_mark = paths_list
                if cut_opt['color']  == 'any' or mark_opt is None: paths_list_mark = []
                if mark_opt['color'] == 'any' or  cut_opt is None: paths_list_cut  = []      # once is enough.
        if self.options.move_only:
                paths_list      = rd.paths2moves(paths_list)
                paths_list_cut  = rd.paths2moves(paths_list_cut)
                paths_list_mark = rd.paths2moves(paths_list_mark)

        if self.options.dummy:
                with open('/tmp/thunderlaser.json', 'w') as fd:
                        json.dump({
                                'paths_bbox': bbox,
                                'cut_opt': cut_opt, 'mark_opt': mark_opt,
                                'paths_unit': 'mm', 'svg_resolution': svg.dpi, 'svg_resolution_unit': 'dpi',
                                'freq1': self.options.freq1, 'freq1_unit': 'kHz',
                                'paths': paths_list,
                                'cut':  { 'paths':paths_list_cut,  'color': cut_color  },
                                'mark': { 'paths':paths_list_mark, 'color': mark_color },
                                }, fd, indent=4, sort_keys=True, encoding='utf-8')
                print("/tmp/thunderlaser.json written.", file=sys.stderr)
        else:
                if len(paths_list_cut) > 0 and len(paths_list_mark) > 0:
                  nlay=2
                else:
                  nlay=1

                if bbox[0][0] < 0 or bbox[0][1] < 0:
                        inkex.errormsg(gettext.gettext('Warning: negative coordinates not implemented in class Ruida(), truncating at 0'))
                # rd.set(globalbbox=bbox)       # Not needed. Even slightly wrong.
                rd.set(nlayers=nlay)

                l=0
                if mark_opt is not None:
                  if len(paths_list_mark) > 0:
                    cc = mark_color if type(mark_color) == list else [128,0,64]
                    rd.set(layer=l, speed=mark_opt['speed'], color=cc)
                    rd.set(layer=l, power=[mark_opt['minpow'], mark_opt['maxpow']])
                    rd.set(layer=l, paths=paths_list_mark)
                    l += 1
                  else:
                    if mark_opt['color'] != 'any' and len(paths_list_cut) == 0:
                      inkex.errormsg(gettext.gettext('ERROR: mark line color "'+mark_opt['color']+'": nothing found.'))
                      sys.exit(0)

                if cut_opt is not None:
                  if len(paths_list_cut) > 0:
                    cc = cut_color if type(cut_color) == list else [128,0,64]
                    rd.set(layer=l, speed=cut_opt['speed'], color=cc)
                    rd.set(layer=l, power=[cut_opt['minpow'], cut_opt['maxpow']])
                    rd.set(layer=l, paths=paths_list_cut)
                    l += 1
                  else:
                    if cut_opt['color'] != 'any' and len(paths_list_mark) == 0:
                      inkex.errormsg(gettext.gettext('ERROR: cut line color "'+cut_opt['color']+'": nothing found.'))
                      sys.exit(0)

                device_used = None
                for device in self.options.devicelist.split(','):
                    fd = None
                    try:
                        fd = open(device, 'wb')
                    except:
                        pass
                    if fd is not None:
                        rd.write(fd)
                        # print(device+" written.", file=sys.stderr)
                        device_used = device
                        break
                if device_used is None:
                        inkex.errormsg(gettext.gettext('Warning: no usable devices in device list (or bad directoy): '+self.options.devicelist))


if __name__ == '__main__':
    e = ThunderLaser()
    e.affect()
