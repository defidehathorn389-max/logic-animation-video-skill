"""Acoustic character alignment of existing narration. No credentials, no new TTS."""
from pathlib import Path
import json,subprocess,wave,sys,argparse
import numpy as np,torch,stable_whisper,imageio_ffmpeg
from stable_whisper.alignment import get_whisper_alignment_func
from stable_whisper.non_whisper.alignment import WordToken
from stable_whisper.options import AllOptions
from whisper.tokenizer import get_tokenizer
parser=argparse.ArgumentParser();parser.add_argument('--source-root',required=True,type=Path);parser.add_argument('projects',nargs='+',type=Path);args=parser.parse_args();ROOT=args.source_root.resolve();torch.set_num_threads(2)
model=stable_whisper.load_model('base',device='cpu')
tok=get_tokenizer(True,language='zh',task='transcribe');run=get_whisper_alignment_func(model,tok,None,AllOptions({'dynamic_heads':True},vanilla_align=True))
punct='，。：？！、； ,.!?:;'
for arg in args.projects:
 P=Path(arg).resolve();spec=json.loads((P/'spec.json').read_text());(P/'work').mkdir(exist_ok=True)
 pos=spec['intro_silence'];segments=[];sections=[];repaired=[]
 for i,lines in enumerate(spec['lines']):
  wav=P/'work'/f'align-{i}.wav';src=ROOT/spec['source_audio']/f'{i+1:02}.wav'
  subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-i',str(src),'-af',f"atempo={spec['rate']}",'-ar','16000','-ac','1',str(wav)],capture_output=True,check=True)
  with wave.open(str(wav)) as f:a=np.frombuffer(f.readframes(f.getnframes()),np.int16).astype(np.float32)/32768
  cc=[c for line in lines for c in line if c not in punct];tokens=[WordToken(c,tok.encode(c)) for c in cc]
  with torch.no_grad():words=run(torch.from_numpy(a),tokens)
  rr=stable_whisper.WhisperResult([words]);rr.adjust_by_silence(a,sample_rate=16000,word_level=True,min_word_dur=.02,k_size=3,verbose=None)
  words=[w.to_dict() for ss in rr.segments for w in ss.words];assert len(words)==len(cc)
  energy=np.convolve(a*a,np.ones(160)/160,'same')
  for j,w in enumerate(words):
   if w['end']-w['start']>=.025 or not j:continue
   prev=words[j-1];lo=max(prev['start']+.035,w['start']-.14);hi=w['start']-.035
   if hi<=lo:continue
   k0=max(0,int(lo*16000));k1=min(len(a),int(hi*16000))
   if k1<=k0:continue
   b=(k0+int(np.argmin(energy[k0:k1])))/16000;old=w['start'];w['start']=round(b,3);prev['end']=w['start'];repaired.append({'section':i,'char':w['word'],'old':old,'new':w['start']})
  k=0
  for line in lines:
   chars=[]
   for c in line:
    if c in punct:
     t=chars[-1]['end'] if chars else pos;chars.append({'char':c,'start':t,'end':t,'punctuation':True})
    else:
     w=words[k];assert w['word']==c;k+=1;chars.append({'char':c,'start':round(pos+w['start'],3),'end':round(pos+w['end'],3),'probability':w.get('probability')})
   segments.append({'text':line,'start':chars[0]['start'],'end':chars[-1]['end'],'chars':chars,'section':i})
  sections.append({'start':pos,'duration':len(a)/16000});pos+=len(a)/16000
  if i==spec['pause_after']:pause=pos;pos+=spec['pause_seconds']
  print(spec['episode'],i+1,'aligned',len(cc),flush=True)
 total=pos+spec['outro_silence'];meta={'sections':sections,'pause_start':pause,'pause_seconds':3,'total':total,'alignment':'acoustic character-token DTW, silence trimming, local energy refinement','repairs':repaired}
 (P/'char-alignment.json').write_text(json.dumps(segments,ensure_ascii=False,indent=2));(P/'timeline.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
