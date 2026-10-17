import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=process.cwd();
const docs=path.join(root,'docs');
const catalog=JSON.parse(fs.readFileSync(path.join(docs,'sprites-catalog.json')));
const fixture=catalog.assets.find(a=>a.asset_id==='fixture-compass');
const manifest=JSON.parse(fs.readFileSync(path.join(docs,fixture.manifest)));
const prefix=path.dirname(path.join(docs,fixture.manifest));
const source=path.join(root,'tests/fixtures/sprites/fixture-compass/integrated/export');
const slots=level=>Array.from({length:level},(_,i)=>i*(64/level));
test('catalog separates explicitly planned and fixture assets',()=>{
 assert.equal(catalog.schema_version,1);
 assert.equal(fixture.release_status,'fixture');
 assert.equal(catalog.assets.find(a=>a.asset_id==='tiger-i').release_status,'planned');
 assert.ok(!('manifest' in catalog.assets.find(a=>a.asset_id==='tiger-i')));
});
test('manifest has fixed 64 slots, RGBA canvas and pivot',()=>{
 assert.equal(manifest.schema_version,1);assert.equal(manifest.heading_slots,64);assert.equal(manifest.degrees_per_slot,5.625);
 assert.deepEqual(manifest.pivot_px,[48,56]);
 assert.equal(manifest.canvas.alpha,'straight');
 assert.deepEqual(manifest.available_levels,[16,32,64]);
});
test('16/32/64 slots use common global numbering and are fully present',()=>{
 assert.equal(Object.keys(manifest.frames).length,64);
 for(const level of [16,32,64])for(const slot of slots(level)){
   const key=String(slot).padStart(3,'0');
   assert.equal(manifest.frames[key],'frames/'+key+'.png');
   assert.ok(fs.existsSync(path.join(prefix,manifest.frames[key])));
   assert.ok(fs.existsSync(path.join(source,manifest.frames[key])));
 }
 assert.deepEqual(slots(16).slice(0,3),[0,4,8]);
 assert.deepEqual(slots(32).slice(0,3),[0,2,4]);
});
test('all PNGs are distinct, correct signatures and contain genuine RGBA alpha',()=>{
 const signatures=new Set();
 for(let i=0;i<64;i++){
   const frame=fs.readFileSync(path.join(prefix,'frames',String(i).padStart(3,'0')+'.png'));
   assert.equal(frame.subarray(0,8).toString('hex'),'89504e470d0a1a0a');
   assert.equal(frame.readUInt32BE(16),96);assert.equal(frame.readUInt32BE(20),96);
   assert.equal(frame[25],6);
   signatures.add(crypto.createHash('sha256').update(frame).digest('hex'));
 }
 assert.equal(signatures.size,64);
});
test('publisher checks all PNG decodes, mirror SHA and path safety',()=>{
 execFileSync(process.execPath,['tools/sprites/publish.mjs','--check'],{cwd:root});
 execFileSync(process.execPath,['tools/sprites/generate_fixture.mjs','--check'],{cwd:root});
});
test('static player does not import Three.js',()=>{
 const html=fs.readFileSync(path.join(docs,'sprites.html'),'utf8');
 assert.ok(html.includes('sprites-viewer.js'));
 assert.ok(!html.includes('three.module'));
});
