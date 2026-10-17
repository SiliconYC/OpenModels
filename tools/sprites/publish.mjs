// Deterministic static Pages export. Add new assets in assets.json, not another viewer.
// node tools/sprites/publish.mjs [--check] [--write]
// Source files are authoritative; docs mirrors are byte-for-byte copies.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const check=process.argv.includes('--check');
const idOK=x=>typeof x==='string'&&/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(x)&&x.length<=64;
const key=i=>String(i).padStart(3,'0');
const readJSON=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const fail=msg=>{throw Error(msg)};
function safeSource(p) {
  if(typeof p!=='string'||p.startsWith('/')||p.includes('\\')||p.split('/').includes('..')||!(/^(models\/.+\/sprites\/export|tests\/fixtures\/sprites\/[a-z0-9-]+\/[a-z0-9-]+\/export)$/.test(p)))fail('Source outside approved sprite export tree: '+p);
  let cur=root;
  for(const part of p.split('/')){
    cur=path.join(cur,part);
    if(fs.lstatSync(cur).isSymbolicLink())fail('Symlink in source path: '+p);
  }
  return cur;
}
function pngInfo(file,width,height) {
  const b=fs.readFileSync(file);
  if(b.length<66||!b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))fail('Not PNG: '+file);
  let off=8,dim=null,idat=[],ended=false;
  while(off+12<=b.length){
    const len=b.readUInt32BE(off),start=off+8,end=start+len;
    if(end+4>b.length)fail('PNG truncated: '+file);
    const type=b.toString('ascii',off+4,off+8);
    let crc=0xffffffff;
    for(let j=off+4;j<end;j++){crc^=b[j];for(let k=0;k<8;k++)crc=crc&1?(crc>>>1)^0xedb88320:crc>>>1;}
    if(((crc^0xffffffff)>>>0)!==b.readUInt32BE(end))fail('PNG CRC mismatch: '+file);
    if(type==='IHDR'){
      if(dim||len!==13||b[start+8]!==8||b[start+9]!==6||b[start+12]!==0)fail('Not noninterlaced RGBA8: '+file);
      dim=[b.readUInt32BE(start),b.readUInt32BE(start+4)];
    }
    if(type==='IDAT')idat.push(b.subarray(start,end));
    off=end+4;if(type==='IEND'){ended=true;break;}
  }
  if(!ended||off!==b.length||!dim||dim[0]!==width||dim[1]!==height||!idat.length)fail('Bad PNG shape: '+file);
  const raw=zlib.inflateSync(Buffer.concat(idat),{maxOutputLength:(width*4+1)*height});
  if(raw.length!==(width*4+1)*height)fail('PNG scanline data invalid: '+file);
  let previous=Buffer.alloc(width*4),transparent=0,opaque=0,offset=0;
  for(let y=0;y<height;y++){
    const filter=raw[offset++],row=Buffer.from(raw.subarray(offset,offset+width*4));offset+=width*4;
    if(filter>4)fail('Unknown PNG filter: '+file);
    for(let x=0;x<row.length;x++){
      const a=x>=4?row[x-4]:0,b=previous[x],c=x>=4?previous[x-4]:0;
      const paeth=()=>{const p=a+b-c,da=Math.abs(p-a),db=Math.abs(p-b),dc=Math.abs(p-c);return da<=db&&da<=dc?a:db<=dc?b:c};
      if(filter===1)row[x]=(row[x]+a)&255;
      if(filter===2)row[x]=(row[x]+b)&255;
      if(filter===3)row[x]=(row[x]+Math.floor((a+b)/2))&255;
      if(filter===4)row[x]=(row[x]+paeth())&255;
    }
    for(let x=3;x<row.length;x+=4){if(row[x]===0)transparent++;if(row[x]===255)opaque++;}
    previous=row;
  }
  if(!transparent||!opaque)fail('Fixture/asset must contain actual straight-alpha transparent and opaque pixels: '+file);
}
function validate(m,e,src) {
  if(!m||m.schema_version!==1||m.asset_id!==e.asset_id||m.variant!==e.variant||m.release_status!==e.release_status||m.heading_slots!==64||m.degrees_per_slot!==5.625)fail('Manifest header mismatch: '+src);
  const c=m.canvas,p=m.pivot_px;
  if(!c||!Number.isInteger(c.width)||!Number.isInteger(c.height)||c.width<16||c.height<16||c.width>4096||c.height>4096||c.alpha!=='straight'||c.color_space!=='sRGB'||!Array.isArray(p)||p.length!==2||!p.every((n,i)=>Number.isInteger(n)&&n>=0&&n<(i?c.height:c.width)))fail('Invalid canvas/pivot: '+src);
  if(!Array.isArray(m.available_levels)||!m.available_levels.length||!m.available_levels.every(n=>[16,32,64].includes(n))||new Set(m.available_levels).size!==m.available_levels.length)fail('Invalid levels: '+src);
  if(!m.frames||Array.isArray(m.frames)||typeof m.frames!=='object')fail('Frames missing');
  for(const [k,v] of Object.entries(m.frames))if(!/^(0[0-5][0-9]|06[0-3])$/.test(k)||v!=='frames/'+k+'.png')fail('Unsafe frame path: '+k);
  for(const level of m.available_levels)for(let i=0;i<64;i+=64/level)if(m.frames[key(i)]!=='frames/'+key(i)+'.png')fail(level+' incomplete');
}
const assetConfig=readJSON(path.join(root,'tools/sprites/assets.json'));
if(!Array.isArray(assetConfig.assets)||!assetConfig.assets.length)fail('Invalid asset configuration');
const catalog={schema_version:1,assets:[]},seen=new Set();
for(const e of assetConfig.assets){
  if(!idOK(e.asset_id)||!idOK(e.variant)||typeof e.title!=='string'||!['fixture','approved','planned'].includes(e.release_status))fail('Unsafe catalog entry');
  const id=e.asset_id+'/'+e.variant;
  if(seen.has(id))fail('Duplicate entry: '+id);seen.add(id);
  const entry={asset_id:e.asset_id,variant:e.variant,release_status:e.release_status,title:e.title};
  if(e.release_status==='planned'){
    if(e.source)fail('Planned entry must not claim a source');
  }else{
    if(!e.source)fail('Missing source: '+id);
    const src=safeSource(e.source),dest=path.join(root,'docs/assets/sprites',id),m=readJSON(path.join(src,'manifest.json'));
    validate(m,e,src);
    entry.manifest='assets/sprites/'+id+'/manifest.json';
    const publishFile=(relative)=>{
      const srcFile=path.join(src,relative),dstFile=path.join(dest,relative);
      if(!fs.statSync(srcFile).isFile()||fs.lstatSync(srcFile).isSymbolicLink())fail('Source frame not regular file');
      if(check){
        if(!fs.existsSync(dstFile)||hash(srcFile)!==hash(dstFile))fail('Published file differs from approved export: '+relative);
      }else {
        fs.mkdirSync(path.dirname(dstFile),{recursive:true});fs.copyFileSync(srcFile,dstFile);
      }
    };
    for(const [k,v] of Object.entries(m.frames)){
      const file=path.join(src,v);
      if(!fs.existsSync(file))fail('Missing frame '+v);
      pngInfo(file,m.canvas.width,m.canvas.height);
      publishFile(v);
    }
    publishFile('manifest.json');
  }
  catalog.assets.push(entry);
}
const output=JSON.stringify(catalog,null,2)+'\n',catalogFile=path.join(root,'docs/sprites-catalog.json');
if(check){
  if(fs.readFileSync(catalogFile,'utf8')!==output)fail('Published catalog differs from asset configuration');
}else fs.writeFileSync(catalogFile,output);
console.log('Sprites '+(check?'verified':'published')+': '+catalog.assets.filter(e=>e.release_status!=='planned').length+' released/fixture asset(s), '+catalog.assets.filter(e=>e.release_status==='planned').length+' planned');
