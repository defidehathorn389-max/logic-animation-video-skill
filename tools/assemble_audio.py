"""Assemble section WAVs and all thinking pauses on one sample-exact clock.
This is timing/assembly only, not a pronunciation or final-quality approval.
Usage: assemble_audio.py EP_DIR --pattern 'audio/{id}-fast.wav'
Optional --alignment-local FILE maps real section-local acoustic timestamps.
"""
import argparse,json
from pathlib import Path
import numpy as np
import soundfile as sf
from audio_timing import build_timeline,place_local_alignment,place_local_events,srt_text

def assemble(ep,pattern,output,timeline_name,alignment_local=None):
 ep=Path(ep);script=json.loads((ep/'script.json').read_text());clips={};frames={};sr=None
 for s in script['sections']:
  x,rate=sf.read(ep/pattern.format(id=s['id']),dtype='float32')
  if x.ndim!=1:raise ValueError('Use preprocessed mono audio')
  if sr is not None and rate!=sr:raise ValueError('Resample to one rate before assembly')
  sr=rate;clips[s['id']]=x;frames[s['id']]=len(x)
 tl=build_timeline(script,frames,sr);audio=np.zeros(tl['total_samples'],dtype='float32')
 for s in tl['sections']:audio[s['start_sample']:s['end_sample']]=clips[s['id']]
 if alignment_local:
  local=json.loads((ep/alignment_local).read_text());mapped=place_local_alignment(local['sections'],tl)
  (ep/'char-alignment.json').write_text(json.dumps({'method':local.get('method','caller-provided acoustic alignment'),'timing_method':'audio_timing sample offsets for all pause events','sections':mapped},ensure_ascii=False,indent=2)+'\n')
  if local.get('sentences'):
   (ep/'subtitles.srt').write_text(srt_text(place_local_events(local['sentences'],tl)),encoding='utf-8')
 dest=ep/output;dest.parent.mkdir(parents=True,exist_ok=True);sf.write(dest,audio,sr,subtype='PCM_16')
 (ep/timeline_name).write_text(json.dumps(tl,ensure_ascii=False,indent=2)+'\n')
 return tl

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('ep');p.add_argument('--pattern',default='audio/{id}-fast.wav');p.add_argument('--output',default='audio/narration.wav');p.add_argument('--timeline',default='timeline.json');p.add_argument('--alignment-local');a=p.parse_args();t=assemble(a.ep,a.pattern,a.output,a.timeline,a.alignment_local);print(json.dumps({'total':t['total'],'pause_events':t['pause_events']},ensure_ascii=False))
