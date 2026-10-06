(()=>{"use strict";
const root=new URL("./",document.currentScript.src);let cards={},ids={},pending;
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function read(name){if(window.EzzcoinsMarket)return window.EzzcoinsMarket.fetchData(name);const r=await fetch(new URL("data/"+name,root),{cache:"no-store"});if(!r.ok)throw Error(name);return r.json()}
async function load(){if(!pending)pending=Promise.all([read("card-renders.json"),read("card-ids.json")]).then(([a,b])=>{cards=a;ids=b;return a}).catch(e=>{pending=null;throw e});return pending}
function get(item,key,special=false){return cards[String(item)]||(special?cards["f:"+key]:null)||null}
function html(c,cls="fc-render",name=c.name){if(c.url)return '<img class="'+cls+'" src="'+esc(c.url)+'" alt="'+esc(name)+' '+esc(c.ovr)+' '+esc(c.version)+' FC 27 card" loading="lazy" decoding="async">';
 const short=c.name.trim().split(/\s+/).pop(),stats=(c.stats||[]).map((n,i)=>'<span><small>'+["PAC","SHO","PAS","DRI","DEF","PHY"][i]+'</small><b>'+esc(n)+'</b></span>').join("");
 return '<div class="'+cls+' ea-item" role="img" aria-label="'+esc(c.name)+' '+esc(c.ovr)+' '+esc(c.version)+' FC 27 card"><img class="ea-frame" src="'+esc(c.frame)+'" alt=""><img class="ea-face" src="'+esc(c.portrait)+'" alt=""><div class="ea-rating">'+esc(c.ovr)+'<small>'+esc(c.pos)+'</small></div><div class="ea-name">'+esc(short)+'</div><div class="ea-stats">'+stats+'</div><div class="ea-type">'+esc(c.version)+'</div></div>'
}
const style=document.createElement("style");style.textContent=`
.fcard.has-card-render{background:transparent!important;box-shadow:none!important;border-radius:0!important}
.fcard.has-card-render:after,.fcard.has-card-render>.fc-sil,.fcard.has-card-render>.fc-mono,.fcard.has-card-render>.fc-fallback{display:none!important}
.fc-render{object-fit:contain!important;border-radius:0!important}
.ea-item{position:relative;container-type:inline-size;isolation:isolate;color:#fff5c8;font-family:Arial,sans-serif;aspect-ratio:300/420}
.fc-render.ea-item{position:absolute;inset:0;width:100%;height:100%}
.ea-item .ea-frame{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;z-index:0}
.ea-item .ea-face{position:absolute;top:21%;left:24%;width:64%;height:46%;object-fit:contain;object-position:bottom;z-index:1}
.ea-rating{position:absolute;left:12%;top:16%;z-index:2;font-size:12cqw;font-weight:800;line-height:1}
.ea-rating small{display:block;font-size:.53em;margin-top:3px}
.ea-name{position:absolute;left:8%;right:8%;top:65%;text-align:center;z-index:2;font-size:8cqw;font-weight:700;line-height:1}
.ea-stats{position:absolute;left:12%;right:12%;top:74%;display:grid;grid-template-columns:repeat(6,1fr);gap:2px;z-index:2;text-align:center}
.ea-stats small{display:block;font-size:3.8cqw;font-weight:700}.ea-stats b{display:block;font-size:5.8cqw;line-height:1.1}
.ea-type{position:absolute;left:12%;right:12%;top:86%;text-align:center;font-size:3.4cqw;font-weight:bold;z-index:2}
.card-art.ea-item{width:184px;max-width:100%;height:auto;min-height:0}
`;document.head.append(style);
async function repairDetail(){const match=location.pathname.match(/-(\d+)\/?$/);if(!match)return;await load();const id=Number(match[1]),special=id>=1e9,key=special?id-1e9:id,c=get(ids[key]||key,key,special);if(!c)return;const current=document.querySelector(".card-art");if(!current)return;const box=document.createElement("div");box.innerHTML=html(c,"card-art");const next=current.nextElementSibling;current.replaceWith(box.firstElementChild);if(next?.classList.contains("card-fallback"))next.hidden=true}
window.EzzcoinsCardArt={load,get,html};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>repairDetail().catch(()=>{}),{once:true});else repairDetail().catch(()=>{});
})();