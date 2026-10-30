# Empirical Scalability Diagnostics — Karp–Flatt

**Student ID:** `230103251`  
**Branch:** `practice-230103251`  
**Measurement host:** Apple M3, 8 physical / 8 logical cores, macOS-15.2-arm64-arm-64bit-Mach-O, Python 3.13.2

All runtimes are medians of three measured runs, except Experiment B, which uses five because lock-contention timing varied noticeably. The measurements include multiprocessing pool/process startup because the handout starts its timer before creating the pool/processes. These same-host measurements are reused from the earlier run of this lab; this exercise has no ID-salted workload, so changing the student ID does not change the benchmark inputs or code.

| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Diagnosis |
|---|---:|---:|---:|---:|---:|---|
| A: Stubborn serial tail | 2.7019 | 1.6103 | 1.0997 | 0.192 | 0.209 | e is nearly flat (e4/e2 = 1.09), consistent with a fixed serial/dispatch fraction; measured e is above the handout’s nominal 0.10–0.14 range. |
| B: Lock contention | 3.6505 | 9.2032 | 9.7437 | 4.042 | 3.226 | T4 > T1 and e(4) > e(2), showing lock contention; speedup remains below 1 at P=2 and P=4. |
| C: Privatized counter | 0.3784 | 0.2072 | 0.1294 | 0.095 | 0.123 | Privatization restores scaling: T4 < T1 and 4-worker efficiency is 73.1%; e remains above the handout’s ≤0.03 target, likely reflecting process startup/dispatch overhead. |

## Interpretation

The two contention measurements separate the mechanisms. Experiment A has approximately stable Karp–Flatt values across worker counts, while Experiment B’s values are several times larger and increase at P=4 as workers serialize on one mutex-protected counter. Experiment C removes shared writes from the inner loop; it recovers 73.1% parallel efficiency at four workers. The empirical C metric does not reach 0.03 on this macOS/Python process setup, so the report records the measured value rather than the handout’s expected value.

## Reproduction

Run from this directory: `python3 profile.py`, `python3 exp_a_serial.py`, `python3 exp_b_contention.py`, `python3 exp_c_fixed.py`. Each benchmark writes its tab-separated raw measurements under `results/`.
