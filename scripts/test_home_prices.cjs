const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('index.html', 'utf8');
const start = source.indexOf('function homeCardPrice(');
const end = source.indexOf('function Le(', start);
assert(start >= 0 && end > start);
const context = {
  L: 1000000000, cardIds: {12: 50500123}, ezMarketPrices: {},
  m: String, R: () => 'just now', Ze: n => n.toLocaleString('en-US'),
  window: {EzzcoinsMarket: {lookup: (_, id) => ({
    50500123: {price: 1500, status: 0, src: 'FUT.GG', at: '2026-10-06T12:00:00Z'},
    123: {price: null, status: 0},
    124: {price: null, status: 1}
  })[id]}}
};
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
assert.match(context.homeCardPrice({price: 999999}, 1000000012), /1,500/);
assert.doesNotMatch(context.homeCardPrice({price: 999999}, 1000000012), /999,999/);
assert.match(context.homeCardPrice({version: 'Gold Rare', price: 999}, 123), /No listings/);
assert.match(context.homeCardPrice({version: 'FUT Champions'}, 1000000099), /Reward card/);
assert.match(context.homeCardPrice({version: 'POTM'}, 124), /SBC card/);
assert.match(context.homeCardPrice({price: 999}, 999), /Price unavailable/);
console.log('Home quotes: exact IDs, live prices, reward/SBC labels and missing listings pass');
