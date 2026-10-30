import ctypes, json, statistics, subprocess, tempfile, time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
C_SRC=r'''#include <stddef.h>
void mm_ijk(const double*A,const double*B,double*C,int n){for(int i=0;i<n;i++)for(int j=0;j<n;j++){double x=C[(size_t)i*n+j];for(int k=0;k<n;k++)x+=A[(size_t)i*n+k]*B[(size_t)k*n+j];C[(size_t)i*n+j]=x;}}
void mm_ikj(const double*A,const double*B,double*C,int n){for(int i=0;i<n;i++)for(int k=0;k<n;k++){double x=A[(size_t)i*n+k];for(int j=0;j<n;j++)C[(size_t)i*n+j]+=x*B[(size_t)k*n+j];}}
'''
def main():
 p=json.loads((ROOT/'results/salted_params.json').read_text()); n=p['N']//2; rng=np.random.default_rng(p['seed']); A=np.ascontiguousarray(rng.random((n,n))); B=np.ascontiguousarray(rng.random((n,n)))
 with tempfile.TemporaryDirectory() as d:
  c=Path(d)/'mm.c'; so=Path(d)/'mm.so'; c.write_text(C_SRC); subprocess.run(['clang','-O3','-shared','-fPIC',str(c),'-o',str(so)],check=True)
  lib=ctypes.CDLL(str(so)); ptr=ctypes.POINTER(ctypes.c_double); lib.mm_ijk.argtypes=lib.mm_ikj.argtypes=[ptr,ptr,ptr,ctypes.c_int]
  def run(name):
   fn=getattr(lib,name); times=[]; out=None
   for _ in range(3):
    out=np.zeros((n,n)); t=time.perf_counter(); fn(A.ctypes.data_as(ptr),B.ctypes.data_as(ptr),out.ctypes.data_as(ptr),n); times.append(time.perf_counter()-t)
   return statistics.median(times),out
  t1,c1=run('mm_ijk'); t2,c2=run('mm_ikj'); err=float(np.max(np.abs(c1-c2)))
  data={'dimension':n,'compiler':'clang -O3 (native C loops called by Python/ctypes)','naive_ijk_median_seconds':t1,'interchanged_ikj_median_seconds':t2,'naive_time_s':t1,'interchanged_time_s':t2,'speedup':t1/t2,'max_abs_error':err,'reference_checksum':float(c1.sum()),'optimized_checksum':float(c2.sum()),'tolerance':1e-12}
  (ROOT/'results/loop_interchange.json').write_text(json.dumps(data,indent=2)+'\n'); print(json.dumps(data,indent=2))
if __name__=='__main__': main()
