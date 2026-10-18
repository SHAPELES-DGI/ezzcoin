/* Shared search spelling and public player-page paths. */
(function(root){
  'use strict';
  const letters={'ø':'o','ß':'ss','ł':'l','æ':'ae','œ':'oe','đ':'d','ı':'i','ð':'d','þ':'th'};
  const normalize=value=>String(value??'').toLowerCase().normalize('NFD').replace(/\p{M}/gu,'').replace(/[øßłæœđıðþ]/g,c=>letters[c]);
  const slug=value=>normalize(value).replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'player';
  const API={normalize,slug};
  root.EzzcoinsSite=API;
  if(typeof module!=='undefined')module.exports=API;
})(typeof globalThis!=='undefined'?globalThis:this);
