/* ===================== YOL MANTIK EDİTÖRÜ =====================
   Kapı düğümü · ızgara + Dijkstra yönlendirme · bağlantı denetimi · mıknatıs (snap)
   Koordinatlar metre; X doğu, Z kuzey; rot derece (saat yönünün tersi +); rot=0 iken kapı güneye (-Z) bakar. */
const PARCEL_TYPES=['crop','pasture','orchard'];
const isParcel=o=>o.kind==='area'&&!o.pts&&PARCEL_TYPES.includes(o.type);
const isItem=o=>!o.pts&&o.w>0&&(o.kind==='building'||isParcel(o));
const isAccess=o=>o.kind==='path'&&(!!o.forId||/^access_/.test(o.uid||''));
const isRoadLike=o=>o.kind==='path'&&(o.type==='road'||o.type==='path');
const TARGET_IDS=new Set(groups.slice(0,6).flatMap(g=>g[2]).map(t=>t.id));
const rad=d=>d*Math.PI/180;
const ROUTE={buf:1.2,ramp:2.5,maxDoorGap:3};
let connBad=new Map(),hover=null,cursor=null;
function toLocal(o,px,pz){const a=rad(o.rot||0),c=Math.cos(a),s=Math.sin(a),dx=px-o.x,dz=pz-o.z;return [dx*c+dz*s,-dx*s+dz*c]}
function rectDist(o,px,pz){const [lx,lz]=toLocal(o,px,pz);return Math.hypot(Math.max(Math.abs(lx)-o.w/2,0),Math.max(Math.abs(lz)-o.d/2,0))}
function facingOf(o){const a=rad(o.rot||0);return [Math.sin(a),-Math.cos(a)]}
function doorNode(o){const [fx,fz]=facingOf(o),r=o.d/2+(isParcel(o)?1.2:1.5);return {x:o.x+fx*r,z:o.z+fz*r}}
function segClosest(px,pz,ax,az,bx,bz){const dx=bx-ax,dz=bz-az,l2=dx*dx+dz*dz;let t=l2?((px-ax)*dx+(pz-az)*dz)/l2:0;t=Math.max(0,Math.min(1,t));const x=ax+t*dx,z=az+t*dz;return {x,z,t,d:Math.hypot(px-x,pz-z)}}
function nearestOnPts(pts,px,pz){let b=null;for(let k=0;k<pts.length-1;k++){const r=segClosest(px,pz,pts[k].x,pts[k].z,pts[k+1].x,pts[k+1].z);if(!b||r.d<b.d)b={...r,k}}return b}
function inPoly(x,z,poly){let c=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a.z>z)!==(b.z>z)&&x<(b.x-a.x)*(z-a.z)/(b.z-a.z+1e-12)+a.x)c=!c}return c}
function sampleLine(pts,step){const out=[{x:pts[0].x,z:pts[0].z}];for(let k=0;k<pts.length-1;k++){const a=pts[k],b=pts[k+1],L=Math.hypot(b.x-a.x,b.z-a.z),n=Math.max(1,Math.ceil(L/step));for(let i=1;i<=n;i++)out.push({x:a.x+(b.x-a.x)*i/n,z:a.z+(b.z-a.z)*i/n})}return out}
function netLines(filter){return objects.filter(o=>isRoadLike(o)&&o.pts&&o.pts.length>1&&(!filter||filter(o)))}

/* ---- ızgara: su + bina tamponu engel, köprü/iskele geçilebilir ---- */
function buildGrid(){
 const W=mapW,H=mapH,blk=new Uint8Array(W*H),soft=new Float32Array(W*H).fill(1);
 const lake=objects.find(o=>o.type==='lake'&&o.pts),river=objects.find(o=>o.type==='river'&&o.pts);
 const hw=(river&&river.strokeW||12)/2+0.6;
 for(let j=0;j<H;j++)for(let i=0;i<W;i++){const x=i+.5,z=j+.5;let w=false;if(lake&&inPoly(x,z,lake.pts))w=true;else if(river){const p=river.pts;for(let k=0;k<p.length-1;k++){if(segClosest(x,z,p[k].x,p[k].z,p[k+1].x,p[k+1].z).d<hw){w=true;break}}}if(w)blk[j*W+i]=1}
 for(const o of objects.filter(o=>isItem(o)||o.type==='fountain')){const r=Math.hypot(o.w,o.d)/2+3,m=isParcel(o)?0.2:ROUTE.buf;for(let j=Math.max(0,Math.floor(o.z-r));j<Math.min(H,Math.ceil(o.z+r));j++)for(let i=Math.max(0,Math.floor(o.x-r));i<Math.min(W,Math.ceil(o.x+r));i++){const d=rectDist(o,i+.5,j+.5),idx=j*W+i;if(d<m)blk[idx]=1;else if(d<3&&!isParcel(o))soft[idx]+=(3-d)*.4}}
 for(const o of objects.filter(o=>o.kind==='utility'&&(o.type==='bridge'||o.type==='pier'))){const ob=o.type==='bridge'?{...o,w:o.w+2*ROUTE.ramp}:o,r=Math.hypot(ob.w,ob.d)/2+1;for(let j=Math.max(0,Math.floor(o.z-r));j<Math.min(H,Math.ceil(o.z+r));j++)for(let i=Math.max(0,Math.floor(o.x-r));i<Math.min(W,Math.ceil(o.x+r));i++)if(rectDist(ob,i+.5,j+.5)<=0){blk[j*W+i]=0;soft[j*W+i]=.7}}
 return {blk,soft,W,H};
}
function targetMask(lines){const W=mapW,H=mapH,m=new Uint8Array(W*H);for(const l of lines)for(const p of sampleLine(l.pts,.5)){const i=Math.floor(p.x),j=Math.floor(p.z);if(i>=0&&j>=0&&i<W&&j<H)m[j*W+i]=1}return m}
/* ikili yığın */
class Heap{constructor(){this.k=[];this.v=[]}get size(){return this.k.length}push(k,v){const K=this.k,V=this.v;let i=K.length;K.push(k);V.push(v);while(i){const p=(i-1)>>1;if(K[p]<=k)break;K[i]=K[p];V[i]=V[p];i=p}K[i]=k;V[i]=v}pop(){const K=this.k,V=this.v,rk=K[0],rv=V[0],lk=K.pop(),lv=V.pop(),n=K.length;if(n){let i=0;for(;;){let c=2*i+1;if(c>=n)break;if(c+1<n&&K[c+1]<K[c])c++;if(K[c]>=lk)break;K[i]=K[c];V[i]=V[c];i=c}K[i]=lk;V[i]=lv}return [rk,rv]}}
const NEI=[[1,0,1],[-1,0,1],[0,1,1],[0,-1,1],[1,1,Math.SQRT2],[1,-1,Math.SQRT2],[-1,1,Math.SQRT2],[-1,-1,Math.SQRT2]];
/* kapıdan en yakın hedef hücreye en ucuz hücre yolu (Dijkstra) */
function dijkstra(grid,start,mask){
 const {blk,soft,W,H}=grid,N=W*H,si=Math.min(W-1,Math.max(0,Math.floor(start.x))),sj=Math.min(H-1,Math.max(0,Math.floor(start.z))),s=sj*W+si;
 const ex=(i,j)=>{const dx=i+.5-start.x,dz=j+.5-start.z;return dx*dx+dz*dz<=5.8};
 const free=(i,j)=>!blk[j*W+i]||ex(i,j);
 const D=new Float32Array(N).fill(Infinity),par=new Int32Array(N).fill(-1),done=new Uint8Array(N),h=new Heap();D[s]=0;h.push(0,s);let found=-1;
 while(h.size){const [d,u]=h.pop();if(done[u])continue;done[u]=1;if(mask[u]&&u!==s){found=u;break}if(mask[u]&&u===s){found=u;break}const ui=u%W,uj=(u/W)|0;
  for(const [di,dj,m] of NEI){const vi=ui+di,vj=uj+dj;if(vi<0||vj<0||vi>=W||vj>=H)continue;const v=vj*W+vi;if(done[v]||!free(vi,vj))continue;if(di&&dj&&!(free(vi,uj)&&free(ui,vj)))continue;const nd=d+m*(soft[v]+soft[u])*.5;if(nd<D[v]){D[v]=nd;par[v]=u;h.push(nd,v)}}}
 if(found<0)return null;const cells=[];for(let u=found;u!==-1;u=par[u])cells.push({x:u%W+.5,z:((u/W)|0)+.5});cells.reverse();return cells;
}
function losClear(grid,a,b,start){const {blk,W,H}=grid;const L=Math.hypot(b.x-a.x,b.z-a.z),n=Math.max(1,Math.floor(L/.35));for(let i=0;i<=n;i++){const x=a.x+(b.x-a.x)*i/n,z=a.z+(b.z-a.z)*i/n,ci=Math.floor(x),cj=Math.floor(z);if(ci<0||cj<0||ci>=W||cj>=H)return false;if(blk[cj*W+ci]){const dx=x-start.x,dz=z-start.z;if(dx*dx+dz*dz>5.8)return false}}return true}
function simplifyPath(grid,pts,start){const out=[pts[0]];let i=0;while(i<pts.length-1){let j=pts.length-1;while(j>i+1&&!losClear(grid,pts[i],pts[j],start))j--;out.push(pts[j]);i=j}return out}
function chaikin(pts,it){for(let r=0;r<it;r++){if(pts.length<3)break;const n=[pts[0]];for(let k=0;k<pts.length-1;k++){const a=pts[k],b=pts[k+1];if(k>0)n.push({x:.75*a.x+.25*b.x,z:.75*a.z+.25*b.z});if(k<pts.length-2)n.push({x:.25*a.x+.75*b.x,z:.25*a.z+.75*b.z})}n.push(pts[pts.length-1]);pts=n}return pts}
function densify(pts,max){const o=[pts[0]];for(let k=0;k<pts.length-1;k++){const a=pts[k],b=pts[k+1],n=Math.max(1,Math.ceil(Math.hypot(b.x-a.x,b.z-a.z)/max));for(let i=1;i<=n;i++)o.push({x:a.x+(b.x-a.x)*i/n,z:a.z+(b.z-a.z)*i/n})}return o}
function pathFree(grid,pts,start){const {blk,W,H}=grid;for(const p of sampleLine(pts,.4)){const i=Math.floor(p.x),j=Math.floor(p.z);if(i<0||j<0||i>=W||j>=H)return false;if(blk[j*W+i]){const dx=p.x-start.x,dz=p.z-start.z;if(dx*dx+dz*dz>5.8)return false}}return true}
function round1(v){return Math.round(v*10)/10}
/* bir yapının kapı düğümünden en yakın ana sokağa kılcal patika */
function routeAccess(o,grid,mask,lines){
 const door=doorNode(o),cells=dijkstra(grid,door,mask);if(!cells)return null;
 const last=cells[cells.length-1];let end=null,bd=1e9;for(const l of lines){const r=nearestOnPts(l.pts,last.x,last.z);if(r&&r.d<bd){bd=r.d;end={x:r.x,z:r.z}}}
 let pts=[{x:door.x,z:door.z},...cells.slice(1)];if(end&&bd<2)pts[pts.length-1]=end;else if(end)pts.push(end);
 pts=simplifyPath(grid,pts,door);let sm=chaikin(densify(pts,6),2);if(!pathFree(grid,sm,door))sm=pts;
 sm[0]={x:door.x,z:door.z};
 return sm.map(p=>({x:round1(p.x),z:round1(p.z)}));
}
function accessObj(o,pts){return {uid:'access_'+o.id,id:'Access_'+o.id,label:'Kapı önü: '+(o.label||o.id),kind:'path',type:'path',strokeW:1.2,pts,lvl:3,gen:true,forId:o.id}}
/* binayı en yakın sokağa paralel döndür (kapı yola baksın) */
function alignDoor(o,lines){
 let best=null;for(const l of lines){const r=nearestOnPts(l.pts,o.x,o.z);if(r&&(!best||r.d<best.d)){const a=l.pts[r.k],b=l.pts[r.k+1],L=Math.hypot(b.x-a.x,b.z-a.z)||1;best={...r,ux:(b.x-a.x)/L,uz:(b.z-a.z)/L}}}
 if(!best)return false;const vx=best.x-o.x,vz=best.z-o.z,L=Math.hypot(vx,vz);if(L<1e-6)return false;
 let nx=-best.uz,nz=best.ux;if(nx*vx+nz*vz<0){nx=-nx;nz=-nz}const f=(nx*vx+nz*vz)/L>.75?[nx,nz]:[vx/L,vz/L];
 let r=Math.atan2(f[0],-f[1])*180/Math.PI;
 if(isParcel(o)){const cards=[[0,0,-1],[90,1,0],[180,0,1],[270,-1,0]];const c=cards.reduce((a,b)=>(b[1]*f[0]+b[2]*f[1]>a[1]*f[0]+a[2]*f[1])?b:a);const old=Math.round((o.rot||0)/90)%4,nw=c[0]/90;if((old&1)!==(nw&1)){const t=o.w;o.w=o.d;o.d=t}o.rot=c[0]===270?-90:c[0]}
 else{r=Math.round(r/5)*5;o.rot=((r+180)%360+360)%360-180}
 return true;
}
const routeLines=()=>netLines(l=>!isAccess(l)&&!l.deck);
function removeAccess(id){objects=objects.filter(a=>!(isAccess(a)&&a.forId===id))}
function setStatus(t){$('saveStatus').textContent=t}
/* tek yapı: sürükleme sonrası */
function refreshItem(o,align){
 removeAccess(o.id);const lines=routeLines();if(align)alignDoor(o,lines);
 const grid=buildGrid(),pts=routeAccess(o,grid,targetMask(lines),lines);
 if(pts){objects.push(accessObj(o,pts));return true}return false;
}
/* tüm yapılar: "Yolları Otomatik Ör / Yenile" */
function refreshAll(align){
 saveUndo();const lines=routeLines(),items=objects.filter(isItem);
 for(const o of items)removeAccess(o.id);
 objects=objects.filter(a=>!(isAccess(a)&&!items.some(i=>i.id===a.forId)));
 if(align)for(const o of items)alignDoor(o,lines);
 const grid=buildGrid(),mask=targetMask(lines),failed=[];
 for(const o of items){const pts=routeAccess(o,grid,mask,lines);if(pts)objects.push(accessObj(o,pts));else failed.push(o.id)}
 render();persist();
 setStatus(failed.length?`Ağ örüldü · rota bulunamayan: ${failed.slice(0,4).join(', ')}${failed.length>4?'…':''}`:`Ağ örüldü · ${items.length} kapı patikası yenilendi`);
}

/* ---- bağlantı denetimi: yola ≤3 m ve ana ağa bağlı mı? ---- */
function computeConn(){
 const lines=netLines(),bad=new Map();if(!lines.length){for(const o of objects)if(isItem(o)&&TARGET_IDS.has(o.id))bad.set(o.id,'ağ yok');return bad}
 const hash=new Map(),key=(i,j)=>i*4096+j,CS=1.5;const samples=[];
 lines.forEach((l,k)=>{for(const p of sampleLine(l.pts,.5)){samples.push([k,p.x,p.z]);const kk=key(Math.floor(p.x/CS),Math.floor(p.z/CS));(hash.get(kk)||hash.set(kk,[]).get(kk)).push(samples.length-1)}});
 const par=lines.map((_,i)=>i),find=a=>{while(par[a]!==a){par[a]=par[par[a]];a=par[a]}return a};
 for(const [k,x,z] of samples){const ci=Math.floor(x/CS),cj=Math.floor(z/CS);for(let di=-1;di<=1;di++)for(let dj=-1;dj<=1;dj++){const arr=hash.get(key(ci+di,cj+dj));if(!arr)continue;for(const id of arr){const s=samples[id];if(s[0]!==k&&(s[1]-x)**2+(s[2]-z)**2<.81){const a=find(k),b=find(s[0]);if(a!==b)par[a]=b}}}}
 const len={};lines.forEach((l,k)=>{const r=find(k);len[r]=(len[r]||0)+l.pts.length});let main=null,mx=-1;for(const r in len)if(len[r]>mx){mx=len[r];main=+r}
 for(const o of objects){if(!isItem(o)||!TARGET_IDS.has(o.id))continue;const d=doorNode(o),ci=Math.floor(d.x/CS),cj=Math.floor(d.z/CS);let best=1e9,bk=-1;
  for(let di=-3;di<=3;di++)for(let dj=-3;dj<=3;dj++){const arr=hash.get(key(ci+di,cj+dj));if(!arr)continue;for(const id of arr){const s=samples[id],dd=Math.hypot(s[1]-d.x,s[2]-d.z);if(dd<best){best=dd;bk=s[0]}}}
  if(best>ROUTE.maxDoorGap)bad.set(o.id,`kapı yola ${best>99?'>4':best.toFixed(1)} m`);else if(find(bk)!==main)bad.set(o.id,'ana ağdan kopuk');}
 return bad;
}

/* ---- mıknatıs: yol düğümü / bina kapısı / yol kenarı ---- */
function snapTarget(p,ignoreUid){
 const R=2.5;let best=null;
 for(const l of netLines(l=>l.uid!==ignoreUid&&l.type!=='river'))for(const v of l.pts){const d=Math.hypot(v.x-p.x,v.z-p.z);if(d<R&&(!best||d<best.d))best={x:v.x,z:v.z,d,kind:'node'}}
 for(const o of objects){if(!isItem(o)||o.uid===ignoreUid)continue;const d0=doorNode(o),d=Math.hypot(d0.x-p.x,d0.z-p.z);if(d<R&&(!best||d<best.d+.01))best={x:d0.x,z:d0.z,d,kind:'door'}}
 if(!best)for(const l of netLines(l=>l.uid!==ignoreUid&&l.type!=='river')){const r=nearestOnPts(l.pts,p.x,p.z);if(r&&r.d<1.3&&(!best||r.d<best.d))best={x:r.x,z:r.z,d:r.d,kind:'edge'}}
 return best;
}
function snapDraw(p,ignoreUid){const t=snapTarget(p,ignoreUid);return t?{x:round1(t.x),z:round1(t.z)}:snap(p)}
function setHover(t,c){const a=hover,b=t;hover=t;cursor=c||cursor;if(!a&&!b&&!drawPts.length)return;drawOverlay()}
function drawOverlay(){
 const g=document.getElementById('overlay');if(!g)return;let s='';
 if(drawPts.length&&cursor){const last=drawPts[drawPts.length-1],c=hover||cursor;s+=`<line x1="${mapPx(last.x)}" y1="${mapPy(last.z)}" x2="${mapPx(c.x)}" y2="${mapPy(c.z)}" stroke="#263f36" stroke-width="1.5" stroke-dasharray="4 3" opacity=".7"/>`}
 if(hover){const col=hover.kind==='door'?'#e0573c':hover.kind==='node'?'#1f7a4d':'#2b6cb0';s+=`<circle cx="${mapPx(hover.x)}" cy="${mapPy(hover.z)}" r="7" fill="${col}" fill-opacity=".18" stroke="${col}" stroke-width="2"/><circle cx="${mapPx(hover.x)}" cy="${mapPy(hover.z)}" r="2" fill="${col}"/>`}
 g.innerHTML=s;
}

/* ===================== TASARIM MANTIK DENETİMİ (7 kural, canlı) =====================
   Python karşılığı: village_semantic_linter.py (aynı eşikler). */
function polyEdgeDist(x,z,poly){let b=1e9;for(let i=0;i<poly.length;i++){const a=poly[i],c=poly[(i+1)%poly.length],d=segClosest(x,z,a.x,a.z,c.x,c.z).d;if(d<b)b=d}return b}
function mkWater(){
 const lake=objects.find(o=>o.type==='lake'&&o.pts),river=objects.find(o=>o.type==='river'&&o.pts),hw=(river&&river.strokeW||12)/2;
 const rd=(x,z)=>{if(!river)return 99;let b=1e9;const p=river.pts;for(let k=0;k<p.length-1;k++){const d=segClosest(x,z,p[k].x,p[k].z,p[k+1].x,p[k+1].z).d;if(d<b)b=d}return b-hw};
 const ld=(x,z)=>{if(!lake)return 99;const d=polyEdgeDist(x,z,lake.pts);return inPoly(x,z,lake.pts)?-d:d};
 return {rd,ld,wd:(x,z)=>Math.min(rd(x,z),ld(x,z))};
}
function boundaryPts(o,step){const hw=o.w/2,hd=o.d/2,out=[],E=[[-hw,-hd,hw,-hd],[hw,-hd,hw,hd],[hw,hd,-hw,hd],[-hw,hd,-hw,-hd]],a=rad(o.rot||0),c=Math.cos(a),s=Math.sin(a);
 for(const [ax,az,bx,bz] of E){const n=Math.max(1,Math.floor(Math.hypot(bx-ax,bz-az)/step));for(let i=0;i<n;i++){const t=i/n,lx=ax+(bx-ax)*t,lz=az+(bz-az)*t;out.push({x:o.x+lx*c-lz*s,z:o.z+lx*s+lz*c})}}return out}
function rectGapJS(a,b){let best=99;for(const [p,q] of [[a,b],[b,a]])for(const pt of boundaryPts(p,.5)){const d=rectDist(q,pt.x,pt.z);if(d<best)best=d}return best}
const LINT_TRIPLES=[['W_House_',[1,2,3]],['W_House_',[4,5,6]],['E_House_',[1,2,3]],['E_House_',[5,6,7]],['E_House_',[8,9,10]],['E_House_',[11,12,13]],['Dock_Build_',[1,2,3]],['Dock_Build_',[2,3,4]],['Dock_Build_',[5,6,7]],['Dock_Build_',[6,7,8]]];
function lintAll(){
 const by=id=>objects.find(o=>o.id===id),Wt=mkWater(),items=objects.filter(isItem),res=[],f1=n=>n.toFixed(1);
 const fountain=objects.find(o=>o.type==='fountain'),plaza=by('Market_Plaza'),pad=n=>String(n).padStart(2,'0');
 /* 1 su kıyısı */
 {const m=[];for(const id of ['Boat_House_01','Boat_House_02']){const o=by(id);if(!o){m.push(id+' yok');continue}
   let bd=1e9;for(const p of boundaryPts(o,.5)){const d=Wt.wd(p.x,p.z);if(d<bd)bd=d}
   if(bd<-.05)m.push(id+' suyun içinde');else if(bd>4)m.push(`${id} kıyıdan ${f1(bd)} m uzak (en çok 4 m)`);
   else{let wp=null;for(let r=.5;r<30&&!wp;r+=.5)for(let k=0;k<36;k++){const a=k*Math.PI/18,x=o.x+Math.cos(a)*r,z=o.z+Math.sin(a)*r;if(Wt.wd(x,z)<=.3){wp={x,z};break}}
    if(wp){const vx=wp.x-o.x,vz=wp.z-o.z,L=Math.hypot(vx,vz)||1,f=facingOf(o);if((f[0]*vx+f[1]*vz)/L<-.2)m.push(id+' cephesi sudan uzağa bakıyor')}}}
  const mill=by('Watermill_01');if(!mill)m.push('Watermill_01 yok');else{let dep=-1e9;for(const p of boundaryPts(mill,.25)){const d=-Wt.rd(p.x,p.z);if(d>dep)dep=d}if(dep<1)m.push(`Watermill_01 çarkı suya ${f1(Math.max(dep,0))} m giriyor (en az 1.0 m)`)}
  res.push({name:'Su kıyısı zorunluluğu',m});}
 /* 2 çiftlik */
 {const m=[],hay=by('Hay_Storage'),pa=by('Pasture_Area_01'),barns=['Farm_Barn_01','Farm_Barn_02'].map(by).filter(Boolean);
  if(!(hay&&pa&&barns.length))m.push('çiftlik öğeleri eksik');else{
   const dh=Math.min(...barns.map(b=>rectGapJS(hay,b)));if(dh>18)m.push(`Samanlık ahırdan ${f1(dh)} m uzak (en çok 18 m)`);
   let dl=1e9;for(const p of boundaryPts(pa,.5)){const d=Wt.ld(p.x,p.z);if(d<dl)dl=d}if(dl<12)m.push(`Otlak göle ${f1(dl)} m yakın (en az 12 m)`);
   const dp=Math.min(...barns.map(b=>rectGapJS(pa,b)));if(dp>15)m.push(`Otlak ahırlardan ${f1(dp)} m uzak (en çok 15 m)`)}
  res.push({name:'Çiftlik ve hayvancılık bütünlüğü',m});}
 /* 3 tarım */
 {const m=[],plots=['Crop_Plot_01','Crop_Plot_02','Crop_Plot_03','Orchard_Plot'].map(by).filter(Boolean);
  for(const p of plots)if(p.z<52||p.z>165)m.push(`${p.id} z=${p.z.toFixed(0)}: tarım kuşağı dışında (52..165)`);
  for(const p of plots)if(plots.length>1&&Math.min(...plots.filter(q=>q!==p).map(q=>rectGapJS(p,q)))>15)m.push(`${p.id} diğer tarım parsellerine komşu değil`);
  for(const o of objects)if(o.gen&&o.kind==='area'&&(o.type==='crop'||o.type==='orchard')&&o.pts){const cz=o.pts.reduce((a,p)=>a+p.z,0)/o.pts.length;if(cz>140||cz<52)m.push(`${o.id} (${o.type}) z=${cz.toFixed(0)}: ekin/meyve olamaz`)}
  res.push({name:'Tarım ve coğrafya uyumu',m});}
 /* 4 zanaat/liman */
 {const m=[],ws=by('Repair_Workshop_01'),nal=by('Market_Shop_04');
  if(ws&&nal){const d=Math.hypot(ws.x-nal.x,ws.z-nal.z);if(d>30)m.push(`Nalbant (M04) atölyeden ${d.toFixed(0)} m uzak (en çok 30 m)`)}
  const cz=plaza&&plaza.pts?plaza.pts.reduce((a,p)=>a+p.z,0)/plaza.pts.length:96.5;
  for(const id of ['Market_Shop_06','Market_Shop_09','Market_Shop_10']){const s=by(id);if(s&&s.z>=cz)m.push(id+' pazarın kuzey yarısında (balıkçı dükkânları güneyde olmalı)')}
  res.push({name:'Zanaat ve liman komşuluğu',m});}
 /* 5 çeşitlilik */
 {const m=[],houses=items.filter(o=>o.type==='house'),small=houses.filter(o=>o.w<4.6||o.d<4).map(o=>o.id);
  if(small.length)m.push('Kulübe boyutu (<4.6x4.0 m): '+small.slice(0,4).join(', ')+(small.length>4?'…':''));
  const sizes=new Set(houses.map(o=>f1(o.w)+'x'+f1(o.d)));if(sizes.size<3)m.push(`Ev ölçüsü çeşitliliği yetersiz (${sizes.size} tür, en az 3)`);
  for(const [pre,ids] of LINT_TRIPLES){const tri=ids.map(i=>by(pre+pad(i)));if(tri.some(t=>!t))continue;
   const zs=tri.map(t=>t.z),rs=tri.map(t=>t.rot||0),zr=Math.max(...zs)-Math.min(...zs),rr=Math.max(...rs)-Math.min(...rs);
   if(zr<1.5||rr<5)m.push(`${tri[0].id}..: asker sırası (z farkı ${f1(zr)} m, açı farkı ${rr.toFixed(0)}°)`)}
  res.push({name:'Organik çeşitlilik (anti copy-paste)',m});}
 /* 6 meydan */
 {const m=[];if(!fountain)m.push('Village_Fountain yok');else{
   if(plaza&&plaza.pts&&!inPoly(fountain.x,fountain.z,plaza.pts))m.push('Çeşme meydanın dışında');
   for(const l of objects.filter(l=>isRoadLike(l)&&l.pts&&!l.deck&&!isAccess(l))){const r=nearestOnPts(l.pts,fountain.x,fountain.z);if(r&&r.d<4)m.push(`${l.id} çeşmeye ${f1(r.d)} m yakın (en az 4 m)`)}
   for(const id of ['Stall_A','Stall_B']){const s=by(id);if(s){const vx=fountain.x-s.x,vz=fountain.z-s.z,L=Math.hypot(vx,vz)||1,f=facingOf(s);if((f[0]*vx+f[1]*vz)/L<.5)m.push(id+' çeşmeye bakmıyor')}}}
  res.push({name:'Meydan ve odak noktası',m});}
 /* 7 çarpışma + erişim */
 {const m=[];
  for(let i=0;i<items.length;i++)for(let j=i+1;j<items.length;j++){const a=items[i],b=items[j];if(Math.hypot(a.x-b.x,a.z-b.z)>(Math.hypot(a.w,a.d)+Math.hypot(b.w,b.d))/2)continue;if(rectGapJS(a,b)<=0)m.push(`çarpışma: ${a.id} ↔ ${b.id}`)}
  for(const o of items)if(o.kind==='building'&&o.type!=='mill'&&boundaryPts(o,.5).some(p=>Wt.wd(p.x,p.z)<-.05))m.push(o.id+' suyun içinde');
  const solids=objects.filter(o=>(isItem(o)&&o.kind==='building')||o.type==='fountain'),ramps=objects.filter(o=>o.type==='pier'||o.type==='bridge').map(o=>o.type==='bridge'?{...o,w:o.w+6}:o);
  let nb=0,nw=0;
  for(const l of netLines()){const hs=(l.strokeW||2)/2;for(const p of sampleLine(l.pts,.5)){
    if(!ramps.some(r=>rectDist(r,p.x,p.z)<=.05)&&Wt.wd(p.x,p.z)<0)nw++;
    for(const o of solids){const R=Math.hypot(o.w,o.d)/2+hs+1;if(Math.abs(o.x-p.x)>R||Math.abs(o.z-p.z)>R)continue;if(rectDist(o,p.x,p.z)<hs-.02){nb++;break}}}}
  if(nb)m.push(`yol-bina kesişimi: ${nb} örnek nokta`);if(nw)m.push(`yol-su kesişimi: ${nw} örnek nokta`);
  const bad=[...connBad.keys()].filter(id=>TARGET_IDS.has(id));if(bad.length)m.push('yola bağlanmayan/kopuk: '+bad.slice(0,5).join(', '));
  res.push({name:'Sıfır çarpışma + %100 erişim',m});}
 return res;
}
function updateLint(){
 const el=$('lint');if(!el)return;let res;try{res=lintAll()}catch(err){el.innerHTML='<small>Denetim hatası: '+esc(err.message)+'</small>';return}
 const ok=res.filter(r=>!r.m.length).length;
 el.innerHTML=`<b class="${ok===res.length?'stat-ok':'stat-bad'}">Tasarım Mantık Denetimi: ${ok} / ${res.length} Kural Geçti</b>`+res.map((r,i)=>`<div class="lint-row ${r.m.length?'bad':'ok'}"><span>${r.m.length?'✗':'✓'} ${i+1}. ${esc(r.name)}</span>${r.m.length?`<small>${esc(r.m.slice(0,3).join(' · '))}${r.m.length>3?' …':''}</small>`:''}</div>`).join('');
}
