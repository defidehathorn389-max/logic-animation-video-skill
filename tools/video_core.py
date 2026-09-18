"""Reusable 16:9 drawing primitives extracted from the existing Skill renderer.
Importing this module never synthesizes audio or starts a render.
"""
import os, math
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
S=1.5
BG='#bdbdbd';INK='#252525';GRAY='#727272';GOLD='#f7ca54';RED='#a94849';WHITE='#f8f8f5'
FONTP=os.environ.get('CHINESE_FONT','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
BOLDP=os.environ.get('CHINESE_FONT_BOLD','/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
fonts={}
def configure(scale):
    global S
    S=scale;fonts.clear()
def ft(s,b=False):
 k=(s,b)
 if k not in fonts:fonts[k]=ImageFont.truetype(BOLDP if b else FONTP,round(s*S),index=2)
 return fonts[k]

def scale_xy(xy):
 if isinstance(xy[0],(tuple,list,np.ndarray)):return [(round(x*S),round(y*S)) for x,y in xy]
 return tuple(round(v*S) for v in xy)

class Draw:
 def __init__(self,im):self.d=ImageDraw.Draw(im)
 def line(self,xy,fill=INK,width=2):self.d.line(scale_xy(xy),fill=fill,width=max(1,round(width*S)),joint='curve')
 def ellipse(self,xy,fill=None,outline=None,width=2):self.d.ellipse(scale_xy(xy),fill=fill,outline=outline,width=max(1,round(width*S)))
 def rectangle(self,xy,fill=None,outline=None,width=2):self.d.rectangle(scale_xy(xy),fill=fill,outline=outline,width=max(1,round(width*S)))
 def round(self,xy,r=10,fill=WHITE,outline=None,width=2):self.d.rounded_rectangle(scale_xy(xy),radius=round(r*S),fill=fill,outline=outline,width=max(1,round(width*S)))
 def polygon(self,xy,fill,outline=None):self.d.polygon(scale_xy(xy),fill=fill,outline=outline,width=round(2*S))
 def arc(self,xy,a,b,fill=INK,width=2):self.d.arc(scale_xy(xy),a,b,fill=fill,width=round(width*S))
 def text(self,x,y,s,size=28,fill=INK,b=False,anchor='mm',stroke=0):self.d.text((round(x*S),round(y*S)),s,font=ft(size,b),fill=fill,anchor=anchor,stroke_width=round(stroke*S),stroke_fill='#646464')

def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)

def mix(a,b,x):return a+(b-a)*ease(x)

def clamp(x):return max(0,min(1,x))

def arrow(d,x1,y1,x2,y2,color=INK,width=2):
 d.line([(x1,y1),(x2,y2)],color,width);ang=math.atan2(y2-y1,x2-x1)
 d.polygon([(x2,y2),(x2-10*math.cos(ang-.42),y2-10*math.sin(ang-.42)),(x2-10*math.cos(ang+.42),y2-10*math.sin(ang+.42))],color)

def cross(d,x,y,r=15):d.line([(x-r,y-r),(x+r,y+r)],RED,6);d.line([(x-r,y+r),(x+r,y-r)],RED,6)

def check(d,x,y):d.line([(x-10,y),(x-2,y+8),(x+14,y-11)],'#46634e',4)

def heading(d,a,b=''):
 d.text(640,77,a,35,b=True)
 if b:d.text(640,128,b,21,GRAY)

def bubble(d,x,y,txt):
 tw=len(txt)*21+30;d.round((x-tw/2,y-23,x+tw/2,y+23),20,WHITE,INK)
 d.polygon([(x-8,y+22),(x+4,y+35),(x+10,y+21)],WHITE)
 d.text(x,y,txt,21,b=True)
