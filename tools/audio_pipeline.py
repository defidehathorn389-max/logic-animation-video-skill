# usage: audio_pipeline.py <episode dir>  -> trims pauses, computes tempo, atempo, timeline.json, char-alignment.json
# script.json 可选字段：chars（缺省自动数）、pause_after（思考拍插在第几段之后，默认 1）、pause_seconds（默认 3.0）、pause_cap_s（默认 0.2）；ffmpeg 不在 PATH 时用 imageio_ffmpeg
import soundfile as sf, numpy as np, json, subprocess, sys, re, os, shutil
os.chdir(sys.argv[1]); d=json.load(open('script.json')); cap=d.get('pause_cap_s',0.2)
if len(d.get('thinking_pauses',[]))>1:
    raise SystemExit('Multiple thinking pauses: use audio_timing.py + assemble_audio.py after per-section audio QA; single-pause pipeline refuses to drop extra pauses.')
N=d.get('chars') or sum(len(re.findall(r'[\u4e00-\u9fff0-9]',s['text'])) for s in d['sections']); d['chars']=N
PAUSE_AFTER=int(d.get('pause_after',1))   # 思考拍插在第几段之后（默认 1；018 的“给你三秒”在第 2 段末）
FF=shutil.which('ffmpeg') or __import__('imageio_ffmpeg').get_ffmpeg_exe()
if not shutil.which('ffmpeg'):   # stable-ts 内部直接调用 'ffmpeg'：把 imageio 的二进制以 ffmpeg 之名放进 PATH
    _b=os.path.join(os.path.expanduser('~'),'.local','bin'); os.makedirs(_b,exist_ok=True); _l=os.path.join(_b,'ffmpeg')
    if not os.path.exists(_l): os.symlink(FF,_l)
    os.environ['PATH']=_b+os.pathsep+os.environ.get('PATH','')
tot=0; tr=[]
for s in d['sections']:
    x,sr=sf.read(f'audio/{s["id"]}.wav'); x=x.mean(1) if x.ndim>1 else x
    win=int(0.02*sr); e=np.convolve(np.abs(x),np.ones(win)/win,'same'); quiet=e<10**(-40/20); keep=np.ones(len(x),bool); i=0
    while i<len(x):
        if quiet[i]:
            j=i
            while j<len(x) and quiet[j]: j+=1
            if (j-i)>cap*sr: keep[i+int(cap*sr/2):j-int(cap*sr/2)]=False
            i=j
        else: i+=1
    idx=np.where(~quiet)[0]; keep[:max(0,idx[0]-int(0.1*sr))]=False; keep[min(len(x),idx[-1]+int(0.1*sr)):]=False
    y=x[keep]; sf.write(f'audio/{s["id"]}-trim.wav',y,sr); tr.append(len(y)/sr); tot+=len(y)/sr
tempo=max(1.0,min(1.35,round(tot/(N/325*60),3))); d['tempo']=tempo; json.dump(d,open('script.json','w'),ensure_ascii=False,indent=1)
t=0; tl=[]
for s in d['sections']:
    subprocess.run([FF,'-loglevel','error','-y','-i',f'audio/{s["id"]}-trim.wav','-filter:a',f'atempo={tempo}',f'audio/{s["id"]}-fast.wav'],check=True)
    x,sr=sf.read(f'audio/{s["id"]}-fast.wav'); L=len(x)/sr; tl.append({'id':s['id'],'start':round(t,3),'end':round(t+L,3),'text':s['text']}); t+=L+0.3
print('tempo',tempo,'speech end',round(t,1),'cpm pure',round(N/(sum(e['end']-e['start'] for e in tl)/60)))
import stable_whisper; model=stable_whisper.load_model('base'); out=[]; issues=[]
for s in tl:
    r=model.align(f'audio/{s["id"]}-fast.wav',s['text'],language='zh'); chars=[]
    for seg in r.segments:
        for w in seg.words:
            for ch in w.word:
                if re.match(r'[\u4e00-\u9fff0-9]',ch): chars.append({'c':ch,'start':round(w.start+s['start'],3),'end':round(w.end+s['start'],3)})
    n=len(re.findall(r'[\u4e00-\u9fff0-9]',s['text']))
    if len(chars)!=n: issues.append((s['id'],len(chars),n))
    i=0
    while i<len(chars):
        j=i
        while j<len(chars) and chars[j]['start']==chars[i]['start'] and chars[j]['end']==chars[i]['end']: j+=1
        k=j-i
        if k>1:
            a,b=chars[i]['start'],chars[i]['end']
            for m in range(k): chars[i+m]['start']=round(a+(b-a)*m/k,3); chars[i+m]['end']=round(a+(b-a)*(m+1)/k,3)
        i=j
    for i,c in enumerate(chars):
        if c['end']-c['start']<=0.001:
            if i+1<len(chars): nx=chars[i+1]; mid=round((nx['start']+nx['end'])/2,3); c['end']=mid; nx['start']=mid
            elif i>0: pv=chars[i-1]; mid=round((pv['start']+pv['end'])/2,3); pv['end']=mid; c['start']=mid; c['end']=round(mid+0.08,3)
    for i in range(1,len(chars)):
        if chars[i]['start']<chars[i-1]['end']: chars[i]['start']=chars[i-1]['end']
        if chars[i]['end']<chars[i]['start']+0.03: chars[i]['end']=round(chars[i]['start']+0.03,3)
    out.append({'id':s['id'],'text':s['text'],'start':s['start'],'end':s['end'],'chars':chars})
PAUSE=float(d.get('pause_seconds',3.0)); p0=tl[PAUSE_AFTER-1]['end']+0.3
for coll in (tl,out):
    for s in coll:
        if s['start']>=p0-0.01:
            s['start']=round(s['start']+PAUSE,3); s['end']=round(s['end']+PAUSE,3)
            for c in s.get('chars',[]): c['start']=round(c['start']+PAUSE,3); c['end']=round(c['end']+PAUSE,3)
json.dump({'sections':tl,'tempo':tempo,'pause_start':round(p0,3),'pause_seconds':PAUSE,'total':round(tl[-1]['end']+1.0,3)},open('timeline.json','w'),ensure_ascii=False,indent=1)
json.dump({'method':'stable-ts base align; shared word times spread; zero-dur split','sections':out,'issues':issues},open('char-alignment.json','w'),ensure_ascii=False,indent=1)
print('issues',issues,'total',round(tl[-1]['end']+1.0,1))
