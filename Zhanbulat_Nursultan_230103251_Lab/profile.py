import json, os, platform, subprocess
from pathlib import Path

def ctl(k):
    try: return subprocess.check_output(['sysctl','-n',k],text=True,stderr=subprocess.DEVNULL).strip()
    except Exception: return None
p={'cpu_model':ctl('machdep.cpu.brand_string') or platform.processor() or platform.machine(),
   'physical_cores':int(ctl('hw.physicalcpu') or os.cpu_count() or 1),
   'logical_threads':int(ctl('hw.logicalcpu') or os.cpu_count() or 1),
   'cache_line_bytes':int(ctl('hw.cachelinesize') or 64),
   'os':platform.platform(),'kernel':platform.release(),
   'python':platform.python_version(),'python_implementation':platform.python_implementation()}
Path(__file__).resolve().parent.joinpath('results/host_profile.json').write_text(json.dumps(p,indent=2)+'\n')
print(json.dumps(p,indent=2))
