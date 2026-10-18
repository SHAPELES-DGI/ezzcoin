const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
  constructor(tag='div'){this.tagName=tag.toUpperCase();this.dataset={};this.children=[];this.attrs={};this._text='';this.parentElement=this;}
  append(...children){this.children.push(...children);}
  after(...children){this.afterElements=children;}
  replaceChildren(...children){this.children=children;this._text='';}
  setAttribute(k,v){this.attrs[k]=v;}
  set textContent(v){this._text=v;this.children=[];}
  get textContent(){return this._text+this.children.map(c=>typeof c==='string'?c:c.textContent).join('');}
  querySelector(selector){return this.children.find(c=>c.className===selector.slice(1))||null;}
}
async function test({reward=false,item='123',path='/p/player-123/'}={}) {
  const box=new Element(),footer=new Element(),heading=new Element();box.dataset={item,reward:String(reward)};heading.textContent='Player';
  const elements=[],events={},timers=[],now=Date.now();let quote={id:123,price:1500,status:0,at:new Date(now).toISOString(),src:'FUT.GG'};
  const M={lookup:()=>quote,load:async()=>({}),freshness:at=>({freshness:now-Date.parse(at)>90*60000?'stale':now-Date.parse(at)>15*60000?'delayed':'fresh',ageMinutes:Math.floor((now-Date.parse(at))/60000)})};
  const context={URL,Date,Number,AbortSignal,location:{pathname:path},document:{currentScript:{src:'https://ezzcoins.com/player-tools.js'},getElementById:id=>id==='px'?box:footer,querySelector:()=>heading,createTextNode:s=>s,createElement:tag=>{const e=new Element(tag);elements.push(e);return e;}},window:{EzzcoinsMarket:M,addEventListener:(type,fn)=>{events[type]=fn;}},setInterval:fn=>timers.push(fn),fetch:async()=>({ok:false})};
  await vm.runInNewContext(fs.readFileSync('player-tools.js','utf8'),context);
  const graph=elements.find(e=>e.tagName==='BUTTON');
  const compare=elements.find(e=>e.tagName==='A'&&e.textContent==='Compare player');
  assert(compare); assert.equal(new URL(compare.href).pathname,'/compare.html');
  assert.equal(new URL(compare.href).searchParams.get('ids'),item);
  assert.equal(new URL(compare.href).searchParams.get('add'),'1');
  if(reward){assert(box.textContent.includes('not tradeable'));assert(!box.textContent.includes('1,500'));assert(graph.disabled);return;}
  assert(box.textContent.includes('1,500'));assert(box.textContent.includes('LIVE'));
  events['ezzcoins:quote-error']();for(const timer of timers)timer();assert(box.textContent.includes('CHECK FAILED'));
  events['ezzcoins:quotes']({detail:{}});assert(box.textContent.includes('LIVE'));
  quote={...quote,at:new Date(now-30*60000).toISOString()};events['ezzcoins:quotes']({detail:{}});assert(box.textContent.includes('DELAYED'));
  quote={...quote,at:new Date(now-120*60000).toISOString()};events['ezzcoins:quotes']({detail:{}});assert(box.textContent.includes('OUTDATED'));
  quote={...quote,price:null,status:1};events['ezzcoins:quotes']({detail:{}});assert(box.textContent.includes('SBC card'));assert(!box.textContent.includes('1,500'));assert(!box.dataset.price);
  quote={...quote,status:0};events['ezzcoins:quotes']({detail:{}});assert(box.textContent.includes('No listings'));
  quote=null;events['ezzcoins:quotes']({detail:{}});assert(box.textContent.includes('No verified'));
}
(async()=>{await test();await test({path:'/p/player-123/index.html'});await test({reward:true});console.log('Player quotes: fresh/delayed/stale, untradeable, missing listings, reward cards and direct index URLs pass.');})().catch(e=>{console.error(e);process.exitCode=1;});
