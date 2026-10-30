"""Measurement, validation, and report helpers for CS482 Variant B."""
import argparse
import json
import multiprocessing as mp
import os
import platform
import statistics
from datetime import datetime
from pathlib import Path


def arguments(description, items, batch=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--items', type=int, default=items)
    parser.add_argument('--workers', nargs='+', type=int, default=[1, 2, 4, 8])
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--resume', action='store_true', help='Reuse completed worker counts from a checkpoint')
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).parent)
    if batch:
        parser.add_argument('--batch-size', type=int, default=10_000)
    args = parser.parse_args()
    if args.items < 1 or args.repeats < 1 or any(p < 1 for p in args.workers):
        parser.error('items, repeats and workers must be positive')
    if 1 not in args.workers:
        parser.error('--workers must include 1 for the baseline')
    if batch and args.batch_size < 1:
        parser.error('batch-size must be positive')
    args.workers = sorted(set(args.workers))
    return args


def partitions(n, p):
    """Cover [0, n) exactly, including a remainder when n is not divisible by p."""
    base, extra = divmod(n, p)
    start = 0
    for i in range(p):
        stop = start + base + (i < extra)
        yield start, stop
        start = stop


def expected_sum(n):
    full, remainder = divmod(n, 7)
    return full * 21 + remainder * (remainder - 1) // 2


def measure(run, args, key=None, **settings):
    rows = []
    reference = None
    checkpoint = args.output_dir / f'checkpoint_{key}.json' if key else None
    signature = {'items': args.items, 'repeats': args.repeats, **settings}
    cached = {}
    if args.resume and checkpoint and checkpoint.exists():
        saved = json.loads(checkpoint.read_text(encoding='utf-8'))
        if saved['signature'] != signature:
            raise ValueError('Checkpoint settings differ. Use the same settings or omit --resume.')
        cached = {row['p']: row for row in saved['rows']}
    for p in args.workers:
        if p in cached:
            row = cached[p]
            if reference is None:
                reference = row['checksum']
            if row['checksum'] != reference:
                raise RuntimeError('Checkpoint checksums differ')
            rows.append(row)
            print(f"P={p}: restored {row['seconds']:.6f}s from checkpoint", flush=True)
            continue
        samples = []
        for repeat in range(args.repeats):
            seconds, checksum = run(p)
            if reference is None:
                reference = checksum
            if checksum != reference:
                raise RuntimeError(f'Checksum mismatch at P={p}: {checksum} != {reference}')
            samples.append(seconds)
            print(f'P={p} repeat={repeat + 1}: {seconds:.6f}s; checksum={checksum}', flush=True)
        rows.append({'p': p, 'seconds': statistics.median(samples),
                     'samples': samples, 'checksum': reference})
        if checkpoint:
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            # Preserve cached counts omitted from this invocation.
            completed = dict(cached)
            completed.update({row['p']: row for row in rows})
            temporary = checkpoint.with_suffix('.tmp')
            temporary.write_text(json.dumps({'signature': signature,
                                            'rows': list(completed.values())}, indent=2), encoding='utf-8')
            temporary.replace(checkpoint)
    t1 = next(row['seconds'] for row in rows if row['p'] == 1)
    print('\nP | Time(s) | Speedup | Efficiency(%) | Karp-Flatt')
    for row in rows:
        p, tp = row['p'], row['seconds']
        row['speedup'] = t1 / tp
        row['efficiency_pct'] = row['speedup'] / p * 100
        row['karp_flatt'] = None if p == 1 else (p * tp / t1 - 1) / (p - 1)
        metric = '-' if p == 1 else f"{row['karp_flatt']:.6f}"
        print(f"{p} | {tp:.6f} | {row['speedup']:.4f} | {row['efficiency_pct']:.2f} | {metric}")
    return rows


def save_results(key, rows, args, **settings):
    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / 'measurements.json'
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    data[key] = {
        'timestamp': datetime.now().astimezone().isoformat(),
        'platform': platform.platform(), 'python': platform.python_version(),
        'cpu_count': os.cpu_count(), 'pool_cpu_count': mp.cpu_count(),
        'items': args.items, 'repeats': args.repeats, **settings, 'rows': rows,
    }
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    write_report(data, args.output_dir)
    print(f'\nSaved: {path} and {args.output_dir / "RESULTS_B.md"}', flush=True)


def write_report(data, directory):
    lines = ['# CS482 Variant B - Empirical Results', '',
             'Student ID: **230103251**', '',
             'Times include process/pool startup, IPC, computation and shutdown. '
             'Each configuration uses its own P=1 baseline. '
             'For repeated runs, the table uses the median.', '',
             'S(p) = T1 / Tp; E(p) = S(p) / p * 100%; '
             'e(p) = (p * Tp / T1 - 1) / (p - 1), for p > 1.', '',
             '| Configuration | Items | T1 (s) | T2 (s) | T4 (s) | T8 (s) | S8 | e(2) | e(8) |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    labels = {'a_micro': 'A: Micro (k=1)', 'a_coarse': 'A: Coarse (k=10000)',
              'b_queue': 'B: Queue', 'c_buffered': 'C: Buffered'}
    for key, label in labels.items():
        config = data.get(key)
        if not config:
            lines.append(f'| {label} | pending | - | - | - | - | - | - | - |')
            continue
        rows = {r['p']: r for r in config['rows']}
        def value(p, field):
            v = rows.get(p, {}).get(field)
            return '-' if v is None else f'{v:.6f}'
        values = [value(p, 'seconds') for p in [1, 2, 4, 8]]
        values += [value(8, 'speedup'), value(2, 'karp_flatt'), value(8, 'karp_flatt')]
        lines.append(f'| {label} | {config["items"]} | ' + ' | '.join(values) + ' |')
    lines += ['', '## Environment and detailed results', '']
    for key, config in data.items():
        lines += [f'### {labels.get(key, key)}', '',
                  f'- Date: {config["timestamp"]}',
                  f'- OS: {config["platform"]}',
                  f'- Python: {config["python"]}',
                  f'- Logical CPUs: {config["cpu_count"]}; default pool count: {config["pool_cpu_count"]}',
                  f'- Items: {config["items"]}; repeats: {config["repeats"]}',
                  f'- Chunk/batch size: {config.get("chunk_size", config.get("batch_size", "one item per message"))}', '',
                  '| P | Time (s) | Speedup | Efficiency (%) | e(p) | Checksum |',
                  '|---:|---:|---:|---:|---:|---:|']
        for r in config['rows']:
            metric = '-' if r['karp_flatt'] is None else f'{r["karp_flatt"]:.6f}'
            speedup = '-' if r['speedup'] is None else f'{r["speedup"]:.6f}'
            efficiency = '-' if r['efficiency_pct'] is None else f'{r["efficiency_pct"]:.2f}'
            lines.append(f'| {r["p"]} | {r["seconds"]:.6f} | {speedup} | '
                         f'{efficiency} | {metric} | {r["checksum"]} |')
        lines.append('')
    lines += ['## Interpretation - complete after running', '',
              '- A: Compare micro and coarse timings at the same P. Explain dispatch and serialization costs.',
              '- B: Compare T1, T4, T8 and the trend in e(p). State whether negative scaling occurred.',
              '- C: Compare S8 and e(8) with the requested targets (S8 > 5 and e(8) <= 0.05).',
              '- Compare throughput = items / seconds for B and C at the same P. '
              'Their default item counts differ, so report both time and throughput.',
              '- Explain any missed targets using measured evidence and machine/process startup limitations. '
              'Do not replace measured values with the sample numbers from the handout.', '',
              'Karp-Flatt reflects effective overhead; an increasing value is consistent with '
              'growing parallel overhead, but by itself does not identify a particular OS or hardware cause.', '']
    (directory / 'RESULTS_B.md').write_text('\n'.join(lines), encoding='utf-8')
