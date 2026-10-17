"""Actual source PNG evidence, independent of potentially cached media previews."""
import hashlib
import json
import struct
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'models/vehicles/land/tiger-i/sprites'
CAND=ASSET/'generated/issue25/candidates/openai'

class OpenAICandidates(unittest.TestCase):
    def test_four_real_imagegen_pngs_at_full_resolution(self):
        m=json.loads((CAND/'manifest.json').read_text('utf-8'))
        self.assertEqual(m['slots'],[0,16,32,48])
        self.assertEqual(m['status'],'REAL_GENERATED_CANDIDATES_UNAPPROVED')
        self.assertFalse(m['controlnet_used'])
        self.assertFalse(m['camera_lock_verified'])
        self.assertFalse(m['slot_matched_3channel_controls_supplied'])
        self.assertFalse(m['approval']['ready_for_16_heading_production'])
        cfg=json.loads((ASSET/'spec.json').read_text('utf-8'))
        self.assertEqual(cfg['degrees_per_slot'],5.625)
        controls=json.loads((ASSET/'control/manifest.json').read_text('utf-8'))
        hashes=set()
        for i in (0,16,32,48):
            k=f'{i:03d}'
            p=CAND/(k+'.png')
            self.assertTrue(p.exists(),str(p))
            b=p.read_bytes()
            self.assertTrue(b.startswith(bytes.fromhex('89504e470d0a1a0a')))
            self.assertGreater(len(b),500_000)
            self.assertEqual(b[12:16],b'IHDR')
            w,h,bits,color,compression,filter_,interlace=struct.unpack('>IIBBBBB',b[16:29])
            self.assertEqual((w,h,bits,color),(1254,1254,8,2))  # RGB, deliberately NOT alpha
            self.assertEqual((compression,filter_,interlace),(0,0,0))
            actual=hashlib.sha256(b).hexdigest()
            self.assertEqual(actual,m['candidates'][k]['sha256'])
            self.assertEqual(m['candidates'][k]['requested_theta_deg'],i*5.625)
            self.assertEqual(controls['frames'][k]['theta_deg'],i*5.625)
            self.assertTrue(m['candidates'][k]['imagegen_generation_id'])
            self.assertFalse(m['candidates'][k]['has_real_transparency'])
            self.assertFalse(m['candidates'][k]['approved'])
            hashes.add(actual)
        self.assertEqual(len(hashes),4)
    def test_never_publish_unapproved_samples(self):
        self.assertFalse((ASSET/'approved').exists())
        self.assertFalse((ASSET/'export').exists())
        self.assertEqual(len(list(CAND.glob('[0-9][0-9][0-9].png'))),4)