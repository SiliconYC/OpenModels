#!/usr/bin/env python3
"""Universal fixed-camera orthographic 64-slot controls. REAL triangle z-buffer.

Commands: generate, verify, sheet; always pass --spec. No Blender, GPU, AI art.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from cpu_renderer import raster, passes
CHANNELS=('silhouette','depth','parts')
LEVELS=(16,32,64)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def slots(n):
    assert n in LEVELS
    return list(range(0,64,64//n))
def load(path):
    path=Path(path).resolve();s=json.loads(path.read_text('utf-8'));c=s['camera']
    assert s['heading_slots']==64 and s['degrees_per_slot']==5.625
    assert c['type']=='orthographic' and c['fixed'] is True and c['world_up']=='+Y'
    assert len(c['canvas_px'])==len(c['pivot_px'])==2
    assert 256<=min(c['canvas_px'])<=max(c['canvas_px'])<=2048
    assert c['near_cam_z_m']<c['far_cam_z_m']
    model=(path.parent/s['model']).resolve()
    assert model.is_relative_to(path.parent) and model.is_file()
    return path,s,model
def frame(path,i,ch):
    return path.parent/'control/frames'/ch/f'{i:03d}.png'
def generate(path,n):
    path,s,model=load(path);c=s['camera']
    with np.load(model,allow_pickle=False) as d:
        v,f,ids=(d[k].copy() for k in ('vertices','faces','ids'))
    assert len(f)==len(ids) and len(f)>1000
    m={'schema_version':1,'purpose':'geometry-controls-only-not-art',
      'asset_id':s['asset_id'],'variant':s['variant'],'source_spec_sha256':sha(path),
      'source_model_sha256':sha(model),'heading_slots':64,'degrees_per_slot':5.625,
      'available_levels':[n],'camera':c,'canvas_px':c['canvas_px'],
      'pivot_px':c['pivot_px'],'rotation_target':'vehicle-only',
      'rotation_axis':'+Y','part_ids':s['part_ids'],'frames':{}}
    for k,i in enumerate(slots(n)):
        labels,z=raster(v,f,ids,yaw=i*5.625,azimuth=c['azimuth_deg'],
            elevation=c['elevation_deg'],width=c['canvas_px'][0],
            height=c['canvas_px'][1],pixels_per_m=c['pixels_per_m'],pivot=c['pivot_px'])
        images=passes(labels,z,near=c['near_cam_z_m'],far=c['far_cam_z_m'])
        opaque=labels>0
        item={'index':i,'theta_deg':i*5.625,'files':{},'sha256':{},
          'visible_pixels':int(np.count_nonzero(opaque)),
          'visible_parts':[int(x) for x in np.unique(labels[opaque])],
          'camera_depth_min_m':round(float(z[opaque].min()),5),
          'camera_depth_max_m':round(float(z[opaque].max()),5)}
        assert item['visible_pixels']>1000
        for ch,img in zip(CHANNELS,images):
            p=frame(path,i,ch);p.parent.mkdir(parents=True,exist_ok=True)
            img.save(p,optimize=True)
            item['files'][ch]=p.relative_to(path.parent).as_posix()
            item['sha256'][ch]=sha(p)
        m['frames'][f'{i:03d}']=item
        if (k+1)%8==0:print(f'Rendered {k+1}/{n} headings × 3 real geometry PNGs',flush=True)
    (path.parent/'control/manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    return m
def verify(path,n):
    path,s,model=load(path);m=json.loads((path.parent/'control/manifest.json').read_text())
    assert m['source_spec_sha256']==sha(path) and m['source_model_sha256']==sha(model)
    assert m['available_levels']==[n] and m['camera']==s['camera']
    assert m['pivot_px']==s['camera']['pivot_px']
    assert list(m['frames'])==[f'{i:03d}' for i in slots(n)]
    distinct=set()
    for i in slots(n):
        item=m['frames'][f'{i:03d}']
        assert item['index']==i and item['theta_deg']==i*5.625
        images={}
        for ch in CHANNELS:
            p=(path.parent/item['files'][ch]).resolve()
            assert p.is_relative_to(path.parent/'control')
            assert p.is_file() and sha(p)==item['sha256'][ch]
            im=Image.open(p);im.load()
            assert im.size==tuple(s['camera']['canvas_px'])
            assert im.mode in (('I;16','I') if ch=='depth' else ('RGBA',))
            images[ch]=np.asarray(im)
        opaque=images['silhouette'][:,:,3]>0
        assert np.array_equal(opaque,images['parts'][:,:,3]>0)
        assert np.array_equal(opaque,images['depth']>0)
        assert int(opaque.sum())==item['visible_pixels']
        assert len(np.unique(images['depth'][opaque]))>5
        distinct.add(item['sha256']['silhouette'])
    assert len(distinct)==n,'Duplicate silhouettes'
    assert slots(16)==list(range(0,64,4)) and slots(32)==list(range(0,64,2))
    assert slots(64)==list(range(64))
    print(f'PASS: {n} unique true-Z orthographic headings × 3 channels')
    return m
def sheet(path,indexes,channel,tile,name):
    path,s,model=load(path)
    assert channel in CHANNELS and 64<=tile<=1024
    assert len(indexes)==len(set(indexes))==16
    assert all(isinstance(i,int) and 0<=i<64 for i in indexes)
    out=Image.new('RGBA',(tile*4,tile*4),(0,0,0,0));cells=[]
    for k,i in enumerate(indexes):
        p=frame(path,i,channel);im=Image.open(p);im.load()
        if channel=='depth':
            data=np.asarray(im)
            im=Image.fromarray((data//257).astype('uint8'),'L').convert('RGBA')
        else:im=im.convert('RGBA')
        im=im.resize((tile,tile),Image.Resampling.NEAREST)
        out.alpha_composite(im,((k%4)*tile,(k//4)*tile))
        cells.append({'row':k//4,'column':k%4,'slot':i,'theta_deg':i*5.625,
                      'source':p.relative_to(path.parent).as_posix()})
    dst=path.parent/'control/sheets'/(name or f'{channel}-sheet')
    dst.parent.mkdir(parents=True,exist_ok=True)
    out.save(str(dst)+'.png')
    Path(str(dst)+'.json').write_text(json.dumps({'row_major':True,
        'tile_px':tile,'channel':channel,'cells':cells},indent=2)+'\n')
    print('SHEET',str(dst)+'.png')
def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['generate','verify','sheet'])
    p.add_argument('--spec',required=True)
    p.add_argument('--level',type=int,choices=LEVELS,default=64)
    p.add_argument('--slots',default='')
    p.add_argument('--channel',choices=CHANNELS,default='parts')
    p.add_argument('--tile',type=int,default=256)
    p.add_argument('--name')
    a=p.parse_args()
    if a.command=='generate':generate(a.spec,a.level)
    elif a.command=='verify':verify(a.spec,a.level)
    else:
        indexes=[int(x) for x in a.slots.split(',')] if a.slots else slots(16)
        sheet(a.spec,indexes,a.channel,a.tile,a.name)
if __name__=='__main__':main()
