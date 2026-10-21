// Public tool capabilities only: no process global, node:process, or indirect lookup.
export function taskClock(toolClock){
 if(!toolClock||typeof toolClock.now!=='function'||!Number.isFinite(toolClock.beginMs)||toolClock.beginMs<0)throw Error('prospective public monotonic clock required');
 let last=toolClock.beginMs;
 return {sample(){const n=toolClock.now();if(!Number.isFinite(n)||n<last)throw Error('public monotonic clock reversed or unavailable');last=n;const elapsedNs=Math.ceil((n-toolClock.beginMs)*1e6);if(!Number.isSafeInteger(elapsedNs)||elapsedNs>=28800e9)throw Error('preparation exceeded task wall allowance');return elapsedNs;}};
}
export function taskEnvironment(publicEnv){
 if(!publicEnv||typeof publicEnv!=='object')throw Error('public tool environment required');
 const allowed=new Set(['SYSTEMROOT','WINDIR','COMSPEC','PATH','PATHEXT','USERPROFILE','APPDATA','LOCALAPPDATA','PROGRAMDATA']);
 const result={};for(const [key,value] of Object.entries(publicEnv)){const name=key.toUpperCase();if(!allowed.has(name))continue;if(typeof value!=='string'||value.includes('\0'))throw Error('invalid public environment value');if(name in result&&result[name]!==value)throw Error('ambiguous public environment key');result[name]=value;}
 if(!result.SYSTEMROOT)throw Error('public SystemRoot unavailable');
 return Object.freeze(result);
}
