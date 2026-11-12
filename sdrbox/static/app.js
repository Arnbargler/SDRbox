(() => {
"use strict";
const $ = id => document.getElementById(id);
const channels = [462.5625,462.5875,462.6125,462.6375,462.6625,462.6875,462.7125];
const canvas=$("spectrum-plot"),ctx=canvas.getContext("2d");
let connected=false,state=null,zoom="full";
function setConnected(yes){
  connected=yes;
  $("connection").textContent=yes?"LAN CONNECTED":"DISCONNECTED";
  $("connection").className=yes?"online":"offline";
  $("capture").disabled=!yes;
  $("sensitivity").disabled=!yes;
  if(!yes){$("receiver-state").textContent="DISCONNECTED";$("message").textContent="Connection lost · reconnecting…";}
  if(yes&&state)render(state);
}
function draw(data){
 const W=canvas.width,H=canvas.height,L=52,R=W-18,T=12,B=H-32;
 ctx.fillStyle="#0c1716";ctx.fillRect(0,0,W,H);
 if(!data||!data.power_db||!data.noise_db){
   ctx.fillStyle="#829e8d";ctx.font="20px system-ui";
   ctx.fillText("START CAPTURE TO SEE LIVE RF SPECTRUM",85,H/2);
   return;
 }
 const low=zoom==="gmrs"?462.49:data.low_mhz,high=zoom==="gmrs"?462.79:data.high_mhz;
 $("range-label").textContent=low.toFixed(3)+"–"+high.toFixed(3)+" MHz";
 const freq=i=>data.low_mhz+(i+0.5)*(data.high_mhz-data.low_mhz)/data.power_db.length;
 const idx=data.power_db.map((_,i)=>i).filter(i=>freq(i)>=low&&freq(i)<=high);
 if(!idx.length)return;
 const floors=idx.map(i=>data.noise_db[i]).sort((a,b)=>a-b);
 const base=floors[Math.floor(floors.length/2)];
 const min=base-11,max=Math.max(min+30,...idx.map(i=>data.power_db[i]+5));
 const X=f=>L+(f-low)/(high-low)*(R-L);
 const Y=v=>B-Math.min(1,Math.max(0,(v-min)/(max-min)))*(B-T);
 ctx.font="15px system-ui";ctx.lineWidth=1;
 for(let j=0;j<=4;j++){
  const y=T+j*(B-T)/4;
  ctx.strokeStyle="#274439";ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(R,y);ctx.stroke();
  ctx.fillStyle="#8ca99b";ctx.fillText((max-(max-min)*j/4).toFixed(0),8,y+5);
  const f=low+(high-low)*j/4;
  ctx.fillText(f.toFixed(3),Math.max(L-24,Math.min(R-64,X(f)-30)),H-8);
 }
 channels.forEach((f,i)=>{
  if(f<low||f>high)return;
  ctx.strokeStyle="#4c765e";ctx.setLineDash([4,5]);ctx.beginPath();
  ctx.moveTo(X(f),T);ctx.lineTo(X(f),B);ctx.stroke();ctx.setLineDash([]);
  if(zoom==="gmrs"){ctx.fillStyle="#d1edd4";ctx.fillText(String(i+1),X(f)-4,T+18);}
 });
 function trace(key,color,width){
  ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();
  idx.forEach((i,j)=>j?ctx.lineTo(X(freq(i)),Y(data[key][i])):ctx.moveTo(X(freq(i)),Y(data[key][i])));
  ctx.stroke();
 }
 trace("noise_db","#eabb78",2);
 trace("power_db","#7affb2",2.4);
 // Orange markers: unselected FFT candidates. Cyan: S3 locked choice.
 const selection=data.selection || {};
 (data.candidates || []).forEach(c => {
   const f=c.frequency_mhz;
   if(f<low||f>high)return;
   const x=X(f), isSelected=selection.frequency_mhz != null &&
      Math.abs(f-selection.frequency_mhz)<=0.008 &&
      (selection.status==="SELECTED" || selection.status==="HANG");
   ctx.strokeStyle=isSelected?"#61d9fc":c.provisional?"#86928e":"#ffcb6e";
   ctx.lineWidth=isSelected?3:2;
   ctx.setLineDash(c.provisional && !isSelected?[2,5]:[]);
   ctx.beginPath();ctx.moveTo(x,T+23);ctx.lineTo(x,B);ctx.stroke();ctx.setLineDash([]);
   if(!c.provisional) {
     ctx.fillStyle=isSelected?"#61d9fc":"#ffcb6e";
     ctx.beginPath();ctx.arc(x,T+21,isSelected?6:4,0,Math.PI*2);ctx.fill();
   }
 });
 // Keep the selected marker during brief RF dropouts (HANG).
 if(selection.status==="HANG" && selection.frequency_mhz>=low && selection.frequency_mhz<=high){
   const x=X(selection.frequency_mhz);
   ctx.strokeStyle="#61d9fc";ctx.setLineDash([5,5]);ctx.lineWidth=2.5;
   ctx.beginPath();ctx.moveTo(x,T+10);ctx.lineTo(x,B);ctx.stroke();ctx.setLineDash([]);
 }
}
function render(s){
 state=s;
 $("status").textContent=s.status;
 const running=s.status==="SCANNING";
 $("capture").textContent=running?"■ STOP CAPTURE":"▶ START CAPTURE";
 $("capture").classList.toggle("running",running);
 $("capture").disabled=!connected;
 $("receiver-state").textContent=running?"CAPTURING":s.status;
 $("message").textContent=s.message;
 $("sensitivity").value=String(s.threshold_db ?? 15);
 $("sensitivity-value").textContent="+"+(s.threshold_db ?? 15)+" dB";
 $("audio-status").textContent=s.audio?.startsWith("ERROR:")?"ERROR":s.audio?.includes("ACTIVE")?"RECEIVING":s.audio?.includes("STOPPED")?"STOPPED":"MUTED";
 const diag=s.spectrum?.audio_diagnostics;
 $("audio-detail").title=diag ? "IQ supply "+diag.pcm_supply_ratio+"x; block "+diag.iq_block_ms+"ms; USB read "+diag.avg_iq_read_ms+"ms; audio DSP "+diag.avg_processing_ms+"ms (cumulative average); IQ queue "+diag.iq_audio_queue_ms+"ms; IQ lost "+diag.iq_dropped_blocks+"; PCM queue "+diag.queued_ms+"ms; PCM drops "+diag.dropped_chunks : "";
 $("audio-detail").textContent=s.audio?.startsWith("ERROR:")?s.audio:
   diag && s.spectrum?.audio_gate
   ? "Gate "+s.spectrum.audio_gate+" · "+diag.pcm_supply_ratio+"x · R"+diag.avg_iq_read_ms+" P"+diag.avg_processing_ms+" · lost "+diag.iq_dropped_blocks
   : "Rackio speaker · 24 kHz NFM";
 if(s.spectrum){
   const sp=s.spectrum;
   const selection=sp.selection || {status:"SEARCHING",frequency_mhz:null};
   $("selection-status").textContent=selection.status;
   if(selection.frequency_mhz != null) {
     $("peak-frequency").textContent=Number(selection.frequency_mhz).toFixed(4)+" MHz";
     $("peak-contrast").textContent=selection.status==="HANG"
       ? "Signal lost · releasing in "+Number(selection.release_remaining_s).toFixed(1)+" s"
       : "+"+Number(selection.contrast_db).toFixed(1)+" dB · "+(selection.audio_active?"NFM audio active":"audio muted");
   }else{
     $("peak-frequency").textContent="— MHz";
     $("peak-contrast").textContent="Waiting for persistent signal";
   }
   const candidates=sp.candidates || [];
   const stable=candidates.filter(c=>!c.provisional);
   $("candidate-count").textContent=String(stable.length);
   const list=$("candidate-list");
   list.replaceChildren();
   if(!stable.length){
     const line=document.createElement("small");
     line.textContent=candidates.length?"Peaks seen; awaiting confirmation":"No persistent peaks above threshold";
     list.append(line);
   }else{
     stable.slice(0,2).forEach(c=>{
       const line=document.createElement("div");
       line.className="candidate-entry";
       const mhz=document.createElement("strong");
       mhz.textContent=Number(c.frequency_mhz).toFixed(4)+" MHz";
       const db=document.createElement("span");
       db.textContent="+"+Number(c.contrast_db).toFixed(1)+" dB";
       line.append(mhz,db);list.append(line);
     });
   }
   $("capture-label").textContent=sp.center_mhz.toFixed(3)+" MHz center · "+(sp.sample_rate_hz/1e6).toFixed(3)+" MS/s";
   $("capture-age").textContent="Last FFT: "+new Date(sp.captured_at*1000).toLocaleTimeString();
   draw(sp);
 }else{
   $("capture-age").textContent=running?"Waiting for IQ…":"No current IQ samples";
   $("candidate-count").textContent="0";
   $("candidate-list").replaceChildren();
   const noCandidates=document.createElement("small");
   noCandidates.textContent="Start capture to examine RF peaks";
   $("candidate-list").append(noCandidates);
   $("selection-status").textContent="SEARCHING";
   $("peak-frequency").textContent="— MHz";
   $("peak-contrast").textContent="No persistent candidate selected";
   draw(null);
 }
}
function setZoom(next){
 zoom=next;
 for(const key of ["full","gmrs"]){
  const b=$("zoom-"+key);b.classList.toggle("selected",key===next);
  b.setAttribute("aria-pressed",String(key===next));
 }
 if(state?.spectrum)draw(state.spectrum);
}
$("zoom-full").addEventListener("click",()=>setZoom("full"));
$("zoom-gmrs").addEventListener("click",()=>setZoom("gmrs"));
$("sensitivity").addEventListener("input",()=>{
 $("sensitivity-value").textContent="+"+$("sensitivity").value+" dB";
});
$("sensitivity").addEventListener("change",async()=>{
 if(!connected)return;
 const threshold_db=Number($("sensitivity").value);
 try{
  const response=await fetch("/api/v1/commands",{
   method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({command:"set_sensitivity",threshold_db})
  });
  if(!response.ok){const error=await response.json();$("message").textContent=error.detail||"Sensitivity change failed";}
 }catch(e){$("message").textContent="Cannot update RF sensitivity";}
});
$("capture").addEventListener("click",async()=>{
 if(!connected||!state)return;
 const command=state.status==="SCANNING"?"scan_stop":"scan_start";
 $("capture").disabled=true;
 try{
  const response=await fetch("/api/v1/commands",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({command})});
  if(!response.ok){const body=await response.json();$("message").textContent=body.detail||"Command failed";}
 }catch(e){$("message").textContent="Cannot contact SDRbox";}
 finally{$("capture").disabled=!connected;}
});
function connect(){
 const protocol=location.protocol==="https:"?"wss:":"ws:";
 const ws=new WebSocket(protocol+"//"+location.host+"/api/v1/events");
 ws.onopen=()=>setConnected(true);
 ws.onmessage=e=>{try{const p=JSON.parse(e.data);if(p.type==="snapshot")render(p.state);}catch(err){console.error("Invalid SDRbox snapshot",err);}};
 ws.onclose=()=>{setConnected(false);setTimeout(connect,1500);};
 ws.onerror=()=>ws.close();
}
draw(null);connect();
})();