# CS482 Variant B - Empirical Results

Student ID: **230103251**

Times include process/pool startup, IPC, computation and shutdown. Each configuration uses its own P=1 baseline. For repeated runs, the table uses the median.

S(p) = T1 / Tp; E(p) = S(p) / p * 100%; e(p) = (p * Tp / T1 - 1) / (p - 1), for p > 1.

| Configuration | Items | T1 (s) | T2 (s) | T4 (s) | T8 (s) | S8 | e(2) | e(8) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A: Micro (k=1) | 1000000 | 139.286032 | 151.442918 | 158.037546 | 78.398717 | 1.776637 | 1.174560 | 0.500413 |
| A: Coarse (k=10000) | 1000000 | - | - | - | 2.774480 | - | - | - |
| B: Queue | 400000 | 5.919803 | 12.353508 | 12.355324 | 12.356520 | 0.479083 | 3.173621 | 2.242651 |
| C: Buffered | 10000000 | 1.284308 | 0.814656 | 0.622122 | 0.552827 | 2.323166 | 0.268631 | 0.349082 |

## Environment and detailed results

### A: Micro (k=1)

- Date: 2026-10-30T15:22:05.053889+05:00
- OS: Windows-11-10.0.26200-SP0
- Python: 3.12.14
- Logical CPUs: 12; default pool count: 12
- Items: 1000000; repeats: 1
- Chunk/batch size: 1

| P | Time (s) | Speedup | Efficiency (%) | e(p) | Checksum |
|---:|---:|---:|---:|---:|---:|
| 1 | 139.286032 | 1.000000 | 100.00 | - | 131434424 |
| 2 | 151.442918 | 0.919726 | 45.99 | 1.174560 | 131434424 |
| 4 | 158.037546 | 0.881348 | 22.03 | 1.179501 | 131434424 |
| 8 | 78.398717 | 1.776637 | 22.21 | 0.500413 | 131434424 |

### A: Coarse (k=10000)

- Date: 2026-10-30T15:22:07.846015+05:00
- OS: Windows-11-10.0.26200-SP0
- Python: 3.12.14
- Logical CPUs: 12; default pool count: 12
- Items: 1000000; repeats: 1
- Chunk/batch size: 10000

| P | Time (s) | Speedup | Efficiency (%) | e(p) | Checksum |
|---:|---:|---:|---:|---:|---:|
| 8 | 2.774480 | - | - | - | 131434424 |

### B: Queue

- Date: 2026-10-30T15:22:58.131931+05:00
- OS: Windows-11-10.0.26200-SP0
- Python: 3.12.14
- Logical CPUs: 12; default pool count: 12
- Items: 400000; repeats: 1
- Chunk/batch size: one item per message

| P | Time (s) | Speedup | Efficiency (%) | e(p) | Checksum |
|---:|---:|---:|---:|---:|---:|
| 1 | 5.919803 | 1.000000 | 100.00 | - | 1199997 |
| 2 | 12.353508 | 0.479200 | 23.96 | 3.173621 | 1199997 |
| 4 | 12.355324 | 0.479130 | 11.98 | 2.449490 | 1199997 |
| 8 | 12.356520 | 0.479083 | 5.99 | 2.242651 | 1199997 |

### C: Buffered

- Date: 2026-10-30T15:23:02.359838+05:00
- OS: Windows-11-10.0.26200-SP0
- Python: 3.12.14
- Logical CPUs: 12; default pool count: 12
- Items: 10000000; repeats: 1
- Chunk/batch size: 10000

| P | Time (s) | Speedup | Efficiency (%) | e(p) | Checksum |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.284308 | 1.000000 | 100.00 | - | 29999994 |
| 2 | 0.814656 | 1.576503 | 78.83 | 0.268631 | 29999994 |
| 4 | 0.622122 | 2.064397 | 51.61 | 0.312537 | 29999994 |
| 8 | 0.552827 | 2.323166 | 29.04 | 0.349082 | 29999994 |

## Measurement provenance and scope

- New runs used Windows 11, Python 3.12.14, and a machine reporting 12 logical CPUs.
- A micro P=1,2,4 measurements were retained from the student's console output, as requested. P=8 was measured later by the agent on the same computer. Different execution conditions can affect comparability.
- Only P=8 was newly measured for both A configurations. No coarse P=1,2,4 timings were available, so their cells remain empty. Coarse speedup and Karp-Flatt metrics cannot be calculated without its own T1.
- B and C were measured sequentially for P=1,2,4,8. Benchmark workloads were not run concurrently.
- Each completed case has one sample, so no variability estimate is available. Timestamps shown above refer to result saving; the retained A measurements were taken earlier.
- Timings include process/pool startup, computation, IPC and shutdown. A also includes checksum summation. Its P=1 baseline uses Pool(1), as in the handout.

## Interpretation

### Experiment A: granularity

At P=8, micro tasks took 78.398717 s, while coarse chunks took 2.774480 s. Coarse chunks were **28.26 times faster** for the same workload and worker count. All completed A checksums were 131434424.

Fine tasks require frequent dispatch, serialization and IPC operations. Coarse chunks amortize those costs over many items. The observed difference supports the importance of task granularity, although timings alone cannot isolate a specific runtime bottleneck.

Using the retained micro baseline, S8 = 1.776637, E8 = 22.21%, and e(8) = 0.500413. The earlier P=2 and P=4 runs were slower than P=1. The later P=8 result improves; e(p) is not monotonic across the combined runs. Interpret this comparison cautiously because P=8 was measured in a later session.

Coarse S8 and e(p) remain unavailable. Substituting the micro baseline for the coarse baseline would be incorrect.

### Experiment B: shared queue

Runtime increased from 5.919803 s at P=1 to 12.356520 s at P=8, a **2.09-fold slowdown**. S8 = 0.479083 and E8 = 5.99%. This is negative scaling. P=2,4,8 timings are almost equal; their tiny differences should not be interpreted as a robust trend from one sample.

Karp-Flatt e(2) = 3.173621, e(4) = 2.449490, and e(8) = 2.242651. All exceed 1, but they decrease with P. The handout's expected rising e(p) trajectory was not reproduced.

Per-record queue traffic is consistent with substantial IPC and synchronization overhead. These measurements alone do not prove a particular OS lock or hardware coherence mechanism. All B checksums were 1199997.

### Experiment C: local buffer aggregation

For 10000000 items and batch_size=10000, runtime fell from 1.284308 s at P=1 to 0.552827 s at P=8. S8 = 2.323166, E8 = 29.04%, and e(8) = 0.349082. All C checksums were 29999994.

| Requested target | Measured | Outcome |
|---|---:|---|
| S8 > 5.0 | 2.323166 | Not reached |
| e(8) <= 0.05 | 0.349082 | Not reached |

Buffering reduces queue traffic by sending locally aggregated sums. It improves performance, but scaling remains sublinear. Process startup, synchronization and the short compute duration are plausible contributors; these measurements do not isolate their individual costs.

### Throughput comparison at P=8

B and C have different item counts. Throughput provides the workload-normalized comparison:

| Configuration | Items | Time (s) | Throughput (items/s) |
|---|---:|---:|---:|
| B | 400000 | 12.356520 | 32371.57 |
| C | 10000000 | 0.552827 | 18088857.90 |

C processed 25 times as many items in 22.35 times less wall-clock time. Its throughput was **558.79 times higher** at P=8. This compares the complete pipelines: B receives each record, whereas C receives aggregated sums.

## Remaining gap

All values are measured or calculated from measured times. No example values from the handout were substituted. A coarse P=1,2,4 measurements remain missing because only P=8 was requested. Completing the full handout matrix requires those three additional measurements.

Raw samples, settings, timestamps and provenance of retained A rows are recorded in measurements.json.
