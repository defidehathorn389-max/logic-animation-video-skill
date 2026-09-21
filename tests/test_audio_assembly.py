import unittest,sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import numpy as np
import soundfile as sf
from assemble_audio import assemble
from audio_timing import place_local_events

class AssemblyTests(unittest.TestCase):
 def test_two_pauses_wav_chars_srt_events(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'audio').mkdir();ids=['a','b','c','d'];sr=8000
   script={'sections':[{'id':i,'text':i} for i in ids], 'thinking_pauses':[{'after_section':'a','seconds':3},{'after_section':'c','seconds':2}]}
   (p/'script.json').write_text(json.dumps(script))
   for n,i in enumerate(ids,1):sf.write(p/'audio'/f'{i}.wav',np.full(sr,n*.1),sr,subtype='PCM_16')
   local={'method':'synthetic fixture, NOT speech alignment','sections':[{'id':i,'chars':[{'c':i,'start':.2,'end':.5}]} for i in ids], 'sentences':[{'section_id':i,'text':i,'start':.2,'end':.5} for i in ids]}
   (p/'local.json').write_text(json.dumps(local))
   tl=assemble(p,'audio/{id}.wav','joined.wav','timeline.json','local.json')
   y,rate=sf.read(p/'joined.wav');self.assertEqual(len(y),tl['total_samples']);self.assertEqual(rate,sr)
   for pause in tl['pause_events']:self.assertTrue(np.all(y[pause['start_sample']:pause['end_sample']]==0))
   aligned=json.loads((p/'char-alignment.json').read_text())
   self.assertEqual(aligned['sections'][-1]['chars'][0]['start'],8.5)
   self.assertIn('00:00:08,500 --> 00:00:08,800',(p/'subtitles.srt').read_text())
   events=place_local_events([{'section_id':'d','start':.2,'end':.5,'action':'test'}],tl)
   self.assertEqual(events[0]['start'],8.5)
   self.assertTrue(np.allclose(y[tl['sections'][-1]['start_sample']:tl['sections'][-1]['end_sample']],.4,atol=1/32768))

if __name__=='__main__':unittest.main()
