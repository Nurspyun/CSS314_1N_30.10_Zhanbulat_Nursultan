import csv, ctypes, json, multiprocessing as mp, statistics, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; K=5_000_000
PROFILE=json.loads((ROOT/'results/host_profile.json').read_text())
PAD_SLOTS=max(8, PROFILE['cache_line_bytes']//ctypes.sizeof(ctypes.c_int64))

def worker(arr, idx, iters, mode, lock):
 if mode=='local':
  x=0
  for _ in range(iters): x+=1
  with lock: arr[idx]=x
 else:
  slot=idx*PAD_SLOTS if mode=='padded' else idx
  for _ in range(iters): arr[slot]+=1

def measure(p, mode):
 size=max(PAD_SLOTS,p*PAD_SLOTS); arr=mp.Array(ctypes.c_int64,size,lock=False); lock=mp.Lock(); ps=[]
 t=time.perf_counter()
 for i in range(p):
  q=mp.Process(target=worker,args=(arr,i,K,mode,lock)); q.start(); ps.append(q)
 for q in ps: q.join()
 elapsed=time.perf_counter()-t
 if any(q.exitcode for q in ps): raise RuntimeError('worker process failed')
 indexes=[i*PAD_SLOTS if mode=='padded' else i for i in range(p)]
 return elapsed,sum(arr[i] for i in indexes)

def main():
 rows=[]
 for mode in ('unpadded','padded','local'):
  for p in (1,2,4,8):
   times=[]; count=None
   for _ in range(3):
    t,count=measure(p,mode); times.append(t)
   rows.append({'mode':mode,'processes':p,'iterations_per_process':K,'padding_bytes':PAD_SLOTS*ctypes.sizeof(ctypes.c_int64) if mode=='padded' else 0,'median_seconds':statistics.median(times),'total_count':count})
 baselines={m:next(r['median_seconds'] for r in rows if r['mode']==m and r['processes']==1) for m in ('unpadded','padded','local')}
 for r in rows:
  r['karp_flatt']=None if r['processes']==1 else ((r['processes']*r['median_seconds']/baselines[r['mode']])-1)/(r['processes']-1)
 with (ROOT/'results/false_sharing_karp_flatt.tsv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
 print('false-sharing benchmark complete')
if __name__=='__main__': main()
