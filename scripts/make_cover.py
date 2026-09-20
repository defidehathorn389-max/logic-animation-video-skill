# 封面三版式（§2.6）：白底 + 居中单个彩色道具（必须取自正片素材）+ 4 字局名（粗宋黑字白描边软阴影）+ 灰色系列名
# 用法: make_cover.py <道具png> <局名> [系列名] [输出目录] [ratios=3x4,4x3,16x9]
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys, os
import numpy as np
FONT='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
FONT_S='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
SIZES={'3x4':(1080,1440),'4x3':(1440,1080),'16x9':(1920,1080)}
# 每个版式的布局参数：道具顶部/高度比例、文字基线比例、文字最大宽度比例、字号比例(相对宽)、系列名位置
LAYOUT={
 '4x3': dict(prop_top=0.10, prop_h=0.40, prop_wmax=0.50, text_y=0.60, text_wmax=0.86, size=0.19, series_y=0.88),
 '3x4': dict(prop_top=0.12, prop_h=0.30, prop_wmax=0.70, text_y=0.56, text_wmax=0.90, size=0.22, series_y=0.86),
 '16x9':dict(prop_top=0.08, prop_h=0.44, prop_wmax=0.40, text_y=0.60, text_wmax=0.70, size=0.15, series_y=0.88),
}
def load_prop(p):
    prop=Image.open(p).convert('RGBA'); a=np.array(prop)
    m=(a[...,:3]>235).all(-1)&(a[...,3]>0); a[m,3]=0   # 白底转透明
    prop=Image.fromarray(a); return prop.crop(prop.getbbox())
def render(prop, juming, series, ratio):
    W,H=SIZES[ratio]; L=LAYOUT[ratio]
    im=Image.new('RGB',(W,H),'white')
    ph=int(H*L['prop_h']); pw=int(prop.width*ph/prop.height)
    if pw>W*L['prop_wmax']: pw=int(W*L['prop_wmax']); ph=int(prop.height*pw/prop.width)
    p=prop.resize((pw,ph),Image.LANCZOS)
    # 道具在 prop_top..prop_top+prop_h 区间内垂直居中
    py=int(H*L['prop_top'])+(int(H*L['prop_h'])-ph)//2
    im.paste(p,((W-pw)//2,py),p)
    txt=' '.join(juming) if len(juming)<=4 else juming
    layer=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
    size=int(W*L['size'])
    while True:
        f=ImageFont.truetype(FONT,size); bb=d.textbbox((0,0),txt,font=f); tw=bb[2]-bb[0]
        if tw<=W*L['text_wmax'] or size<40: break
        size-=4
    x=(W-tw)//2-bb[0]; y=int(H*L['text_y'])-bb[1]
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((x+8,y+10),txt,font=f,fill=(0,0,0,110)); sh=sh.filter(ImageFilter.GaussianBlur(10))
    im.paste(sh,(0,0),sh)
    d.text((x,y),txt,font=f,fill='black',stroke_width=int(size*0.06),stroke_fill='white')
    im.paste(layer,(0,0),layer)
    fs=ImageFont.truetype(FONT_S,int(min(W,H)*0.03)); d2=ImageDraw.Draw(im); sb=d2.textbbox((0,0),series,font=fs)
    d2.text(((W-(sb[2]-sb[0]))//2,int(H*L['series_y'])),series,font=fs,fill=(120,120,120))
    return im
def make(prop_path, juming, series='墨问 · 逻辑局', outdir='.', ratios='3x4,4x3,16x9'):
    prop=load_prop(prop_path); os.makedirs(outdir,exist_ok=True); outs=[]
    for r in ratios.split(','):
        im=render(prop,juming,series,r); o=os.path.join(outdir,f'cover-{r}.jpg'); im.save(o,quality=92); outs.append(o); print(o,im.size)
    return outs
if __name__=='__main__': make(*sys.argv[1:])
