// Puppeteer real-browser acceptance (desktop + phone + true WebGL + failure case).
import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
const origin=process.env.OPENMODELS_BASE || 'http://127.0.0.1:8765/OpenModels/';
const browser=await puppeteer.launch({headless:true,executablePath:'/usr/bin/google-chrome',
 args:['--no-sandbox','--enable-webgl','--use-gl=angle','--use-angle=swiftshader','--disable-gpu-sandbox']});
const page=await browser.newPage();
const errors=[];page.on('pageerror',e=>errors.push(String(e)));
const status=()=>page.evaluate(()=>window.__spriteViewerStatus?.());
const wait=()=>page.waitForFunction(()=>window.__spriteViewerStatus?.().loaded===true,{timeout:25000});
const requireIt=(value,message)=>{if(!value)throw Error(message)};
try{
 fs.mkdirSync('acceptance',{recursive:true});
 await page.setViewport({width:1280,height:850,deviceScaleFactor:1});
 await page.goto(origin,{waitUntil:'domcontentloaded'});
 requireIt(await page.$('a[href="./sprites.html"]'),'Home missing sprite entry');
 requireIt(await page.$('a[href="./3d.html"]'),'Home missing 3D entry');
 requireIt(!(await page.$('#stage')),'Home incorrectly embeds legacy viewer');
 await page.screenshot({path:'acceptance/home-desktop.png'});
 await page.goto(origin+'sprites.html',{waitUntil:'domcontentloaded'});
 await wait();
 requireIt((await status()).level===16,'Default 16 level');
 requireIt((await status()).available_levels.join(',')==='16,32,64','All 3 levels are real');
 requireIt(await page.$eval('#asset-status',e=>e.textContent.includes('测试夹具')),'fixture designation missing');
 await page.click('#next');await wait();
 requireIt((await status()).slot===4,'16-heading step not 4');
 await page.click('[data-level="32"]');await wait();
 requireIt((await status()).level===32,'32-heading not enabled');
 await page.click('#next');await wait();
 requireIt((await status()).slot===6,'32-heading step not 2');
 await page.click('[data-level="64"]');await wait();
 await page.click('#next');await wait();
 requireIt((await status()).slot===7,'64-heading step not 1');
 for(const n of [64,128,256]){
   await page.click('[data-size="'+n+'"]');
   requireIt((await status()).size===n,'Pixel preview '+n+' failed');
 }
 await page.click('#checker');
 requireIt(await page.$eval('#canvas-holder',e=>e.classList.contains('checkered')),'Checkerboard not toggled');
 const canvas=await page.$('#sprite-canvas'),r=await canvas.boundingBox(),oldSlot=(await status()).slot;
 await page.mouse.move(r.x+r.width*.3,r.y+r.height*.5);
 await page.mouse.down();await page.mouse.move(r.x+r.width*.48,r.y+r.height*.5,{steps:10});await page.mouse.up();
 await wait();
 requireIt((await status()).slot!==oldSlot,'Mouse drag did not rotate');
 await page.click('#play');
 await new Promise(resolve=>setTimeout(resolve,520));
 requireIt((await status()).playing,'Autoplay not running');
 await page.click('#play');requireIt(!(await status()).playing,'Pause not working');
 await page.screenshot({path:'acceptance/sprites-desktop.png'});
 await page.setViewport({width:390,height:820,deviceScaleFactor:1,isMobile:true,hasTouch:true});
 await page.goto(origin,{waitUntil:'domcontentloaded'});await page.screenshot({path:'acceptance/home-mobile.png'});
 await page.goto(origin+'sprites.html?asset=fixture-compass&variant=integrated&level=64&heading=63',{waitUntil:'domcontentloaded'});
 await wait();
 requireIt((await status()).slot===63,'Deep link heading lost');
 const mobileCanvas=await page.$('#sprite-canvas'),bounds=await mobileCanvas.boundingBox();
 const sx=Math.round(bounds.x+bounds.width*.3),sy=Math.round(bounds.y+bounds.height*.45);
 const client=await page.createCDPSession();
 await client.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:sx,y:sy}]});
 await client.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:sx+60,y:sy}]});
 await client.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
 await wait();requireIt((await status()).slot!==63,'Touch swipe not rotating');
 await page.screenshot({path:'acceptance/sprites-mobile.png'});
 await page.goto(origin+'?model=test-cube',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>document.querySelector('#load-state')?.textContent==='已加载真实 GLB',{timeout:50000});
 requireIt(page.url().includes('/3d.html?model=test-cube'),'Legacy model deep link not redirected');
 requireIt((await page.evaluate(()=>window.__openmodelsCameraStatus?.())).type==='OrthographicCamera','GLB/orthographic missing');
 await page.click('[data-projection="perspective"]');
 requireIt((await page.evaluate(()=>window.__openmodelsCameraStatus?.())).type==='PerspectiveCamera','Real perspective missing');
 for(const view of ['front','back','left','right','top','iso'])await page.click('[data-view="'+view+'"]');
 await page.click('[data-shading="clay"]');await page.click('#wire');await page.click('#reset');
 await page.screenshot({path:'acceptance/3d-mobile.png'});
 await page.goto(origin+'sprites.html?asset=not-a-real-asset&variant=integrated',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>!document.querySelector('#failure').hidden,{timeout:15000});
 requireIt((await page.$eval('#failure',e=>e.textContent)).includes('未知资产'),'Invalid asset URL not rejected');
 // Simulate missing PNG in a new page, disable the cache so request interception is decisive.
 const broken=await browser.newPage();
 await broken.setCacheEnabled(false);await broken.setRequestInterception(true);
 broken.on('request',req=>req.url().endsWith('/frames/000.png')?req.abort('failed'):req.continue());
 await broken.goto(origin+'sprites.html?asset=fixture-compass&variant=integrated&level=64&heading=0',{waitUntil:'domcontentloaded'});
 await broken.waitForFunction(()=>!document.querySelector('#failure').hidden,{timeout:15000});
 requireIt((await broken.$eval('#failure',e=>e.textContent)).includes('帧加载失败'),'Missing image not surfaced');
 await broken.close();
 requireIt(!errors.length,'Browser exceptions: '+errors.join(' | '));
 console.log('PASS desktop and mobile: portal, actual RGBA PNG, 16/32/64, sizes, checker, drag, touch, autoplay, deep links, true GLB/Three, errors');
}catch(e){
 console.error('SPRITE_BROWSER_FAIL',e,errors);
 await page.screenshot({path:'acceptance/failure.png'}).catch(()=>{});
 process.exitCode=1;
}finally{await browser.close();}
