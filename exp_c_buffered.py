"""Experiment C: send one locally aggregated sum per batch."""
import multiprocessing as mp
import time
from lab_utils import arguments, expected_sum, measure, partitions, save_results


def buffered_worker(out_queue, start, stop, batch_size=10_000):
    buffer = []
    for i in range(start, stop):
        buffer.append(i % 7)
        if len(buffer) >= batch_size:
            out_queue.put(sum(buffer))
            buffer.clear()
    if buffer:
        out_queue.put(sum(buffer))
    out_queue.put(None)


def run_buffered(p, total_items=10_000_000, batch_size=10_000):
    q = mp.Queue()
    workers = [mp.Process(target=buffered_worker, args=(q, start, stop, batch_size))
               for start, stop in partitions(total_items, p)]
    t0 = time.perf_counter()
    for worker in workers:
        worker.start()
    active, total = p, 0
    while active:
        value = q.get()
        if value is None:
            active -= 1
        else:
            total += value
    for worker in workers:
        worker.join()
        if worker.exitcode != 0:
            raise RuntimeError(f'Worker failed: {worker.exitcode}')
    q.close()
    q.join_thread()
    elapsed = time.perf_counter() - t0
    if total != expected_sum(total_items):
        raise RuntimeError('Buffered result failed validation')
    return elapsed, total


def main():
    args = arguments(__doc__, 10_000_000, batch=True)
    rows = measure(lambda p: run_buffered(p, args.items, args.batch_size), args,
                   key='c_buffered', batch_size=args.batch_size)
    save_results('c_buffered', rows, args, batch_size=args.batch_size)


if __name__ == '__main__':
    mp.freeze_support()
    main()
