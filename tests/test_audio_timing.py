import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audio_timing import build_timeline,place_local_alignment,pause_plan

class TimingTests(unittest.TestCase):
 def script(self):return {'sections':[{'id':str(i),'text':'sample'} for i in range(1,5)],'thinking_pauses':[{'after_section':'1','seconds':3},{'after_section':'3','seconds':2}]}
 def test_two_pauses_exact_samples(self):
  t=build_timeline(self.script(),{str(i):16000 for i in range(1,5)},16000)
  self.assertEqual([s['start'] for s in t['sections']],[0,4,5.3,8.3])
  self.assertEqual(t['total_samples'],161600)
  self.assertEqual(t['pause_seconds_total'],5)
  self.assertNotIn('pause_start',t)
 def test_shift_all_chars(self):
  t=build_timeline(self.script(),{str(i):16000 for i in range(1,5)},16000)
  a=[{'id':str(i),'chars':[{'c':'x','start':.2,'end':.5}]} for i in range(1,5)]
  out=place_local_alignment(a,t)
  self.assertAlmostEqual(out[3]['chars'][0]['start'],8.5)
  self.assertEqual(a[3]['chars'][0]['start'],.2)
 def test_legacy(self):
  s=self.script();del s['thinking_pauses'];s.update(pause_after=2,pause_seconds=3)
  t=build_timeline(s,{str(i):16000 for i in range(1,5)},16000)
  self.assertAlmostEqual(t['pause_start'],2.3);self.assertEqual(t['pause_seconds'],3)
 def test_no_pauses_explicit(self):
  s=self.script();s['thinking_pauses']=[]
  t=build_timeline(s,{str(i):16000 for i in range(1,5)},16000)
  self.assertEqual(t['pause_seconds_total'],0);self.assertAlmostEqual(t['total'],5.7)
 def test_invalid_anchors(self):
  s=self.script();s['thinking_pauses'][1]['after_section']='1'
  with self.assertRaises(ValueError):build_timeline(s,{str(i):16000 for i in range(1,5)},16000)
 def test_negative(self):
  s=self.script();s['thinking_pauses'][0]['seconds']=-1
  with self.assertRaises(ValueError):build_timeline(s,{str(i):16000 for i in range(1,5)},16000)
 def test_no_fake_alignment(self):
  t=build_timeline(self.script(),{str(i):16000 for i in range(1,5)},16000)
  a=[{'id':str(i),'chars':[{'c':'x','start':.2,'end':2}]} for i in range(1,5)]
  with self.assertRaises(ValueError):place_local_alignment(a,t)
 def test_last_pause(self):
  s=self.script();s['thinking_pauses']=[{'after_section':'4','seconds':2}]
  t=build_timeline(s,{str(i):16000 for i in range(1,5)},16000)
  self.assertAlmostEqual(t['total'],7.7)

if __name__=='__main__':unittest.main()
