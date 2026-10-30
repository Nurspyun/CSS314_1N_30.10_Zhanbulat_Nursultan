#!/usr/bin/env python3
"""Experiment C: local per-worker counting, one final reduction."""
import csv, multiprocessing as mp, statistics, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WORKERS=(1,2,4); TOTAL_INCREMENTS=20_000_000; REPEATS=3

def private_worker(iterations):
    local_sum=0
    for _ in range(iterations): local_sum+=1
    return local_sum

def run_privatized(p,total_increments=TOTAL_INCREMENTS):
    increments_per_worker=total_increments//p
    tasks=[increments_per_worker]*p
    t0=time.perf_counter()
    with mp.Pool(processes=p) as pool: results=pool.map(private_worker,tasks)
    total=sum(results); elapsed=time.perf_counter()-t0
    if total != total_increments: raise AssertionError(f'{total} != {total_increments}')
    return elapsed,total

def main():
    rows=[]
    for p in WORKERS:
        observations=[run_privatized(p) for _ in range(REPEATS)]
        rows.append({'experiment':'C_privatized','workers':p,'repeats':REPEATS,
                     'total_increments':observations[-1][1],
                     'runtime_s':statistics.median(x[0] for x in observations)})
    t1=rows[0]['runtime_s']
    for r in rows:
        p=r['workers']; r['speedup']=t1/r['runtime_s']
        r['karp_flatt']=None if p==1 else ((p*r['runtime_s']/t1)-1)/(p-1)
    with (ROOT/'results/exp_c.tsv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
    print('Experiment C (median seconds):', ', '.join(f"P={r['workers']} {r['runtime_s']:.4f}s" for r in rows))
if __name__=='__main__': main()
