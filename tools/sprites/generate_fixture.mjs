// Pure Node.js stdlib fixture generator. No AI, GLB, external art or canvas dependency.
// node tools/sprites/generate_fixture.mjs [--check]
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const dest=path.join(root,'tests/fixtures/sprites/fixture-compass/integrated/export/frames');
const N=96,pivot=[48,56],poly=[[32,0],[7,-14],[-11,-11],[-25,-20],[-22,-2],[-31,11],[-1,12],[8,5]];
const table=Array.from({length:256},(_,n)=>{let a=n;for(let k=0;k<8;k++)a=a&1?0xedb88320^(a>>>1):a>>>1;return a>>>0});
const u32=n=>[(n>>>24)&255,(n>>>16)&255,(n>>>8)&255,n&255];
function chunk(type,data) {
  const bytes=[...[...type].map(c=>c.charCodeAt(0)),...data];
  let crc=0xffffffff;for(const b of bytes)crc=table[(crc^b)&255]^(crc>>>8);
  return [...u32(data.length),...bytes,...u32((crc^0xffffffff)>>>0)];
}
function png(slot) {
  const raw=[],a=slot*Math.PI*2/64,c=Math.cos(a),s=Math.sin(a);
  for(let y=0;y<N;y++){
    raw.push(0);
    for(let x=0;x<N;x++){
      const dx=x+.5-pivot[0],dy=y+.5-pivot[1],u=c*dx+s*dy,v=-s*dx+c*dy;
      let hit=false;
      for(let i=0,j=poly.length-1;i<poly.length;j=i++){
        const A=poly[i],B=poly[j];
        if((A[1]>v)!=(B[1]>v)&&u<(B[0]-A[0])*(v-A[1])/(B[1]-A[1])+A[0])hit=!hit;
      }
      let color=hit?(u>12?[247,181,90,255]:u<-16?[185,105,113,255]:[113,192,161,255]):[0,0,0,0];
      if(u>-17&&u<-5&&v<0&&v>-5&&hit)color=[50,101,147,255];
      if(u*u+v*v<9)color=[239,243,219,255];
      raw.push(...color);
    }
  }
  let p=1,q=0;for(const v of raw){p=(p+v)%65521;q=(q+p)%65521;}
  const d=[120,1,1,raw.length&255,raw.length>>>8,(~raw.length)&255,((~raw.length)>>>8)&255,...raw,...u32((q<<16)|p)];
  return Buffer.from([137,80,78,71,13,10,26,10,...chunk('IHDR',[...u32(N),...u32(N),8,6,0,0,0]),...chunk('IDAT',d),...chunk('IEND',[])]);
}
const check=process.argv.includes('--check');
if(!check)fs.mkdirSync(dest,{recursive:true});
for(let i=0;i<64;i++){
  const file=path.join(dest,String(i).padStart(3,'0')+'.png'),expected=png(i);
  if(check){
    if(!fs.existsSync(file)||!fs.readFileSync(file).equals(expected))throw Error('Fixture mismatch: '+file);
  }else fs.writeFileSync(file,expected);
}
console.log('Fixture '+(check?'verified':'generated')+': 64 deterministic RGBA PNGs, 96×96, fixed pivot [48,56]');
