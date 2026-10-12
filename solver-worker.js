importScripts('tools-core.js');
onmessage=({data})=>{try{const result=data.score?EzzTools.solveScore(data.pool,data.score,data.parsed):EzzTools.solvePuzzle(data.pool,data.parsed,data.slots);postMessage(result);}catch(e){postMessage({error:'The solution could not be verified: '+e.message});}};
