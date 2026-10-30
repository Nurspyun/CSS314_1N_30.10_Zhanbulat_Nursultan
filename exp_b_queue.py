"""Experiment B: send every record through a shared multiprocessing.Queue."""
import multiprocessing as mp
import time
from lab_utils import arguments, expected_sum, measure, partitions, save_results


def queue_worker(out_queue, start, stop):
    for i in range(start, stop):
        out_queue.put(i % 7)
    out_queue.put(None)


def run_queue_benchmark(p, total_items=400_000):
    q = mp.Queue()
    workers = [mp.Process(target=queue_worker, args=(q, start, stop))
               for start, stop in partitions(total_items, p)]
    t0 = time.perf_counter()
    for worker in workers:
        worker.start()
    active, count, total = p, 0, 0
    while active:
        value = q.get()
        if value is None:
            active -= 1
        else:
            count += 1
            total += value
    for worker in workers:
        worker.join()
        if worker.exitcode != 0:
            raise RuntimeError(f'Worker failed: {worker.exitcode}')
    q.close()
    q.join_thread()
    elapsed = time.perf_counter() - t0
    if count != total_items or total != expected_sum(total_items):
        raise RuntimeError('Queue result failed validation')
    return elapsed, total


def main():
    args = arguments(__doc__, 400_000)
    rows = measure(lambda p: run_queue_benchmark(p, args.items), args, key='b_queue')
    save_results('b_queue', rows, args)


if __name__ == '__main__':
    mp.freeze_support()
    main()
