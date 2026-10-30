#!/usr/bin/env python3
"""Experiment B: one shared counter protected by a multiprocessing lock."""
import csv, multiprocessing as mp, statistics, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
WORKERS=(1,2,4); TOTAL_INCREMENTS=2_000_000; REPEATS=5

def contended_worker(shared_counter, lock, iterations):
    for _ in range(iterations):
        with lock:
            shared_counter.value += 1

def run_contended(p,total_increments=TOTAL_INCREMENTS):
    increments_per_worker=total_increments//p
    counter=mp.Value('i',0); lock=mp.Lock()
    procs=[mp.Process(target=contended_worker,args=(counter,lock,increments_per_worker)) for _ in range(p)]
    t0=time.perf_counter()
    for proc in procs: proc.start()
    for proc in procs: proc.join()
    elapsed=time.perf_counter()-t0
    if any(proc.exitcode != 0 for proc in procs): raise RuntimeError('worker process failed')
    if counter.value != total_increments: raise AssertionError(f'{counter.value} != {total_increments}')
    return elapsed,counter.value

def main():
    rows=[]
    for p in WORKERS:
        observations=[run_contended(p) for _ in range(REPEATS)]
        rows.append({'experiment':'B_lock_contention','workers':p,'repeats':REPEATS,
                     'total_increments':observations[-1][1],
                     'runtime_s':statistics.median(x[0] for x in observations)})
    t1=rows[0]['runtime_s']
    for r in rows:
        p=r['workers']; r['speedup']=t1/r['runtime_s']
        r['karp_flatt']=None if p==1 else ((p*r['runtime_s']/t1)-1)/(p-1)
    with (ROOT/'results/exp_b.tsv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
    print('Experiment B (median seconds):', ', '.join(f"P={r['workers']} {r['runtime_s']:.4f}s" for r in rows))
if __name__=='__main__': main()
