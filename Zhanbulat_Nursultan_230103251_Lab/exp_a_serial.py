#!/usr/bin/env python3
"""Experiment A: fixed serial delay plus process-parallel math work."""
import csv, math, multiprocessing as mp, statistics, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKERS = (1, 2, 4)
TOTAL_CHUNKS = 16
CHUNK_SIZE = 2_000_000
REPEATS = 3

def heavy_math(n):
    return sum(math.sin(i) * math.cos(i) for i in range(1, n))

def run_experiment(workers, total_chunks=TOTAL_CHUNKS, chunk_size=CHUNK_SIZE):
    t0 = time.perf_counter()
    time.sleep(0.40)  # deliberate serial section from the handout
    with mp.Pool(processes=workers) as pool:
        values = pool.map(heavy_math, [chunk_size] * total_chunks)
    return time.perf_counter() - t0, sum(values)

def main():
    rows=[]
    for p in WORKERS:
        observations=[run_experiment(p) for _ in range(REPEATS)]
        rows.append({'experiment':'A_serial_tail','workers':p,'repeats':REPEATS,
                     'runtime_s':statistics.median(x[0] for x in observations),
                     'checksum':observations[-1][1]})
    t1=rows[0]['runtime_s']
    for r in rows:
        p=r['workers']; r['speedup']=t1/r['runtime_s']
        r['karp_flatt']=None if p==1 else ((p*r['runtime_s']/t1)-1)/(p-1)
    with (ROOT/'results/exp_a.tsv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
    print('Experiment A (median seconds):', ', '.join(f"P={r['workers']} {r['runtime_s']:.4f}s" for r in rows))
if __name__=='__main__': main()
