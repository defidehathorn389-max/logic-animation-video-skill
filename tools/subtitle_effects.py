"""Optional original caption motion + procedural foley. No reference media or project data.
Existing approved karaoke styling stays separate. Timing input must be acoustic/event based.
2D roll/flip are approximations, not proprietary editor preset reproductions.
"""
import math
import numpy as np
from PIL import Image,ImageFilter
PRESETS={
 'drop':(.24,'soft_thump'), 'flip':(.28,'air_swipe'), 'rise':(.26,'tick'),
 'impact':(.22,'soft_thump'), 'roll':(.32,'air_swipe'), 'snow':(.38,'glass_ping'),
 'shake':(.32,'low_pulse'), 'zoom':(.22,'soft_thump'),
 'zoom_shake':(.28,'soft_thump'), 'dissolve':(.30,'air_swipe'), 'fade':(.30,'glass_ping')}
def pose(name,elapsed,index=0):
 if name not in PRESETS:raise ValueError('Unknown preset')
 duration=PRESETS[name][0];delay=index*.035 if name in ('rise','snow') else 0
 u=max(0.,min(1.,(elapsed-delay)/duration));e=1-(1-u)**3
 p=dict(dx=0.,dy=0.,sx=1.,sy=1.,rotation=0.,opacity=0. if elapsed<delay else 1.,blur=0.)
 if name=='drop':p['dy']=-28*(1-e)
 elif name=='flip':p['sy']=max(.025,math.sin(u*math.pi/2));p['dy']=-10*(1-e)
 elif name=='rise':p['dy']=24*(1-e);p['rotation']=12*(1-e)
 elif name=='impact':p['sx']=p['sy']=1+.18*math.sin(math.pi*u)*(1-u);p['blur']=3*(1-e)
 elif name=='roll':p['dy']=20*(1-e);p['sy']=max(.05,math.sin(u*math.pi/2));p['rotation']=-8*(1-e)
 elif name=='snow':p['dy']=-26*(1-e);p['dx']=math.sin(index*2.3)*15*(1-e);p['rotation']=math.sin(index+1)*16*(1-e);p['opacity']*=e
 elif name=='shake':p['dx']=6*math.sin(u*8*math.pi)*(1-u);p['dy']=2*math.sin(u*6*math.pi)*(1-u)
 elif name=='zoom':p['sx']=p['sy']=.85+.15*e
 elif name=='zoom_shake':p['sx']=p['sy']=.88+.12*e;p['dx']=5*math.sin(u*8*math.pi)*(1-u)
 elif name in ('fade','dissolve'):p['opacity']*=e
 return p

def transform(rgba,name,elapsed,index=0):
 p=pose(name,elapsed,index);im=rgba.convert('RGBA');im=im.resize((max(1,round(im.width*p['sx'])),max(1,round(im.height*p['sy']))),Image.Resampling.BICUBIC)
 if p['rotation']:im=im.rotate(p['rotation'],resample=Image.Resampling.BICUBIC,expand=True)
 if p['blur']>.1:im=im.filter(ImageFilter.GaussianBlur(p['blur']))
 a=np.array(im.getchannel('A'),dtype=float)
 if name=='dissolve':
  noise=np.random.default_rng(1947+index).random(a.shape);a*=noise<=p['opacity']
 else:a*=p['opacity']
 im.putalpha(Image.fromarray(np.uint8(np.clip(a,0,255))))
 return im,(p['dx'],p['dy'])

def synth(kind,sr=24000,peak_db=-32,seed=1947):
 """Original sound synthesis. Peak ceiling is not a LUFS or masking guarantee."""
 durations={'soft_thump':.14,'air_swipe':.18,'tick':.045,'glass_ping':.25,'low_pulse':.28}
 if kind not in durations:raise ValueError('Unknown cue')
 t=np.arange(round(durations[kind]*sr))/sr;rng=np.random.default_rng(seed);noise=rng.standard_normal(len(t));u=t/durations[kind]
 if kind=='soft_thump':x=np.sin(2*np.pi*(130*t-180*t*t))*np.exp(-35*t)+.12*noise*np.exp(-90*t)
 elif kind=='air_swipe':x=np.convolve(noise,np.ones(5)/5,mode='same')*np.sin(np.pi*u)**2
 elif kind=='tick':x=(np.sin(2*np.pi*1500*t)+.3*noise)*np.exp(-130*t)
 elif kind=='glass_ping':x=(np.sin(2*np.pi*1450*t)+.35*np.sin(2*np.pi*2200*t))*np.exp(-24*t)
 else:x=np.sin(2*np.pi*82*t)*np.sin(np.pi*u)**2
 fade=min(round(.004*sr),len(x)//2);x[:fade]*=np.linspace(0,1,fade);x[-fade:]*=np.linspace(1,0,fade);x*=10**(peak_db/20)/max(np.max(abs(x)),1e-12)
 return x.astype('float32')

def mix_events(voice,events,sr=24000,cooldown=.12):
 """Sparse phrase/action cues only; rejects negatives/too-close cues. No per-letter firing."""
 out=np.asarray(voice,dtype='float32').copy();last=-math.inf
 for event in sorted(events,key=lambda e:e['time']):
  when=float(event['time'])
  if when<0 or when-last<cooldown:raise ValueError('Negative or crowded cue')
  cue=synth(event['kind'],sr,event.get('peak_db',-32));start=round(when*sr)
  if start>=len(out):raise ValueError('Cue beyond audio')
  n=min(len(cue),len(out)-start);out[start:start+n]+=cue[:n];last=when
 if np.max(abs(out))>10**(-1/20):raise ValueError('Mix exceeds -1dBFS sample peak; lower cue gain and measure true peak separately')
 return out
