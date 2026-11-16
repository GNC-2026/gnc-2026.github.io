# Builds the public GitHub Pages scoreboard from the dashboard's live data.
# usage: python3 build.py <live.json> <outdir> [--assets]
import re,json,sys,os,base64,html,io,time,datetime
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__))
live=json.load(open(sys.argv[1])); live=live.get('data',live); out=sys.argv[2]
X=json.load(open(HERE+'/data.json'))
P={int(k):v for k,v in X['players'].items()}; PH=set(X['photos'])
TEAMS=X['teams']; TM={t['key']:t for t in TEAMS}; RET=X['ret']
CATS=['A+','A','B+','B','WD'];SL={'A+':2,'A':2,'B+':5,'B':5,'WD':2};PROT={'A+':70000,'A':70000,'B+':70000,'B':30000,'WD':30000}
QC={'A+':'#e8b931','A':'#3ddc84','B+':'#4d94ec','B':'#a97ef0','WD':'#f39237'}
PURSE=985000
e=html.escape
def fmt(v):
  v=int(v);s=str(v);h,t=s[:-3],s[-3:]
  return (re.sub(r'(\d)(?=(\d\d)+$)',r'\1,',h)+','+t) if h else t
ph=lambda i,c='':f'<img class="{c}" src="img/p{i}.jpg" alt="" loading="lazy">' if str(i) in PH else f'<span class="{c} np">{e(P[i]["name"][:1])}</span>'
lg=lambda t:f'<img class="lg" src="img/l{t["logo"]}.png" alt="">'
sales=[dict(id=int(k),**v) for k,v in live.get('sales',{}).items() if int(k) in P]
recent=sorted(sales,key=lambda x:-x.get('t',0)); top=sorted(sales,key=lambda x:-x['price'])
lot=live.get('lot') or {}; lid=lot.get('id'); onblock=lid and str(lid) not in live.get('sales',{}) and str(lid) not in live.get('unsold',{}) and int(lid) in P
spent=sum(x['price'] for x in sales)
def stats(k):
  cats={c:0 for c in CATS};lst=[]
  for r in RET:
    if r['team']==k: cats[P[r['id']]['cat']]+=1;lst.append(dict(id=r['id'],role=r['role'],price=None))
  sp=0
  for x in sales:
    if x['team']==k: cats[P[x['id']]['cat']]+=1;sp+=x['price'];lst.append(dict(id=x['id'],price=x['price'],t=x.get('t',0)))
  op={c:max(0,SL[c]-cats[c]) for c in CATS};prot=sum(op[c]*PROT[c] for c in CATS)
  return dict(cats=cats,lst=lst,rem=PURSE-sp,spent=sp,count=len(lst),open=op,prot=prot)
catbar=''.join(f'<div class="c" style="--q:{QC[c]}"><b>{c}</b><i><u style="width:{round(100*(sum(1 for r in RET if P[r["id"]]["cat"]==c)+sum(1 for x in sales if P[x["id"]]["cat"]==c))/(SL[c]*6))}%"></u></i><em>{sum(1 for r in RET if P[r["id"]]["cat"]==c)+sum(1 for x in sales if P[x["id"]]["cat"]==c)}/{SL[c]*6}</em></div>' for c in CATS)
teams=''
for t in TEAMS:
  st=stats(t['key']);mine=[x for x in recent if x['team']==t['key']]
  pips=''.join(f'<span class="pg"><em>{c}</em>'+''.join(f'<i class="{"on" if j<st["cats"][c] else ""}"></i>' for j in range(SL[c]))+'</span>' for c in CATS)
  roster=''
  for c in CATS:
    ps=[x for x in st['lst'] if P[x['id']]['cat']==c]
    ps.sort(key=lambda x:(0 if x.get('role') else 1,-(x['price'] or 0)))
    roster+=f'<div class="rc" style="--q:{QC[c]}">{c}</div>'+''.join(f'<div class="rp">{ph(x["id"])}<b>{e(P[x["id"]]["name"])}</b><span>{(x["role"] if x.get("role") else fmt(x["price"]))}</span></div>' for x in ps)+''.join('<div class="rp open">Open slot</div>' for _ in range(st['open'][c]))
  teams+=f'''<details class="t" style="--tc:{t["c"]}"><summary><div class="th">{lg(t)}<b>{e(t["name"])}</b><em><i>{st["count"]}</i>/16</em></div>
<div class="mn"><div><span>Purse left</span><b>{fmt(st["rem"])}</b></div><div class="r"><span>Protected · Free</span><b class="s">{fmt(st["prot"])} · {fmt(max(0,st["rem"]-st["prot"]))}</b></div></div>
<div class="bar"><u style="width:{round(100*st["rem"]/PURSE)}%"></u></div><div class="pips">{pips}</div>
{f'<div class="lb">{ph(mine[0]["id"])}<div><small>Latest buy</small><b>{e(P[mine[0]["id"]]["name"])}</b></div><span>{fmt(mine[0]["price"])}</span></div>' if mine else '<div class="lb none">No buys yet</div>'}
<div class="more">Tap to see full squad</div></summary><div class="roster">{roster}</div></details>'''
if onblock:
  ld=TM.get(lot.get('team') or '')
  hero=f'<div class="hero"><span class="tag"><i></i>On the block · {P[int(lid)]["cat"]}</span><div class="hb">{ph(int(lid),"big")}<div><h2>{e(P[int(lid)]["name"])}</h2><small>{"Current bid" if ld else "Opening bid"}</small><div class="amt">{fmt(lot.get("bid",5000))}</div>{f"<div class=who style=--tc:{ld['c']}>{lg(ld)}{e(ld['name'])}</div>" if ld else ""}</div></div></div>'
elif recent:
  x=recent[0];t=TM[x['team']]
  hero=f'<div class="hero sold" style="--tc:{t["c"]}"><span class="tag">Just sold</span><div class="hb">{ph(x["id"],"big")}<div><h2>{e(P[x["id"]]["name"])}</h2><div class="amt">{fmt(x["price"])}</div><div class="who">{lg(t)}{e(t["name"])}</div></div></div></div>'
else: hero='<div class="hero"><span class="tag">Starting soon</span><p class="soon">The auction opens with the A+ players. Results will appear here.</p></div>'
rows=lambda arr,rank=False:''.join(f'<div class="row" style="--tc:{TM[x["team"]]["c"]}">'+ph(x['id'])+f'<div><b>{e(P[x["id"]]["name"])}</b><small>{e(TM[x["team"]]["name"])}</small></div><span class="p">{fmt(x["price"])}</span></div>' for i,x in enumerate(arr))
rules='<ol class="rlist">'+open(HERE+'/rules_frag.html').read()+'</ol>'
# --- squads tab ---
squads=''
for t in TEAMS:
  st=stats(t['key']);ro=''
  for c in CATS:
    ps=sorted([x for x in st['lst'] if P[x['id']]['cat']==c],key=lambda x:(0 if x.get('role') else 1,-(x['price'] or 0)))
    ro+=f'<div class="rc" style="--q:{QC[c]}">{c} <em>{st["cats"][c]}/{SL[c]}</em></div>'+''.join(f'<div class="rp">{ph(x["id"])}<b>{e(P[x["id"]]["name"])}</b><span>{(x["role"] if x.get("role") else fmt(x["price"]))}</span></div>' for x in ps)+''.join('<div class="rp open">Open slot</div>' for _ in range(st['open'][c]))
  squads+=f'<div class="sq" style="--tc:{t["c"]}"><div class="th">{lg(t)}<b>{e(t["name"])}</b><em><i>{st["count"]}</i>/16</em></div><div class="sqm"><span>Purse left <b>{fmt(st["rem"])}</b></span><span>Spent <b>{fmt(st["spent"])}</b></span></div>{ro}</div>'
# --- players tab ---
retd={r['id']:r for r in RET}; sold={x['id']:x for x in sales}; uns=live.get('unsold',{})
cards=''
for i in sorted(P):
  c=P[i]['cat']
  if i in retd: tag,cls=f'{retd[i]["role"]} · {e(TM[retd[i]["team"]]["name"])}','ret';tc=TM[retd[i]['team']]['c']
  elif i in sold: tag,cls=f'{e(TM[sold[i]["team"]]["name"])} · {fmt(sold[i]["price"])}','sold';tc=TM[sold[i]['team']]['c']
  elif str(i) in uns: tag,cls='Unsold · recall','uns';tc='#888'
  else: tag,cls='Yet to come','',;tc='#e8b931'
  cards+=f'<div class="pc {cls}" data-c="{c}" data-s="{cls or "wait"}" data-n="{e(P[i]["name"].lower())} #{i}" style="--tc:{tc}"><div class="im">{ph(i)}<span class="no">#{i}</span><span class="ct" style="background:{QC[c]}">{c}</span></div><b>{e(P[i]["name"])}</b><small>{tag}</small></div>'
fbtn=''.join(f'<button data-f="{c}">{c}</button>' for c in ['All']+CATS)
sbtn=''.join(f'<button data-g="{k}">{v}</button>' for k,v in [('all','Everyone'),('sold','Sold'),('wait','Yet to come'),('uns','Unsold'),('ret','Owners & strategists')])
# recent sales for the SOLD reveals (newest 8, sent oldest first)
LAST=[dict(t=x.get('t',0),name=P[x['id']]['name'],team=TM[x['team']]['name'],c=TM[x['team']]['c'],logo=TM[x['team']]['logo'],price=fmt(x['price']),photo=(f'img/p{x["id"]}.jpg' if str(x['id']) in PH else ''),kind=x.get('kind','')) for x in reversed(recent[:8])]
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5,minutes=30)))
asof=datetime.datetime.fromtimestamp((live.get('at') or time.time()*1000)/1000,datetime.timezone(datetime.timedelta(hours=5,minutes=30)))
page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GNC BPL 2026 · Live Scoreboard</title>
<link rel="icon" href="img/club.png"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;600&display=swap">
<style>{open(HERE+'/style.css').read()}</style></head><body>
<header><img class="club" src="img/club.png" alt=""><div><h1>GNC Badminton <span>Premier League</span> 2026</h1><p>Player auction · live scoreboard</p></div>
<div class="upd"><i></i>Results as of {asof.strftime("%-I:%M %p").lower()} · updates about every minute</div></header>
<nav class="tabs"><a href="#scoreboard" data-t="scoreboard">Scoreboard</a><a href="#squads" data-t="squads">Squads</a><a href="#players" data-t="players">Players</a><a href="#rules" data-t="rules">Rules</a></nav>
<main id="v-scoreboard" class="view"><div class="L"><div class="kp"><div><b>{len(sales)+len(RET)}/96</b><span>Players signed</span></div><div><b>{fmt(spent)}</b><span>Total spent</span></div><div><b>{fmt(top[0]["price"]) if top else "–"}</b><span>Top buy{(" · "+e(P[top[0]["id"]]["name"].split()[0])) if top else ""}</span></div><div><b>{len(sales)}</b><span>Sold at auction</span></div></div>
<div class="cats">{catbar}</div><div class="teams">{teams}</div></div>
<div class="R"><div class="box"><h4>Top buys</h4>{rows(top[:5],True) or '<p class="em">No sales yet</p>'}</div><div class="box"><h4>Recently sold</h4>{rows(recent[:8]) or '<p class="em">No sales yet</p>'}</div></div></main>
<section id="v-squads" class="view" hidden><div class="sqsearch"><input id="sqq" type="search" placeholder="Search a player…" autocomplete="off"><span id="sqn"></span></div><div class="sqs">{squads}</div></section>
<section id="v-players" class="view" hidden><div class="flt"><input id="pq" type="search" placeholder="Search name or #number…" autocomplete="off"><div class="seg">{fbtn}</div><div class="seg">{sbtn}</div></div><div class="grid">{cards}</div></section>
<section id="v-rules" class="view rules" hidden><h2>Player auction – rules &amp; guidelines</h2><p class="rsub">Monday, 16 November 2026 · 6:00 PM · GNC Conference Hall, First Floor</p>{rules}</section>
<footer>Unofficial live mirror of the auction dashboard · updates about every minute</footer>
<div id="sov" hidden></div><canvas id="cf"></canvas>
<script>const LAST={json.dumps(LAST)};</script>
<script>
const V=['scoreboard','squads','players','rules'];
function show(){{const v=V.includes(location.hash.slice(1))?location.hash.slice(1):'scoreboard';V.forEach(x=>document.getElementById('v-'+x).hidden=x!==v);document.querySelectorAll('.tabs a').forEach(a=>a.classList.toggle('on',a.dataset.t===v))}}
addEventListener('hashchange',()=>{{show();scrollTo(0,0)}});show();
let f='All',g='all';const pq=document.getElementById('pq');const ap=()=>{{const q=pq.value.trim().toLowerCase();document.querySelectorAll('.pc').forEach(p=>p.hidden=!((f==='All'||p.dataset.c===f)&&(g==='all'||p.dataset.s===g)&&(!q||p.dataset.n.includes(q))))}};pq.oninput=ap;
document.querySelectorAll('[data-f]').forEach(b=>b.onclick=()=>{{f=b.dataset.f;document.querySelectorAll('[data-f]').forEach(x=>x.classList.toggle('on',x===b));ap()}});
document.querySelectorAll('[data-g]').forEach(b=>b.onclick=()=>{{g=b.dataset.g;document.querySelectorAll('[data-g]').forEach(x=>x.classList.toggle('on',x===b));ap()}});
document.querySelector('[data-f]').classList.add('on');
const sqq=document.getElementById('sqq');sqq.oninput=()=>{{const v=sqq.value.trim().toLowerCase();let n=0;document.querySelectorAll('#v-squads .rp').forEach(r=>{{const b=r.querySelector('b');const m=!v||(b&&b.textContent.toLowerCase().includes(v));r.hidden=!m;if(v&&m)n++}});document.querySelectorAll('#v-squads .rc').forEach(c=>c.hidden=!!v);document.getElementById('sqn').textContent=v?(n?n+' found':'No match'):''}};document.querySelector('[data-g]').classList.add('on');
// reload for fresh results every 15 s, but only on the Scoreboard and Squads tabs (and keep the scroll position)
try{{const y=sessionStorage.getItem('y');if(y)scrollTo(0,+y)}}catch(e){{}}
// SOLD moments: every sale this viewer hasn't seen yet (under 5 min old, at most 4), oldest first; a first-time visitor sees only the newest
let sov=false;
(function(){{if(!LAST.length)return;let seen=null;try{{seen=localStorage.getItem('seen')}}catch(e){{}}
 const newest=LAST[LAST.length-1].t;try{{localStorage.setItem('seen',newest)}}catch(e){{}}
 let q=LAST.filter(x=>Date.now()-x.t<300000&&(seen===null?x.t===newest:x.t>+seen)).slice(-4);
 if(!q.length)return;
 const o=document.getElementById('sov');let i=0,tm=null;sov=true;
 const show=()=>{{const L=q[i];o.style.setProperty('--tc',L.c);
  o.innerHTML=`<div class="si">${{L.photo?`<img class="sp" src="${{L.photo}}" alt="">`:''}}<div><div class="sw">SOLD</div><div class="sn"></div><div class="st"><img src="img/l${{L.logo}}.png" alt=""><b></b></div><div class="spr">${{L.price}}</div></div></div><div class="sd">${{q.length>1?`${{i+1}} of ${{q.length}} · `:''}}Tap to ${{i<q.length-1?'see next':'close'}}</div>`;
  o.querySelector('.sn').textContent=L.name;o.querySelector('.st b').textContent=L.team;o.hidden=false;confetti([L.c,'#e8b931','#ffffff']);
  clearTimeout(tm);tm=setTimeout(next,q.length>1?3500:5000)}};
 const next=()=>{{i++;if(i<q.length)show();else{{clearTimeout(tm);o.hidden=true;sov=false}}}};
 o.onclick=next;show();
}})();
function confetti(cols){{const c=document.getElementById('cf'),x=c.getContext('2d');c.width=innerWidth;c.height=innerHeight;const ps=Array.from({{length:160}},()=>({{x:Math.random()*c.width,y:-20-Math.random()*c.height*.5,vx:(Math.random()-.5)*4,vy:2+Math.random()*4,r:Math.random()*6.28,s:6+Math.random()*6,col:cols[Math.floor(Math.random()*cols.length)]}}));let n=0;(function f(){{x.clearRect(0,0,c.width,c.height);ps.forEach(p=>{{p.x+=p.vx;p.y+=p.vy;p.vy+=.05;p.r+=.1;x.save();x.translate(p.x,p.y);x.rotate(p.r);x.fillStyle=p.col;x.fillRect(-p.s/2,-p.s/4,p.s,p.s/2);x.restore()}});if(++n<220)requestAnimationFrame(f);else x.clearRect(0,0,c.width,c.height)}})()}}
setInterval(()=>{{if(sov)return;const v=location.hash.slice(1)||'scoreboard';if((v==='scoreboard'||(v==='squads'&&!sqq.value))&&!document.hidden&&!document.querySelector('details[open]')){{try{{sessionStorage.setItem('y',scrollY)}}catch(e){{}}location.reload()}}}},15000);
</script></body></html>'''
open(out+'/index.html','w').write(page)
print('built',len(sales),'sales',len(page),'bytes')
