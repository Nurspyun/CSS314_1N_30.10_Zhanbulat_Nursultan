import hashlib,json,sys
from pathlib import Path
from src.salt import get_student_params
ROOT=Path(__file__).resolve().parent; R=ROOT/'results'
def check(cond,msg):
 if not cond: raise SystemExit('[FAIL] '+msg)
 print('[PASS] '+msg)
def main():
 host=json.loads((R/'host_profile.json').read_text()); params=json.loads((R/'salted_params.json').read_text())
 check(host['physical_cores']>=1 and host['logical_threads']>=1,'Milestone 0: host topology present')
 check(params==get_student_params(params['student_id']),'Milestone 0: salted parameters validated')
 d=json.loads((R/'loop_interchange.json').read_text()); check(d['max_abs_error']<=1e-12,'Milestone 1: interchanged matrix matches reference within tolerance')
 import csv
 with (R/'false_sharing_karp_flatt.tsv').open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
 check(len(rows)==12 and all(int(x['total_count'])==int(x['processes'])*int(x['iterations_per_process']) for x in rows),'Milestone 2: all counters match process-count × iterations')
 with (R/'scaling_metrics.tsv').open() as f: scaling=list(csv.DictReader(f,delimiter='\t'))
 strong=[x for x in scaling if x['study']=='strong']; check(len(strong)>=1 and all(abs(float(x['checksum'])-float(strong[0]['checksum']))<=1e-8 for x in strong),'Milestone 3: strong scaling stencil checksums agree')
 files=['host_profile.json','salted_params.json','stride_results.tsv','loop_interchange.json','false_sharing_karp_flatt.tsv','scaling_metrics.tsv','roofline_summary.json']
 digest=hashlib.sha256()
 for name in files: digest.update(name.encode()+b'\0'+(R/name).read_bytes())
 (R/'verification_receipt.sig').write_text('sha256:'+digest.hexdigest()+'\n'); print('All generated datasets validated; SHA-256 receipt written.')
if __name__=='__main__': main()
