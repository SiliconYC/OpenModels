#!/usr/bin/env python3
"""Refined early Tiger I (Tiger 131 era) original procedural geometry.

Metres; +X forward, +Y up, +Z to vehicle's right. No Blender/CAD binary.
Reproduce with Python 3.12, numpy and trimesh. Details are deliberately
modelled as REAL triangle geometry, not fake labels or pre-rendered images.

Historical dimensional sources (not copied 3D assets):
https://tankmuseum.org/article/two-widths-track/
https://tiger1.info/EN/RoadWheelSpacing.html
https://tiger1.info/EN/Hull-dimensions.html
https://tiger1.info/EN/Turret-dimensions.html
https://tiger1.info/EN/Hull-crew-hatches.html
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[5]
ASSET = ROOT / "models/vehicles/land/tiger-i"
WEB = ROOT / "docs/assets"
EXPORT = ASSET / "export"
GREY = EXPORT / "tiger-i-refined-grey.glb"
WEB_GREY = WEB / "tiger-i-refined-grey.glb"
REPORT = EXPORT / "refined-mesh-report.json"

ARMOUR = (160, 166, 153)
UPPER = (172, 177, 164)
WELD = (126, 136, 129)
DARK = (55, 64, 62)
TRACK = (67, 74, 71)
TIRE = (45, 50, 49)
STEEL = (117, 127, 122)
RIM = (145, 151, 142)
DARKENED = (79, 87, 80)
HINGE = (92, 101, 97)
PX, PY = .315, 2.18
SECTIONS = 20


def tint(mesh, color):
    mesh.visual.vertex_colors = np.tile(np.array([*color, 255], dtype=np.uint8), (len(mesh.vertices), 1))
    return mesh


def geom(verts, faces, color):
    m = trimesh.Trimesh(vertices=np.asarray(verts, dtype=np.float64),
                        faces=np.asarray(faces, dtype=np.int64), process=False)
    if len(m.faces) == 0 or not np.isfinite(m.vertices).all():
        raise ValueError("invalid geometry")
    return tint(m, color)


def box(ext, pos, color=ARMOUR):
    m = trimesh.creation.box(extents=ext)
    m.apply_translation(pos)
    return tint(m, color)


def extrude_xy(contour, width, color):
    """Full width X/Y armour silhouette; CCW XY contour."""
    v = [[x,y,-width/2] for x,y in contour] + [[x,y,width/2] for x,y in contour]
    n=len(contour)
    f=[]
    for k in range(1,n-1):
        f.extend([(0,k+1,k),(n,n+k,n+k+1)])
    for i in range(n):
        j=(i+1)%n
        f.extend([(i,j,n+j),(i,n+j,n+i)])
    return geom(v,f,color)


def extrude_xz(contour, lo, hi, color, roof_inset=0):
    """Raised turret shell in local Turret coordinates, with planar top."""
    n=len(contour)
    c=np.asarray(contour,dtype=float).mean(axis=0)
    low=[[x,lo,z] for x,z in contour]
    high=[[c[0]+(x-c[0])*(1-roof_inset),hi,c[1]+(z-c[1])*(1-roof_inset)] for x,z in contour]
    fs=[]
    for k in range(1,n-1):
        fs.extend([(0,k,k+1),(n,n+k+1,n+k)])
    for i in range(n):
        j=(i+1)%n
        fs.extend([(i,n+j,j),(i,n+i,n+j)])
    return geom(low+high,fs,color)


def lathe_z(profile, center, color, segments=20):
    """Closed radial/rim profile revolved around Z. Wheel dish/rubber tyre."""
    p=list(profile)
    v=[]
    for r,z in p:
        for i in range(segments):
            a=i*2*math.pi/segments
            v.append([r*math.cos(a)+center[0],r*math.sin(a)+center[1],z+center[2]])
    faces=[]
    for k in range(len(p)):
        q=(k+1)%len(p)
        for i in range(segments):
            j=(i+1)%segments
            a=k*segments+i
            b=k*segments+j
            c=q*segments+i
            d=q*segments+j
            faces.extend([(a,b,d),(a,d,c)])
    return geom(v,faces,color)


def lathe_y(profile, center, color, sections=18):
    v=[]
    for r,y in profile:
        for k in range(sections):
            a=2*math.pi*k/sections
            v.append([center[0]+r*math.cos(a), center[1]+y, center[2]+r*math.sin(a)])
    faces=[]
    for i in range(len(profile)):
        j=(i+1)%len(profile)
        for k in range(sections):
            l=(k+1)%sections
            faces.extend([(i*sections+k,i*sections+l,j*sections+l),
                          (i*sections+k,j*sections+l,j*sections+k)])
    return geom(v,faces,color)


def lathe_x(profile, center, color, sections=20):
    v=[]
    for x,r in profile:
        for i in range(sections):
            a=2*math.pi*i/sections
            v.append([center[0]+x,center[1]+r*math.sin(a),center[2]+r*math.cos(a)])
    faces=[]
    for k in range(len(profile)):
        j=(k+1)%len(profile)
        for i in range(sections):
            q=(i+1)%sections
            faces.extend([(k*sections+i,k*sections+q,j*sections+q),
                          (k*sections+i,j*sections+q,j*sections+i)])
    return geom(v,faces,color)


def disk_y(radius, height, center, color, segments=18):
    profile=[(.002,0),(radius,0),(radius,height),(.002,height)]
    return lathe_y(profile,center,color,segments)


def wheel_profile(zwidth):
    h=zwidth*.5
    # Thick rubber rim with sloping inner metal dish, hollow-looking centre.
    return [(.018,-h),(.235,-h),(.300,-h*.80),(.344,-h*.97),
            (.394,-h*.98),(.402,-h*.62),(.402,h*.58),(.388,h*.98),
            (.347,h*.98),(.310,h*.75),(.250,h*.38),(.114,h*.18),(.018,h*.18)]


def wheel(z,x,cy=.62,rscale=1):
    m=lathe_z([(r*rscale,v) for r,v in wheel_profile(.11)],
              [x,cy,z],RIM,segments=18)
    return m


def wheel_hub(z,x,cy,side):
    m=lathe_z([(.016,-.015),(.101,-.012),(.126,.015),(.126,.032),(.01,.032)],
              [x,cy,z],DARKENED,segments=14)
    return m


def track_loop(steps_per_end=24):
    """Closed CCW topographic track path; tangent around +X front sprocket."""
    rear,front=-2.49,2.49
    cy,r=.70,.64  # outer belt at y=.06; cast shoes at y≈.015
    points=[(rear,cy-r),(front,cy-r)]
    for a in np.linspace(-math.pi/2,math.pi/2,steps_per_end+1)[1:]:
        points.append((front+r*math.cos(a),cy+r*math.sin(a)))
    points.append((rear,cy+r))
    for a in np.linspace(math.pi/2,3*math.pi/2,steps_per_end+1)[1:]:
        points.append((rear+r*math.cos(a),cy+r*math.sin(a)))
    # Do not repeat the starting vertex: the closing belt face is
    # generated by modulo indexing, and duplicate ends make zero-area UV faces.
    assert np.linalg.norm(np.array(points[0])-np.array(points[-1])) < 1e-8
    return points[:-1]


def track_belt(zcenter):
    path=np.asarray(track_loop(),float)
    n=len(path)
    # Separate outside and inside radial profiles along lateral extrusion.
    zs=(zcenter-.3625,zcenter+.3625)
    center_y=.70
    ins=[]
    for x,y in path:
        if x>2.49: center=(2.49,center_y)
        elif x<-2.49: center=(-2.49,center_y)
        else: center=(x,center_y)
        delta=np.array([x-center[0],y-center[1]])
        dist=np.linalg.norm(delta)
        if dist<.001:
            delta=np.array([0, -1 if y<center_y else 1])
        ins.append([x,y]-np.asarray(delta)/np.linalg.norm(delta)*.105)
    inside=np.asarray(ins)
    verts=[]
    for coords in (path,inside):
        for z in zs:
            verts.extend([[x,y,z] for x,y in coords])
    fs=[]
    for i in range(n):
        j=(i+1)%n
        for a,b in ((0,n),(n,3*n),(3*n,2*n),(2*n,0)):
            fs.extend([(a+i,a+j,b+j),(a+i,b+j,b+i)])
    return geom(verts,fs,TRACK)


def oriented_shoe(center, tangent, zcenter, width=.72):
    """Actual cast tread pad. Local horizontal extends tangent to track."""
    tx,ty=tangent
    # 0.077m long side profile; thick enough to read in the RTS view.
    m=box([.077,.035,width], [0,0,0], TRACK)
    angle=math.atan2(ty,tx)
    m.apply_transform(trimesh.transformations.rotation_matrix(angle,[0,0,1]))
    m.apply_translation([center[0],center[1],zcenter])
    return m


def shoes(zcenter, n=100):
    path=np.asarray(track_loop(),float)
    edges=np.linalg.norm(np.roll(path,-1,axis=0)-path,axis=1)
    dists=np.insert(np.cumsum(edges),0,0)
    length=dists[-1]
    parts=[]
    for k in range(n):
        t=(k+.5)*length/n
        seg=int(np.searchsorted(dists,t,side='right')-1)
        seg=min(seg,len(path)-1)
        vec=path[(seg+1)%len(path)]-path[seg]
        d=vec/np.linalg.norm(vec)
        p=path[seg]+d*(t-dists[seg])
        outward=np.array([d[1],-d[0]])
        p+=outward*.026
        # Tread is a real 3D prismatic shoe, not a printed fake.
        parts.append(oriented_shoe(p,d,zcenter,width=.72))
    return tint(trimesh.util.concatenate(parts),TRACK)


def sprocket(x,cy,z,outer=True):
    # Driven radial disc, castellated small tooth tips and hub are separate solids.
    return lathe_z([(.03,-.058),(.24,-.058),(.28,-.035),(.40,-.041),
                    (.47,-.042),(.47,.042),(.40,.046),
                    (.27,.025),(.12,.06),(.03,.060)], [x,cy,z],STEEL,22)


def sprocket_teeth(x,cy,z,teeth=12):
    parts=[]
    for k in range(teeth):
        a=2*math.pi*k/teeth
        m=box([.13,.105,.16],[x+.477*math.cos(a),cy+.477*math.sin(a),z],WELD)
        m.apply_transform(trimesh.transformations.rotation_matrix(a,[0,0,1],point=[x+.477*math.cos(a),cy+.477*math.sin(a),z]))
        parts.append(m)
    return tint(trimesh.util.concatenate(parts),STEEL)


def guard_panels(side):
    return [(i,(-2.64+i*.88)) for i in range(6)]


def engine_grille(x,z):
    frame=box([.65,.019,.58],[x,2.208,z],WELD)
    slats=[]
    for k in range(7):
        slats.append(box([.55,.012,.026],[x,2.226,z-.24+k*.08],DARK))
    return frame,tint(trimesh.util.concatenate(slats),DARK)


def trans(pos):
    matrix=np.eye(4)
    matrix[:3,3]=pos
    return matrix


def build_scene():
    scene=trimesh.Scene(base_frame="World")
    scene.graph.update(frame_to="Hull",frame_from="World",matrix=np.eye(4))
    names=[]
    def attach(m,name,parent="Hull"):
        scene.add_geometry(m,geom_name=name,node_name=name,parent_node_name=parent)
        names.append(name)
    def tb(name,size,location,color=ARMOUR):
        x,y,z=location
        attach(box(size,[x-PX,y-PY,z],color),name,"Turret")
    # Main lower tub with distinctive near-vertical front and rear armour,
    # lower glacis chamfer, sponsons and near-flat Tiger upper roof.
    attach(extrude_xy([(-3.158,.72),(2.72,.72),(3.158,1.05),
                      (3.158,1.83),(3.00,2.13),(-2.94,2.13),
                      (-3.158,1.99)],2.60,ARMOUR),"HullArmour")
    attach(extrude_xy([(-2.90,.85),(2.60,.85),(2.89,1.23),
                      (2.89,1.45),(-2.89,1.45)],2.16,STEEL),"LowerTub")
    attach(box([5.93,.11,2.68],[-.02,2.17,0],UPPER),"RoofPlate")
    attach(box([5.30,.10,2.85],[-.03,1.68,0],ARMOUR),"Sponsons")
    # Distinct nose armour face and angled upper glacis, important silhouette.
    attach(box([.10,.89,2.62],[3.105,1.54,0],UPPER),"NoseVerticalPlate")
    attach(box([.32,.06,2.72],[2.88,2.18,0],WELD),"NoseRoofTransition")
    attach(box([.10,.25,2.60],[-3.105,1.98,0],STEEL),"RearVerticalPlate")
    # Early Tiger driver's vision block and hull MG ball mount.
    attach(box([.085,.18,.42],[3.175,1.87,-.62],WELD),"DriverViewPlate")
    attach(box([.031,.035,.31],[3.226,1.855,-.62],DARK),"DriverVisionSlot")
    attach(lathe_x([(0,.016),(.03,.14),(.11,.18),(.17,.09),(.17,.018)],
                   [3.115,1.73,.61],WELD),"BowMachinegunBall")
    attach(lathe_x([(0,.034),(.13,.028),(.22,.024),(.23,.034)],
                   [3.264,1.73,.61],DARK),"BowMachinegunBarrel")
    for side in (-1,1):
        # Foredeck crew hatches: 560 mm circles ~900 mm from centre.
        z=side*.90
        attach(disk_y(.285,.026,[2.12,2.227,z],UPPER),"CrewHatch_"+str(side))
        attach(box([.29,.035,.078],[2.13,2.263,z],WELD),"HatchPeriscopeCover_"+str(side))
        attach(box([.17,.022,.11],[1.96,2.259,z],DARKENED),"HatchHinge_"+str(side))
        # Structural track guards: six distinct plates, not giant continuous bars.
        for i,x in guard_panels(side):
            attach(box([.854,.047,.32],[x,1.477,side*1.68],UPPER),
                   f"SideSkirt_{side}_{i+1}")
            attach(box([.024,.07,.32],[x+.427,1.481,side*1.68],WELD),
                   f"SideSkirtJoint_{side}_{i+1}")
        # Complete independent track shell and 100 visible cast tread shoes.
        zc=side*1.411
        attach(track_belt(zc),f"TrackBelt_{side}")
        attach(shoes(zc),f"TrackShoes_{side}")
        # Early 1943: 8 stations x 3 offset rubber-tyred wheels = 24/side.
        # Alternate axle stations use offset z positions for real interleaving.
        for station in range(8):
            x=-2.19+.515*station
            offsets=(1.14,1.39,1.64) if station%2==0 else (1.205,1.455,1.685)
            for layer,z0 in enumerate(offsets):
                z=side*z0
                # Wheel mesh (visible dished profile) and seated hub.
                attach(wheel(z,x),"RoadWheel_%+d_%02d_%d"%(side,station+1,layer+1))
                if layer==2:
                    attach(wheel_hub(z+side*.055,x,.62,side),
                           "WheelHub_%+d_%02d"%(side,station+1))
        # Drive sprocket at front, elevated above ground; idler at the rear.
        for kind,x in (("Sprocket",2.49),("Idler",-2.49)):
            attach(sprocket(x,.70,side*1.43),f"{kind}_{side}")
            attach(sprocket_teeth(x,.70,side*1.43),
                   f"{kind}Teeth_{side}")
        # Tow eyes and upper forward fenders.
        attach(box([.29,.19,.115],[3.07,.89,side*1.01],STEEL),f"TowEye_{side}")
        attach(box([.35,.055,.70],[2.94,1.34,side*1.40],WELD),f"FrontFender_{side}")
        # Rear exhaust vertical silencer pairs; use real cylinders in Y.
        z=side*.78
        attach(lathe_y([(.03,0),(.18,0),(.18,.54),(.16,.61),(.03,.61)],
                       [-3.22,.95,z],DARKENED),f"ExhaustSilencer_{side}")
        attach(lathe_y([(.025,0),(.075,0),(.07,.21),(.022,.21)],
                       [-3.22,1.55,z],TIRE),f"ExhaustTip_{side}")
        attach(box([.09,.55,.37],[-3.345,1.27,z],WELD),f"ExhaustGuard_{side}")
    # Engine deck: transverse engine access lid plus mirrored grills.
    attach(box([1.70,.028,2.54],[-2.09,2.242,0],UPPER),"EngineCover")
    attach(disk_y(.35,.025,[-2.19,2.255,0],STEEL),"EngineAccessHatch")
    for j,x in enumerate((-2.64,-1.89)):
        for side in (-1,1):
            z=side*.87
            frame,slats=engine_grille(x,z)
            attach(frame,f"CoolingGrilleFrame_{j}_{side}")
            attach(slats,f"CoolingGrilleSlats_{j}_{side}")
    # Hatch on rear engine lid, small lifting handles, fan access.
    for z in (-.32,.32):
        attach(box([.34,.03,.026],[-2.18,2.275,z],DARKENED),
               "EngineHinge_"+str(z))
    # Turret ring genuinely sits over a rotary interface, not floating.
    attach(disk_y(.923,.055,[PX,2.16,0],DARKENED),"TurretRace")
    scene.graph.update(frame_to="Turret",frame_from="Hull",
                       matrix=trans([PX,PY,0]))
    # Tiger I horseshoe turret: broad flat forward shield with rounded aft
    # cheeks and strongly curved rear (not a pointy fantasy polygon).
    turret_outline=[
        (-1.21,0),(-1.185,-.27),(-1.105,-.51),(-.97,-.71),
        (-.77,-.86),(-.48,-.975),(-.18,-1.025),(.20,-1.04),
        (.60,-1.02),(1.00,-.93),(1.39,-.76),(1.51,-.70),
        (1.51,.70),(1.39,.76),(1.00,.93),(.60,1.02),
        (.20,1.04),(-.18,1.025),(-.48,.975),(-.77,.86),
        (-.97,.71),(-1.105,.51),(-1.185,.27)]
    attach(extrude_xz([(x-PX,z) for x,z in turret_outline],
                      .045,.585,ARMOUR,roof_inset=.025),"TurretShell","Turret")
    # Roof inset and weld rim (thin distinct cap) - flatter than side armour.
    roof=[(x-PX,z*.97) for x,z in turret_outline]
    attach(extrude_xz(roof,.585,.602,UPPER),"TurretRoof","Turret")
    # Early flat frontal mantlet with tapered round gun shield front;
    # shield asymmetry: historically wider to one side of the bore.
    # Local x/y/Z positions. Mounted on turret, not recoiling with gun.
    tb("MantletShield",[.23,.57,1.34],[1.60,2.44,-.075],STEEL)
    attach(lathe_x([(0,.08),(.03,.28),(.16,.32),(.26,.26),(.285,.13),
                    (.285,.05)], [1.66-PX,2.435-PY,0],ARMOUR),"GunCollar","Turret")
    tb("MantletSight",[.035,.14,.16],[1.77,2.48,-.52],DARKENED)
    # Commander cupola behind and left of turret gun centre (early drum style).
    cx,cz=-.48-PX,-.59
    attach(lathe_y([(.02,0),(.27,0),(.29,.042),(.292,.186),
                    (.274,.215),(.02,.215)], [cx,.592,cz],STEEL),"CommanderCupola","Turret")
    attach(disk_y(.25,.024,[cx,.806,cz],UPPER),"CupolaTop","Turret")
    for i in range(6):
        a=math.pi*2*i/6
        tb(f"CupolaVision_{i}",[.028,.055,.096],
           [cx+PX+.275*math.cos(a),PY+.702,cz+.275*math.sin(a)],DARK)
    # Loader's round hatch and cupola machine details on turret roof.
    attach(disk_y(.235,.026,[.53-PX,.61,.61],UPPER),"LoaderHatch","Turret")
    attach(box([.16,.035,.045],[.39-PX,.647,.61],WELD),"LoaderHatchHinge","Turret")
    # Practical stowage bin fixed to rear turret, flatter ends with side bracket.
    tb("TurretStowage",[.315,.395,1.34],[-1.24,2.45,0],STEEL)
    for side in (-1,1):
        tb(f"TurretBinBracket_{side}",[.18,.13,.075],[-1.07,2.36,side*.58],DARKENED)
        # Turret roof lifting eyes
        for x in (-.53, .72):
            tb(f"TurretLift_{side}_{int(x*100)}",[.065,.05,.065],
               [x,2.804,side*.78],WELD)
    # Gun tube moves independently in longitudinal -X recoil.
    scene.graph.update(frame_to="Barrel",frame_from="Turret",matrix=trans([1.335,.25,0]))
    attach(lathe_x([(0,.07),(.02,.155),(.16,.156),(.31,.123),
                    (.60,.123),(.80,.112),(1.7,.111),
                    (2.95,.096),(3.20,.095),(3.25,.095),
                    (3.25,.062),(0,.062)],
                   [0,0,0],UPPER),"BarrelTube","Barrel")
    # A true dual-baffle hollow-looking cylindrical muzzle brake; two wide
    # hoops are separated by actual side braces, unlike prior rectangular box.
    attach(lathe_x([(3.205,.12),(3.205,.168),(3.31,.174),
                    (3.31,.13)], [0,0,0],STEEL),"MuzzleFirstRing","Barrel")
    attach(lathe_x([(3.445,.125),(3.445,.188),(3.565,.183),
                    (3.565,.135)], [0,0,0],WELD),"MuzzleSecondRing","Barrel")
    attach(lathe_x([(3.565,.125),(3.565,.160),(3.642,.161),
                    (3.642,.118)], [0,0,0],STEEL),"MuzzleExitRing","Barrel")
    for side in (-1,1):
        attach(box([.26,.067,.09],[3.38,side*.152,0],DARKENED),
               f"MuzzleBridge_{side}","Barrel")
    return scene,names


def main():
    scene,names=build_scene()
    EXPORT.mkdir(parents=True,exist_ok=True)
    WEB.mkdir(parents=True,exist_ok=True)
    payload=trimesh.exchange.gltf.export_glb(scene)
    GREY.write_bytes(payload)
    WEB_GREY.write_bytes(payload)
    verified=trimesh.load(GREY,force="scene")
    tris=sum(len(m.faces) for m in verified.geometry.values())
    verts=sum(len(m.vertices) for m in verified.geometry.values())
    bounds=np.asarray(verified.bounds)
    assert {"Hull","Turret","Barrel"}.issubset(set(verified.graph.nodes))
    assert tris>6000, "detailed real geometry did not generate"
    assert abs(bounds[0][1])<.08, "tread must touch the ground"
    assert abs(bounds[0][0]+3.158)<.4
    assert abs(bounds[1][0]-5.292)<.45
    assert bounds[1][1]<=3.20
    road=sum(k.startswith("RoadWheel_") for k in verified.geometry)
    assert road==48,(road,list(verified.geometry)[:10])
    report={"asset":"tiger-i-early-1943","phase":"refined geometry early production",
            "historical_reference":["tankmuseum.org/article/two-widths-track/",
                                    "tiger1.info/EN/RoadWheelSpacing.html",
                                    "tiger1.info/EN/Hull-dimensions.html",
                                    "tiger1.info/EN/Turret-dimensions.html"],
            "source":"source/build_refined.py","triangles":tris,"vertices":verts,
            "mesh_count":len(verified.geometry),
            "bounds_xyz_m":np.round(bounds,5).tolist(),
            "road_wheels_per_side":24,"road_wheels_total":road,
            "road_wheel_stations_per_side":8,"track_shoes_per_side":100,
            "track_width_m":.725,"wheels_diameter_m":.804,
            "parts":{k:{"triangles":len(v.faces),"vertices":len(v.vertices)}
                     for k,v in verified.geometry.items()},
            "articulations":{"Turret":{"parent":"Hull","pivot":[.315,2.18,0],"axis":"+Y"},
                             "Barrel":{"parent":"Turret","pivot_turret":[1.335,.25,0],
                                       "recoil":"-X"}},
            "not_modelled":"interior, suspension arms, measured weld lines, final textures",
            "rebuild_command":"python models/vehicles/land/tiger-i/source/build_refined.py"}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:report[k] for k in ("triangles","vertices","mesh_count",
                                          "bounds_xyz_m","road_wheels_total")},ensure_ascii=False))


if __name__=="__main__":
    main()
