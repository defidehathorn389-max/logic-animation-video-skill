"""Shared publishing pipeline: SC typography, acoustic captions, poses, sound, QA."""
import math,json,wave,subprocess,hashlib,re,os
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import imageio_ffmpeg
FF=imageio_ffmpeg.get_ffmpeg_exe()
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';BOLD='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
class Episode:
 def __init__(self,p,scale=1,shared_assets=None,source_root=None):
  self.p=Path(p).resolve();self.shared=Path(shared_assets).resolve() if shared_assets else self.p.parent/'shared';self.repo=Path(source_root).resolve() if source_root else self.p.parents[2];self.scale=scale;self.spec=json.loads((self.p/'spec.json').read_text());self.meta=json.loads((self.p/'timeline.json').read_text());self.cues=json.loads((self.p/'char-alignment.json').read_text());self.starts=[s['start'] for s in self.meta['sections']];self.durations=[s['duration'] for s in self.meta['sections']];self.total=self.meta['total'];self.pause=self.meta['pause_start'];self.images={};self.sprites={}
  report_root=os.environ.get('LOGIC_VIDEO_REPORT_DIR')
  if not report_root:raise ValueError('Set LOGIC_VIDEO_REPORT_DIR to the private handoff task verification directory')
  self.reports=Path(report_root).resolve();self.reports.mkdir(parents=True,exist_ok=True)
  for kind,n in [('explain','character.png'),('think','pose-think.png'),('point','pose-point.png'),('reveal','pose-reveal.png')]:self.images[kind]=Image.open(self.shared/n).convert('RGBA')
  self.flat=[c for q in self.cues for c in q['chars'] if not c.get('punctuation')];self.full=''.join(c['char'] for c in self.flat)
 def at(self,fragment,end=False):
  frag=re.sub(r'[，。？！、；：\s]','',fragment);i=self.full.index(frag);return self.flat[i+len(frag)-1]['end'] if end else self.flat[i]['start']
 def progress(self,t,a,b):return max(0,min(1,(t-a)/max(.05,b-a)))
 def actor(self,im,kind,x=138,bottom=610,h=305):
  key=(kind,h,self.scale)
  if key not in self.sprites:
   sp=self.images[kind];self.sprites[key]=sp.resize((round(h*self.scale*sp.width/sp.height),round(h*self.scale)),Image.Resampling.LANCZOS)
  sp=self.sprites[key];im.paste(sp,(round(x*self.scale-sp.width/2),round(bottom*self.scale-sp.height)),sp)
 def captions(self,d,t):
  q=next((q for q in self.cues if q['start']<=t<q['end']+.12),None)
  if q is None:return
  f=ImageFont.truetype(FONT,round(29*self.scale),index=2);ww=[f.getlength(c)/self.scale for c in q['text']];x=640-sum(ww)/2
  for j,c in enumerate(q['chars']):
   age=t-c['start']
   if age<0:break
   pop=4*math.sin(min(1,age/.12)*math.pi) if age<.12 else 0
   color='#f7ca54' if c['start']<=t<c['end'] and not c.get('punctuation') else '#f8f8f5'
   d.text(x+ww[j]/2,673-pop,c['char'],29,color,stroke=2);x+=ww[j]
 def countdown(self,d,t,x=680,y=350):
  e=t-self.pause;n=max(1,3-int(e));p=e%1
  d.round((x-132,y-133,x+132,y+133),22,'#f8f8f5','#252525',2);d.text(x,y-94,'给你三秒，想一想',22,b=True)
  d.ellipse((x-58,y-58,x+58,y+58),None,'#ddddda',4);d.arc((x-58,y-58,x+58,y+58),-90,-90+360*(1-p),'#f7ca54',5)
  d.text(x,y-3,str(n),round(76+10*max(0,1-p/.15)),b=True);d.text(x,y+99,'3 · 2 · 1',19,'#727272')
 def prepare_audio(self,events=()):
  work=self.p/'work';work.mkdir(exist_ok=True);sr=24000;audio=np.zeros(round(self.total*sr))
  for i,at in enumerate(self.starts):
   src=self.repo/self.spec['source_audio']/f'{i+1:02}.wav';dst=work/f'paced-{i}.wav'
   subprocess.run([FF,'-y','-i',str(src),'-af',f"atempo={self.spec['rate']}",'-ar',str(sr),'-ac','1',str(dst)],capture_output=True,check=True)
   with wave.open(str(dst)) as w:a=np.frombuffer(w.readframes(w.getnframes()),np.int16)/32768
   st=round(at*sr);nn=min(len(a),len(audio)-st);audio[st:st+nn]+=a[:nn]
  def tone(at,f=660,vol=.045):
   n=int(.18*sr);tt=np.arange(n)/sr;v=vol*np.sin(2*np.pi*f*tt)*np.exp(-tt*30)*np.minimum(1,tt*300);j=round(at*sr);nn=min(n,len(audio)-j)
   if j>=0 and nn>0:audio[j:j+nn]+=v[:nn]
  for k in range(3):tone(self.pause+k,660+60*k,.065)
  for at in self.starts:tone(at,480,.022)
  for at in events:tone(at,1050,.035)
  t=np.arange(len(audio))/sr;bed=np.zeros_like(audio)
  for j,freq in enumerate([73.416,110,146.832,164.814]):bed+=(.34 if j<2 else .12)*np.sin(2*np.pi*freq*t+.05*np.sin(t*.3+j))*(.65+.35*np.sin(t*.17+j)**2)
  for k,at in enumerate(np.arange(2,self.total,4)):
   u=t-at;env=np.where(u>=0,(1-np.exp(-np.maximum(u,0)*7))*np.exp(-np.maximum(u,0)*1.4),0);bed+=.12*np.sin(2*np.pi*[293.665,220,261.626,164.814][k%4]*u)*env
  bed=bed/max(np.max(np.abs(bed)),1e-9)*.8;bed*=np.minimum(t/2,1)*np.minimum((self.total-t)/3,1)
  power=np.convolve(np.abs(audio),np.ones(960)/960,'same');duck=1-.37*np.clip(power/.045,0,1);bed*=10**(-25/20)*duck;audio+=bed
  peak=np.max(np.abs(audio));atten=min(1,.88/max(peak,1e-9));audio*=atten
  (self.reports/'audio-qa.json').write_text(json.dumps({'bgm_gain_db':-25,'duck_db_approx':-4,'peak_dbfs':float(20*np.log10(np.max(np.abs(audio)))),'final_safety_gain':float(atten),'source':'original procedural ambient bed; no third-party music'},indent=2))
  with wave.open(str(work/'mix.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((audio*32767).astype('<i2').tobytes())
 def render(self,func):
  p=self.p;work=p/'work';work.mkdir(exist_ok=True);sample=func(0);w,h=sample.size;body=work/'body.mp4';frames=math.ceil(self.total*30)
  cmd=[FF,'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r','30','-i','-','-i',str(work/'mix.wav'),'-vf','scale=1920:1080:flags=lanczos','-c:v','libx264','-preset','veryfast','-threads','1','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',str(body)]
  with (work/'encode.log').open('w') as log:
   proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=log,stderr=log)
   for k in range(frames):
    proc.stdin.write(func(k/30).tobytes())
    if k%600==0:print(p.name,k/30,'/',self.total,flush=True)
   proc.stdin.close();assert proc.wait()==0
  cmd=[FF,'-y','-i',str(self.shared/'intro.mp4'),'-i',str(body),'-i',str(self.shared/'outro.mp4'),'-filter_complex',f'[0:v]setpts=PTS-STARTPTS[v0];[1:v]setpts=PTS-STARTPTS[v1];[2:v]setpts=PTS-STARTPTS[v2];[0:a]aresample=48000,apad,atrim=duration=1,asetpts=PTS-STARTPTS[a0];[1:a]aresample=48000,apad,atrim=duration={frames/30},asetpts=PTS-STARTPTS[a1];[2:a]aresample=48000,apad,atrim=duration=3,asetpts=PTS-STARTPTS[a2];[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]','-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-threads','1','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(p/'video.mp4')]
  subprocess.run(cmd,capture_output=True,check=True)
  def ts(t):v=round(t*1000);return f'{v//3600000:02}:{v//60000%60:02}:{v//1000%60:02},{v%1000:03}'
  (p/'subtitles.srt').write_text(''.join(f"{i+1}\n{ts(q['start']+1)} --> {ts(q['end']+1.12)}\n{q['text']}\n\n" for i,q in enumerate(self.cues)))
  chars=json.loads(json.dumps(self.cues))
  for q in chars:
   q['start']+=1;q['end']+=1
   for c in q['chars']:c['start']+=1;c['end']+=1
  (p/'char-timing-final.json').write_text(json.dumps(chars,ensure_ascii=False,indent=2))
  r=subprocess.run([FF,'-v','error','-i',str(p/'video.mp4'),'-f','null','-'],capture_output=True)
  q={'decode_ok':r.returncode==0,'errors':r.stderr.decode(),'duration_seconds':frames/30+4,'resolution':[1920,1080],'fps':30,'sha256':hashlib.sha256((p/'video.mp4').read_bytes()).hexdigest(),'bytes':(p/'video.mp4').stat().st_size,'character_alignment':'acoustic DTW + silence trim; machine estimates not manual zero-error proof'}
  (self.reports/'qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2));print('DONE',p.name,q,flush=True)
