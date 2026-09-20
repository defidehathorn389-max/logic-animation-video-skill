# 葬经人 B 代式封面：纯白底 + 居中单个彩色道具 + 大号黑字4字局名(白描边+软阴影) + 下方小字系列名
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys
W,H = 1440,1080
FONT='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
def make(prop_path, juming, series='墨问 · 逻辑局', out='cover-4x3.jpg'):
    im=Image.new('RGB',(W,H),'white')
    prop=Image.open(prop_path).convert('RGBA')
    # 白底图标：把近白像素转透明
    import numpy as np; a=np.array(prop); m=(a[...,:3]>235).all(-1); a[m,3]=0; prop=Image.fromarray(a)
    prop=prop.crop(prop.getbbox())
    ph=int(H*0.40); pw=int(prop.width*ph/prop.height)
    if pw>W*0.5: pw=int(W*0.5); ph=int(prop.height*pw/prop.width)
    prop=prop.resize((pw,ph),Image.LANCZOS)
    im.paste(prop,((W-pw)//2,int(H*0.10)),prop)
    txt=' '.join(juming) if len(juming)<=4 else juming
    layer=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(layer)
    size=int(W*0.19)
    while True:
        f=ImageFont.truetype(FONT,size); bb=d.textbbox((0,0),txt,font=f); tw=bb[2]-bb[0]
        if tw<=W*0.86: break
        size-=4
    th=bb[3]-bb[1]
    x=(W-tw)//2-bb[0]; y=int(H*0.60)-bb[1]
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).text((x+8,y+10),txt,font=f,fill=(0,0,0,110)); sh=sh.filter(ImageFilter.GaussianBlur(10))
    im.paste(sh,(0,0),sh)
    d.text((x,y),txt,font=f,fill='black',stroke_width=int(size*0.06),stroke_fill='white')
    im.paste(layer,(0,0),layer)
    fs=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',int(W*0.03))
    d2=ImageDraw.Draw(im); sb=d2.textbbox((0,0),series,font=fs)
    d2.text(((W-(sb[2]-sb[0]))//2, int(H*0.88)),series,font=fs,fill=(120,120,120))
    im.save(out,quality=92); print(out,im.size)
if __name__=='__main__': make(*sys.argv[1:])
