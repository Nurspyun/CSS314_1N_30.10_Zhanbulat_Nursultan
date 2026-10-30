import csv, json, statistics, time
from pathlib import Path
import numpy as np
from salt import get_student_params
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=json.loads((ROOT/'results/salted_params.json').read_text()); n=p['buffer_elements']
 a=np.ones(n,dtype=np.float64); rows=[]
 for s in (1,2,4,8,16,32,64,128):
  view=a[::s]
  for _ in range(5): float(np.sum(view))
  ts=[]
  for _ in range(5):
   t=time.perf_counter_ns(); total=float(np.sum(view)); ts.append(time.perf_counter_ns()-t)
  med=statistics.median(ts); rows.append((s,len(view),med,med/len(view),total))
 with (ROOT/'results/stride_results.tsv').open('w') as f:
  w=csv.writer(f,delimiter='\t'); w.writerow(['stride','elements_touched','median_time_ns','ns_per_element','latency_ns','checksum']); w.writerows([(a,b,c,d,d,e) for a,b,c,d,e in rows])
 print('stride benchmark complete')
if __name__=='__main__': main()
