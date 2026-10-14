export class ScenarioState{
 constructor(){this.request=null;this.confirmed=false;this.result=null;this.stale=false;}
 propose(parameters,baseVersion){this.invalidate();this.request={request_id:globalThis.crypto?.randomUUID?.()||String(Date.now()),case_id:'BROWSER-SYNTHETIC',base_version:baseVersion,parameters:structuredClone(parameters)};return this.request;}
 invalidate(){this.confirmed=false;if(this.result)this.stale=true;}
 confirm(version){if(!this.request||this.request.base_version!==version)throw Error('账本或参数已变化，请重新确认');this.confirmed=true;this.stale=false;return structuredClone(this.request);}
 calculate(fn,version){if(!this.confirmed||!this.request||this.request.base_version!==version)throw Error('请先确认本次参数');const snapshot=structuredClone(this.request);this.result={snapshot,value:fn(snapshot.parameters)};this.stale=false;return this.result;}
}
