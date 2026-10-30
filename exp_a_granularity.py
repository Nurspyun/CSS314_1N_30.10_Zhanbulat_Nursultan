"""Experiment A: Collatz tasks with fine and coarse Pool.map chunks."""
import multiprocessing as mp
import time
from lab_utils import arguments, measure, save_results


def collatz_steps(n):
    steps = 0
    while n > 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps


def run_granularity(workers, total_items=1_000_000, chunk_size=1):
    t0 = time.perf_counter()
    with mp.Pool(processes=workers) as pool:
        results = pool.map(collatz_steps, range(1, total_items + 1), chunksize=chunk_size)
    checksum = sum(results)
    return time.perf_counter() - t0, checksum


def main():
    args = arguments(__doc__, 1_000_000)
    checksums = []
    for key, chunk_size in [('a_micro', 1), ('a_coarse', 10_000)]:
        print(f'\nExperiment A: chunksize={chunk_size}', flush=True)
        rows = measure(lambda p: run_granularity(p, args.items, chunk_size), args,
                       key=key, chunk_size=chunk_size)
        checksums.append(rows[0]['checksum'])
        save_results(key, rows, args, chunk_size=chunk_size)
    if checksums[0] != checksums[1]:
        raise RuntimeError('Fine and coarse runs produced different results')


if __name__ == '__main__':
    mp.freeze_support()
    main()
