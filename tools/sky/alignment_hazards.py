"""Planetary alignments vs earthquakes and volcanic eruptions, 1965-2016 (+ eruption replication 1900-1964).
Catalogs (public mirrors, fetched by this script into tools/sky/cache/):
  USGS ComCat M5.5+ 1965-2016 (plotly/datasets earthquakes-23k.csv); declustered with Gardner-Knopoff windows.
  Smithsonian GVP VOTW confirmed eruptions with day-precision start dates (rfordatascience/tidytuesday 2020-05-12, to Apr 2020).
Alignments (PyEphem, daily 00 UTC): Mercury/Venus inferior conjunctions, retrograde days, double inferior conjunction
(Mercury and Venus within 20 d), heliocentric Sun-Mercury-Venus-Earth line-up (<=15 deg), 5+ of Me..Sa incl. Earth in 60 deg.
Test: hazards falling in +-7/+-15 d windows (or on retrograde days) vs 5,000 circular time shifts of the hazard dates,
one-sided p, Benjamini-Hochberg q over all tests. Writes data/alignment_tests.csv and data/alignment_calendar.csv.
Run: python3 tools/sky/alignment_hazards.py
"""
import os, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; C=ROOT/'tools'/'sky'/'cache'; C.mkdir(exist_ok=True)
for fn,u in [('earthquakes-23k.csv','https://raw.githubusercontent.com/plotly/datasets/master/earthquakes-23k.csv'),
             ('eruptions.csv','https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-05-12/eruptions.csv')]:
    if not (C/fn).exists(): urllib.request.urlretrieve(u,C/fn)
import ephem, math, csv, json, datetime as dt, numpy as np
rng=np.random.default_rng(42)
T0=dt.date(1965,1,1); T1=dt.date(2016,12,31); N=(T1-T0).days+1
def day(d): return (d-T0).days
# ---- ephemeris, daily 00 UTC
geo={}; helio={}
bodies={'Mercury':ephem.Mercury,'Venus':ephem.Venus}
lon={k:np.zeros(N) for k in bodies}; dist={k:np.zeros(N) for k in bodies}; sun=np.zeros(N)
hl={k:np.zeros(N) for k in ['Mercury','Venus','Mars','Jupiter','Saturn']}
for i in range(N):
    d=ephem.Date(T0+dt.timedelta(i)); s=ephem.Sun(d); sun[i]=ephem.Ecliptic(s).lon
    for k,B in bodies.items():
        b=B(d); lon[k][i]=ephem.Ecliptic(b).lon; dist[k][i]=b.earth_distance
    for k in hl:
        b=getattr(ephem,k)(d); hl[k][i]=b.hlon
earth_h=(sun+math.pi)%(2*math.pi)
wrap=lambda x:(x+math.pi)%(2*math.pi)-math.pi
events={}
for k in bodies:
    dl=wrap(np.diff(lon[k])); retro=np.r_[dl<0,dl[-1]<0]; events[f'{k} retrograde (days)']=retro
    el=wrap(lon[k]-sun); sgn=np.sign(el); ic=[i for i in range(1,N) if sgn[i]!=sgn[i-1] and dist[k][i]<1]
    events[f'{k} inferior conjunction']=np.array(ic)
mic=events['Mercury inferior conjunction']; vic=events['Venus inferior conjunction']
events['Double inferior conjunction (Mercury and Venus within 20 d)']=np.array([v for v in vic if np.min(abs(mic-v))<=20])
events['Both retrograde (days)']=events['Mercury retrograde (days)']&events['Venus retrograde (days)']
# heliocentric line-up: Mercury, Venus, Earth within 15 deg heliocentric longitude, mid-day of each run
spread=np.array([np.ptp(np.unwrap(np.array([hl['Mercury'][i],hl['Venus'][i],earth_h[i]])-earth_h[i])) for i in range(N)])
spread=np.degrees(np.abs(np.array([max(abs(wrap(hl['Mercury'][i]-earth_h[i])),abs(wrap(hl['Venus'][i]-earth_h[i])),abs(wrap(hl['Mercury'][i]-hl['Venus'][i]))) for i in range(N)])))
runs=[];i=0
while i<N:
    if spread[i]<=15:
        j=i
        while j+1<N and spread[j+1]<=15: j+=1
        runs.append(i+int(np.argmin(spread[i:j+1]))); i=j+1
    else: i+=1
events['Sun–Mercury–Venus–Earth line-up (heliocentric ≤15°)']=np.array(runs)
# 5+ of Me,Ve,Ea,Ma,Ju,Sa within a 60° heliocentric sector
def cluster(i):
    L=np.sort(np.array([hl[k][i] for k in hl]+[earth_h[i]])%(2*math.pi)); g=np.diff(np.r_[L,L[0]+2*math.pi]); 
    best=0
    for a in range(6):
        best=max(best,sum(((L-L[a])%(2*math.pi))<=math.radians(60)))
    return best
cl=np.array([cluster(i) for i in range(0,N)])
runs=[];i=0
while i<N:
    if cl[i]>=5:
        j=i
        while j+1<N and cl[j+1]>=5: j+=1
        runs.append((i+j)//2); i=j+1
    else: i+=1
events['5+ planets (Me–Sa incl. Earth) within 60° heliocentric']=np.array(runs)
# ---- catalogs
Q=[]
for r in csv.DictReader(open(C/'earthquakes-23k.csv')):
    m,d_,y=r['Date'].split('/') if '/' in r['Date'] else (None,None,None)
    if not y: continue
    Q.append((dt.date(int(y),int(m),int(d_)),float(r['Latitude']),float(r['Longitude']),float(r['Magnitude'])))
Q.sort()
def gk(m): return 10**(0.032*m+2.7389) if m>=6.5 else 10**(0.5409*m-0.547), 10**(0.1238*m+0.983)  # (days, km) Gardner-Knopoff
def hav(a,b,c,d):
    a,b,c,d=map(math.radians,(a,b,c,d)); return 6371*2*math.asin(math.sqrt(math.sin((c-a)/2)**2+math.cos(a)*math.cos(c)*math.sin((d-b)/2)**2))
idx=sorted(range(len(Q)),key=lambda k:-Q[k][3]); dep=set()
for k in idx:
    if k in dep: continue
    t,km=gk(Q[k][3])
    for j in range(len(Q)):
        if j!=k and j not in dep and 0<=(Q[j][0]-Q[k][0]).days<=t and Q[j][3]<=Q[k][3] and hav(Q[k][1],Q[k][2],Q[j][1],Q[j][2])<=km: dep.add(j)
main=[q for k,q in enumerate(Q) if k not in dep]
E=[]
for r in csv.DictReader(open(C/'eruptions.csv')):
    if r['eruption_category']!='Confirmed Eruption': continue
    try: d=dt.date(int(r['start_year']),int(r['start_month']),int(r['start_day']))
    except: continue
    if T0<=d<=T1: E.append((d,r['vei']))
sets={'M6+ mainshocks':[day(q[0]) for q in main if q[3]>=6 and T0<=q[0]<=T1],
      'M7+ mainshocks':[day(q[0]) for q in main if q[3]>=7 and T0<=q[0]<=T1],
      'M7.5+ mainshocks':[day(q[0]) for q in main if q[3]>=7.5 and T0<=q[0]<=T1],
      'Eruption starts, VEI 2+':[day(d) for d,v in E if v not in ('NA','') and float(v)>=2],
      'Eruption starts, VEI 3+':[day(d) for d,v in E if v not in ('NA','') and float(v)>=3]}
def mask_from(ev,w):
    if ev.dtype==bool: return ev
    m=np.zeros(N,bool)
    for e in ev: m[max(0,e-w):e+w+1]=True
    return m
rows=[]; P=5000
for en,ev in events.items():
    for w in ([None] if ev.dtype==bool else [7,15]):
        m=mask_from(ev,w); frac=m.mean()
        for sn,s in sets.items():
            s=np.array(s); obs=m[s].sum(); exp=frac*len(s)
            null=np.array([m[(s+o)%N].sum() for o in rng.integers(1,N,P)])
            p=(1+np.sum(null>=obs))/(P+1); ratio=obs/null.mean()
            rows.append(dict(alignment=en,window='' if w is None else f'±{w} d',n_alignments=int(len(ev)) if ev.dtype!=bool else '',time_share=round(frac*100,1),hazard=sn,n=len(s),observed=int(obs),expected=round(float(null.mean()),1),ratio=round(float(ratio),2),p_value=round(float(p),3)))
print('mainshocks',len(main),'of',len(Q),'eruptions',len(E))
for r in rows: print(f"{r['alignment'][:45]:45s} {r['window']:6s} {r['hazard']:24s} n={r['n']:5d} obs={r['observed']:5d} exp={r['expected']:7.1f} ratio={r['ratio']:.2f} p={r['p_value']}")

pv=np.array([r['p_value'] for r in rows]); n=len(pv); o=np.argsort(pv)
q=np.empty(n); q[o]=np.minimum.accumulate((pv[o]*n/np.arange(1,n+1))[::-1])[::-1]
for r,qq in zip(rows,q):
    r['q_fdr']=round(float(min(qq,1)),2)
    r['verdict']='Real finding' if qq<0.1 else ('Nominal only (fails correction)' if r['p_value']<0.05 else 'No effect')
rows.sort(key=lambda r:r['p_value'])
with open(ROOT/'data'/'alignment_tests.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=['rank']+list(rows[0].keys())); w.writeheader()
    for i,r in enumerate(rows,1): w.writerow({'rank':i,**r})
# calendar 2025-2027
# event lies between 00 UTC of day i-1 and day i; it is dated to day i-1 (UTC)
cal=[]; d0=dt.date(2025,1,1); prev={}
for i in range((dt.date(2027,12,31)-d0).days):
    d=ephem.Date(d0+dt.timedelta(i)); s_=ephem.Ecliptic(ephem.Sun(d)).lon
    for k,B in bodies.items():
        b=B(d); L=ephem.Ecliptic(b).lon; e=wrap(L-s_)
        if k in prev:
            pL,pe,pdl=prev[k]; dl=wrap(L-pL)
            if pdl is not None and (dl<0)!=(pdl<0): cal.append((str(d0+dt.timedelta(i-1)),f'{k} turns {"retrograde" if dl<0 else "direct"}','station'))
            if np.sign(e)!=np.sign(pe): cal.append((str(d0+dt.timedelta(i-1)),f'{k} {"inferior" if b.earth_distance<1 else "superior"} conjunction with the Sun' + (f' ({b.earth_distance:.2f} AU from Earth)' if b.earth_distance<1 else ''),'conjunction'))
            prev[k]=(L,e,dl)
        else: prev[k]=(L,e,None)
cal.sort()
with open(ROOT/'data'/'alignment_calendar.csv','w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['date','event','kind']); w.writerows(cal)
print('wrote alignment_tests.csv',len(rows),'and alignment_calendar.csv',len(cal))
