/* Exact-item catalogue used by the price browser. No DOM or network dependencies. */
(function(root){
  'use strict';
  const S=root.EzzcoinsSite||(typeof require==='function'?require('./site-utils.js'):null);
  function buildCards(roster,extras,feed,lookup,specials=[],ids={}){
    const cols=Object.fromEntries(roster.cols.map((col,i)=>[col,i]));
    const routes=new Map(),byId=new Map();
    for(const row of roster.rows){
      const id=+row[cols.id],rating=+row[cols.ovr],name=row[cols.name];
      const url=rating>=75?'p/'+S.slug(name)+'-'+id+'/':'';
      routes.set(id,url);
      byId.set(id,{id,name,full:row[cols.full],rating,position:row[cols.pos],club:row[cols.club],nation:row[cols.nation],version:'Base',type:'base',url});
    }
    for(const card of specials){
      const key=Number(card.gid||card.fid),id=Number(ids[key]||card.eaId||card.gid);
      if(key&&id&&!card.excluded)routes.set(id,'p/'+S.slug(card.name)+'-'+(card.version?S.slug(card.version):'special')+'-'+(1e9+key)+'/');
    }
    const ec=Object.fromEntries(extras.cols.map((col,i)=>[col,i]));
    for(const row of extras.rows){
      const id=+row[ec.id],baseId=+row[ec.baseId],version=String(row[ec.version]||'');
      const type=/icon/i.test(version)?'icon':/hero/i.test(version)?'hero':/^(?:rare|common|gold|silver|bronze|base)$/i.test(version)||id===baseId?'base':'special';
      let url=routes.get(id)||(type==='base'?routes.get(baseId):'')||row[ec.url]||'';
      // Only our own page paths and the verified metadata provider are link targets.
      if(url&&!/^p\/[a-z0-9-]+\/$/.test(url)&&!/^https:\/\/www\.fut\.gg\/players\//.test(url))url='';
      byId.set(id,{...byId.get(id),id,name:row[ec.name],rating:+row[ec.ovr],position:row[ec.pos],club:row[ec.club],nation:row[ec.nation],version,type,url});
    }
    for(const row of feed.rows)if(!byId.has(row[0]))byId.set(row[0],{id:row[0],name:'Card details unavailable',rating:null,position:'',club:'',version:'Exact item ID '+row[0],type:'unknown',url:''});
    // A transferred base item's old ID resolves to the new item. Display/export that quote once,
    // preferring its exact metadata; genuine special versions remain separate.
    const canonical=new Map();
    for(const card of byId.values()){
      const id=lookup(feed,card.id,'console')?.id||card.id,exact=byId.get(id);
      const chosen=exact&&exact.type!=='unknown'?exact:card;
      if(!canonical.has(id)||chosen.id===id)canonical.set(id,{...chosen,id});
    }
    return [...canonical.values()].map(card=>({...card,key:S.normalize([card.name,card.full,card.club,card.nation,card.version,card.id].join(' '))}));
  }
  const API={buildCards};root.EzzcoinsPrices=API;if(typeof module!=='undefined')module.exports=API;
})(typeof globalThis!=='undefined'?globalThis:this);
