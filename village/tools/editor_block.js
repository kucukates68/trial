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
 for(const o of objects.filter(isItem)){const r=Math.hypot(o.w,o.d)/2+3,m=isParcel(o)?0.2:ROUTE.buf;for(let j=Math.max(0,Math.floor(o.z-r));j<Math.min(H,Math.ceil(o.z+r));j++)for(let i=Math.max(0,Math.floor(o.x-r));i<Math.min(W,Math.ceil(o.x+r));i++){const d=rectDist(o,i+.5,j+.5),idx=j*W+i;if(d<m)blk[idx]=1;else if(d<3&&!isParcel(o))soft[idx]+=(3-d)*.4}}
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
