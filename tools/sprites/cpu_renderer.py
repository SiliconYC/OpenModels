"""CPU orthographic triangle rasterizer, a real per-pixel Z-buffer.

No fake 2.5D depth, GLB rotation masquerading as sprite, GPU or GUI.
Coordinate: +X forward; +Y up; +Z right; pivot is ground origin.
"""
from __future__ import annotations
import math
import numpy as np
from PIL import Image

def camera_basis(azimuth_deg, elevation_deg):
    az=math.radians(azimuth_deg); el=math.radians(elevation_deg)
    toward=np.array([math.cos(el)*math.cos(az),math.sin(el),math.cos(el)*math.sin(az)])
    right=np.cross(np.array([0.,1.,0.]),toward)
    right/=np.linalg.norm(right)
    up=np.cross(toward,right)
    up/=np.linalg.norm(up)
    return right,up,toward

def raster(vertices, faces, ids, *, yaw=0., azimuth=0., elevation=35.,
           width=512,height=512,pixels_per_m=47.,pivot=(256,354)):
    v=np.asarray(vertices,float)
    a=math.radians(yaw); c,s=math.cos(a),math.sin(a)
    # True +Y rotation of every vertex, never the camera.
    turned=np.column_stack((c*v[:,0]+s*v[:,2],v[:,1],-s*v[:,0]+c*v[:,2]))
    right,up,toward=camera_basis(azimuth,elevation)
    projected=np.stack((pivot[0]+turned@right*pixels_per_m,
                        pivot[1]-turned@up*pixels_per_m,
                        turned@toward),axis=-1)
    zbuffer=np.full((height,width),-np.inf,np.float32)
    labels=np.zeros((height,width),np.uint8)
    for tri,idvalue in zip(faces,ids):
        p=projected[tri]
        x0=max(int(np.floor(min(p[:,0]))),0);x1=min(int(np.ceil(max(p[:,0]))),width-1)
        y0=max(int(np.floor(min(p[:,1]))),0);y1=min(int(np.ceil(max(p[:,1]))),height-1)
        if x1<x0 or y1<y0: continue
        (xa,ya,za),(xb,yb,zb),(xc,yc,zc)=p
        den=(yb-yc)*(xa-xc)+(xc-xb)*(ya-yc)
        if abs(den)<1e-8: continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1]; xx=xx+.5; yy=yy+.5
        alpha=((yb-yc)*(xx-xc)+(xc-xb)*(yy-yc))/den
        beta=((yc-ya)*(xx-xc)+(xa-xc)*(yy-yc))/den
        gamma=1-alpha-beta
        mask=(alpha>=-1e-6)&(beta>=-1e-6)&(gamma>=-1e-6)
        if not mask.any(): continue
        camz=alpha*za+beta*zb+gamma*zc
        window=zbuffer[y0:y1+1,x0:x1+1]
        visible=mask&(camz>window)
        if not visible.any(): continue
        window[visible]=camz[visible]
        sub=labels[y0:y1+1,x0:x1+1]
        sub[visible]=idvalue
    return labels,zbuffer

COLORS=np.array([[0,0,0,0],[155,171,154,255],[206,196,133,255],
 [238,161,100,255],[99,130,124,255],[128,155,197,255],
 [181,142,191,255]],dtype=np.uint8)

def passes(labels, camera_depth, near=-12.,far=12.):
    """Returns actual alpha RGBA silhouette + 16-bit camera-depth + class-ID RGBA."""
    opaque=labels>0
    seam=np.zeros_like(opaque)
    seam[1:,:]|=(labels[1:,:]!=labels[:-1,:])
    seam[:-1,:]|=(labels[:-1,:]!=labels[1:,:])
    seam[:,1:]|=(labels[:,1:]!=labels[:,:-1])
    seam[:,:-1]|=(labels[:,:-1]!=labels[:,1:])
    seam &= opaque
    rgba=np.zeros((*labels.shape,4),np.uint8)
    rgba[opaque]=[38,46,47,255]
    rgba[seam]=[245,246,232,255]
    depth=np.zeros_like(labels,dtype=np.uint16)
    # Higher values are nearer to camera. Zero is reserved for unseen background.
    depth[opaque]=np.rint((np.clip(camera_depth[opaque],near,far)-near)/(far-near)*65534+1).astype(np.uint16)
    partition=COLORS[labels]
    return (Image.fromarray(rgba,"RGBA"),Image.fromarray(depth),
            Image.fromarray(partition,"RGBA"))

def shade_preview(labels):
    return Image.fromarray(COLORS[labels],"RGBA")
