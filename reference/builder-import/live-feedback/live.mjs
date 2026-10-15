import {IDS,compute,rms} from './model.mjs';
const $=id=>document.getElementById(id);
const canvas=$('view'), ctx=canvas.getContext('2d'), video=$('camera');
const buffer=document.createElement('canvas'); buffer.width=320; buffer.height=180;
const bx=buffer.getContext('2d',{willReadFrequently:true});
const loads=[1,1,1,1,1,1];
let stream=null,audio=null,source=null,analyser=null,samples=null,raf=0,epoch=0,frame=0,pending=false;
IDS.forEach((id,i)=>{
  const label=document.createElement('label'),title=document.createElement('span'),input=document.createElement('input');
  title.textContent=id.toUpperCase(); input.type='range';input.min='0';input.max='1';input.step='.01';input.value='1';
  input.setAttribute('aria-label',id+' synthetic load');input.addEventListener('input',()=>loads[i]=Number(input.value));
  label.append(title,input);$('loads').append(label);
});
function status(text){$('status').textContent=text+' Live engine gate CLOSED.';}
function clear(){ctx.clearRect(0,0,canvas.width,canvas.height);bx.clearRect(0,0,320,180);$('level').value=0;frame=0;}
function stop(message='Stopped. Devices off.'){
  ++epoch; pending=false;cancelAnimationFrame(raf);raf=0;
  if(stream) for(const track of stream.getTracks()) track.stop();stream=null;
  video.pause();video.srcObject=null;
  source?.disconnect();analyser?.disconnect();source=null;analyser=null;
  if(samples) samples.fill(0);samples=null;
  const closing=audio;audio=null;if(closing) void closing.close().catch(()=>{});
  clear();$('start').disabled=false;$('stop').disabled=true;status(message);
}
function draw(token){
  if(token!==epoch||!stream)return;
  try{
    analyser.getFloatTimeDomainData(samples);const level=rms(samples);$('level').value=level;
    if(video.readyState>=2){
      const {melt}=compute(loads,level);bx.drawImage(video,0,0,320,180);
      const input=bx.getImageData(0,0,320,180),out=bx.createImageData(320,180),phase=frame++*.023;
      for(let y=0;y<180;y++)for(let x=0;x<320;x++){
        const shift=melt*(12*Math.sin(y*.065+phase+Math.sin(x*.018)*2)+18*Math.sin(y*.017-phase*.6));
        const sag=melt*(10*Math.sin(x*.022+phase)+Math.max(0,y-70)*.11);
        const px=Math.max(0,Math.min(319,Math.floor(x+shift))),py=Math.max(0,Math.min(179,Math.floor(y+sag)));
        const a=(py*320+px)*4,b=(y*320+x)*4;
        out.data[b]=input.data[a];out.data[b+1]=input.data[a+1];out.data[b+2]=input.data[a+2];out.data[b+3]=255;
      }
      bx.putImageData(out,0,0);ctx.drawImage(buffer,0,0,canvas.width,canvas.height);
      input.data.fill(0);out.data.fill(0);
    }
    raf=requestAnimationFrame(()=>draw(token));
  }catch(error){stop('Visual processing failed: '+error.message);}
}
async function start(){
  if(pending||stream)return;
  if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia){status('Use HTTPS or localhost with a supported browser.');return;}
  const AC=window.AudioContext||window.webkitAudioContext;
  if(!AC){status('Web Audio is unavailable.');return;}
  pending=true;const token=++epoch;$('start').disabled=true;$('stop').disabled=false;status('Requesting camera and microphone permission.');
  let acquired=null,localAudio=null;
  try{
    localAudio=new AC();audio=localAudio;await localAudio.resume();
    if(token!==epoch){void localAudio.close().catch(()=>{});return;}
    acquired=await navigator.mediaDevices.getUserMedia({video:{width:{ideal:640},height:{ideal:360}},audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:false}});
    if(token!==epoch){acquired.getTracks().forEach(t=>t.stop());return;}
    stream=acquired;video.srcObject=stream;await video.play();
    if(token!==epoch)return;
    source=audio.createMediaStreamSource(stream);analyser=audio.createAnalyser();analyser.fftSize=1024;source.connect(analyser);
    samples=new Float32Array(analyser.fftSize);
    stream.getTracks().forEach(track=>track.addEventListener('ended',()=>{if(token===epoch)stop('Device disconnected or permission revoked.');},{once:true}));
    pending=false;status('Live camera + microphone. Synthetic visual output; no speaker playback.');draw(token);
  }catch(error){
    acquired?.getTracks().forEach(t=>t.stop());
    if(token===epoch)stop('Cannot start: '+error.name+'. '+error.message);
    else if(localAudio&&localAudio.state!=='closed')void localAudio.close().catch(()=>{});
  }
}
$('start').addEventListener('click',start);$('stop').addEventListener('click',()=>stop());
window.addEventListener('pagehide',()=>stop());
document.addEventListener('visibilitychange',()=>{if(document.hidden)stop('Paused for privacy because the page is hidden.');});
clear();
