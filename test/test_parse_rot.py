from __future__ import print_function
import re

def parse_rot_expr(expr):
  r = []
  expr_n=0
  rot = None
  splitter = ';'
  if splitter not in expr:
    splitter = ','
  for term in re.sub("\s+", '', expr).split(splitter):
    m = re.match('([xyz][:=])?(.*)', re.sub(',','.',term), re.I)
    if m:
      p = (m.group(1) or '').lower() 
      v = float(m.group(2))
      if 'x' in p:
        rot = 'rotX'
      elif 'y' in p:
        rot = 'rotY'
      elif 'z' in p:
        rot = 'rotZ'
      else:
        rot = 'rot' + ('X', 'Y', 'Z')[expr_n%3]
      r.append((rot, v))
    else:
      print("Unknown rotation expression: '%s'. Expected X:nnn" % term, file=sys.stderr)
    expr_n += 1
  return r

print(parse_rot_expr(" z: 2;4 ; Y:-3.5;x=4,5; 333"))
print(parse_rot_expr(" z: 2,4 , Y:-3.5,x=4.5, 333"))
