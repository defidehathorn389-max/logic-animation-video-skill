import unittest,sys,math
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from subtitle_effects import PRESETS,pose,transform,synth,mix_events
class EffectsTest(unittest.TestCase):
 def test_all_presets(self):
  for name in PRESETS:
   for t in [-1,0,.05,.15,.3,1,3]:
    p=pose(name,t,2);self.assertTrue(all(math.isfinite(v) for v in p.values()));self.assertTrue(0<=p['opacity']<=1)
   self.assertEqual(pose(name,-1)['opacity'],0)
   p=pose(name,3,2);self.assertAlmostEqual(p['opacity'],1);self.assertAlmostEqual(p['dx'],0);self.assertAlmostEqual(p['dy'],0)
 def test_raster(self):
  for name in PRESETS:
   im,offset=transform(Image.new('RGBA',(100,50),'white'),name,.1);self.assertEqual(im.mode,'RGBA');self.assertGreater(im.width,0)
 def test_sounds(self):
  for kind in {v[1] for v in PRESETS.values()}:
   x=synth(kind);self.assertTrue(np.isfinite(x).all());self.assertLessEqual(np.max(abs(x)),10**(-32/20)+1e-6);self.assertEqual(float(x[0]),0);self.assertEqual(float(x[-1]),0)
 def test_mix(self):
  v=np.zeros(24000);x=mix_events(v,[{'time':.1,'kind':'tick'},{'time':.4,'kind':'air_swipe'}]);self.assertEqual(len(x),len(v));self.assertGreater(np.max(abs(x)),0)
  with self.assertRaises(ValueError):mix_events(v,[{'time':.1,'kind':'tick'},{'time':.11,'kind':'tick'}])
if __name__=='__main__':unittest.main()
