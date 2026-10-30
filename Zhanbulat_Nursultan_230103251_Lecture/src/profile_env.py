import argparse, json, os, platform, subprocess, sys
from pathlib import Path
from salt import get_student_params
ROOT = Path(__file__).resolve().parents[1]

def sysctl(key):
    try: return subprocess.check_output(['sysctl','-n',key], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception: return None

def profile():
    arm = platform.machine().lower() in ('arm64','aarch64')
    cpu = sysctl('machdep.cpu.brand_string') or platform.processor() or 'Unknown'
    return {'cpu_model': cpu, 'microarchitecture': 'Apple M3 (ARMv8.6-A family; exact core mix not exposed via portable API)' if 'Apple M3' in cpu else platform.machine(),
      'base_frequency_hz': None, 'frequency_note': 'macOS does not expose a stable base frequency for Apple Silicon via sysctl',
      'physical_cores': int(sysctl('hw.physicalcpu') or os.cpu_count() or 1), 'logical_threads': int(sysctl('hw.logicalcpu') or os.cpu_count() or 1),
      'smt': int(sysctl('hw.logicalcpu') or 0) > int(sysctl('hw.physicalcpu') or 0),
      'cache_bytes': {'L1_data':int(sysctl('hw.l1dcachesize') or 0) or None,'L2':int(sysctl('hw.l2cachesize') or 0) or None,'L3':int(sysctl('hw.l3cachesize') or 0) or None},
      'cache_line_bytes': int(sysctl('hw.cachelinesize') or 64), 'os':platform.platform(), 'kernel':platform.release(),
      'python':{'version':sys.version,'implementation':platform.python_implementation(),'executable':sys.executable}}

if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--student-id',required=True); a=ap.parse_args()
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/host_profile.json').write_text(json.dumps(profile(),indent=2)+'\n')
    (ROOT/'results/salted_params.json').write_text(json.dumps(get_student_params(a.student_id),indent=2)+'\n')
    print(json.dumps(profile(),indent=2))
