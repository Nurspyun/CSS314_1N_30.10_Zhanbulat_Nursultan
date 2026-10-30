import csv, json, math, multiprocessing as mp, statistics, time
from multiprocessing import shared_memory
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; _SHM=None; _ARR=None

def init_worker(name, shape):
 global _SHM,_ARR
 _SHM=shared_memory.SharedMemory(name=name); _ARR=np.ndarray(shape,dtype=np.float64,buffer=_SHM.buf)

def stencil_chunk(bounds):
 lo,hi=bounds; a=_ARR
 # Each process gets a disjoint row band of the five-point stencil.
 lo=max(1,lo); hi=min(a.shape[0]-1,hi)
 out=(a[lo-1:hi-1,1:-1]+a[lo+1:hi+1,1:-1]+a[lo:hi,0:-2]+a[lo:hi,2:]+a[lo:hi,1:-1])/5.0
 return float(out.sum()), int(out.size)

def run(n,p,seed):
 rng=np.random.default_rng(seed); a=np.ascontiguousarray(rng.random((n,n))); shm=shared_memory.SharedMemory(create=True,size=a.nbytes)
 try:
  np.ndarray(a.shape,dtype=a.dtype,buffer=shm.buf)[:]=a
  bounds=[(1+(n-2)*i//p,1+(n-2)*(i+1)//p) for i in range(p)]
  t=time.perf_counter()
  with mp.Pool(p,initializer=init_worker,initargs=(shm.name,a.shape)) as pool: parts=pool.map(stencil_chunk,bounds)
  elapsed=time.perf_counter()-t; return elapsed,sum(x for x,_ in parts),sum(y for _,y in parts)
 finally: shm.close(); shm.unlink()

def main():
 p=json.loads((ROOT/'results/salted_params.json').read_text()); n=p['N']; maxp=min(8,mp.cpu_count()); ps=[x for x in (1,2,4,8) if x<=maxp]; rows=[]; checks={}
 for workers in ps:
  vals=[run(n,workers,p['seed']) for _ in range(3)]; t=statistics.median(v[0] for v in vals); checks[workers]=vals[-1][1]
  rows.append({'study':'strong','processes':workers,'dimension':n,'median_seconds':t,'speedup':None,'efficiency_percent':None,'karp_flatt':None,'scaled_speedup':None,'checksum':checks[workers]})
 t1=rows[0]['median_seconds']
 for r in rows:
  P=r['processes']; S=t1/r['median_seconds']; r['speedup']=S; r['efficiency_percent']=100*S/P; r['karp_flatt']=None if P==1 else (1/S-1/P)/(1-1/P)
 # Least-squares fit constrained to the physical Amdahl range 0 <= s <= 1.
 observed=[r for r in rows if r['study']=='strong']
 candidates=[i/10000 for i in range(10001)]
 s_est=min(candidates,key=lambda s:sum((r['speedup']-1/(s+(1-s)/r['processes']))**2 for r in observed))
 fit_speedups={str(r['processes']):1/(s_est+(1-s_est)/r['processes']) for r in observed}
 for P in ps:
  dim=math.ceil(n*math.sqrt(P)); vals=[run(dim,P,p['seed']) for _ in range(3)]; tw=statistics.median(v[0] for v in vals); work_ratio=(dim*dim)/(n*n)
  rows.append({'study':'weak','processes':P,'dimension':dim,'median_seconds':tw,'speedup':None,'efficiency_percent':None,'karp_flatt':None,'scaled_speedup':P*t1/(work_ratio*tw),'checksum':vals[-1][1]})
 with (ROOT/'results/scaling_metrics.tsv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
 summary={'stencil':'5-point average stencil (4 additions + one division per output; 5 FLOPs/output)', 'arithmetic_intensity_flop_per_byte':5/48,'arithmetic_intensity':5/48,'regime':'memory-bound (expected for this low-intensity stencil; exact peak CPU FLOP/s unavailable)','memory_bytes_model':'5 input doubles + 1 output double per output (no cache reuse): 48 B/output; spatial reuse can reduce DRAM traffic', 'memory_bandwidth_peak_gb_s':100,'memory_bandwidth_source':'Apple MacBook Air M3 official technical specifications; host model reported as Apple M3, exact product variant not verified', 'amdahl_serial_fraction_estimate_constrained_least_squares':s_est,'amdahl_fit_speedups':fit_speedups,'amdahl_asymptotic_speedup':(1/s_est if s_est>0 else None),'classification':'Low arithmetic intensity suggests a memory-bandwidth-sensitive regime; a rigorous roofline bound needs peak CPU FLOP/s for this exact host configuration. Timings include process startup and shared-memory overhead.', 'strong_scaling_rows':[r for r in rows if r['study']=='strong'],'weak_scaling_rows':[r for r in rows if r['study']=='weak']}
 (ROOT/'results/roofline_summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print('scaling and roofline complete')
if __name__=='__main__': main()
