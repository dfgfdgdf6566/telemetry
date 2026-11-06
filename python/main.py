import threading
import time
from pathlib import Path

from sources import Source
from validator import is_valid
from repository import Repository
from wal import Wal
from trends import pick_trend

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "telemetry.db"
WAL_PATH = BASE / "wal" / "trends.wal"

CHECKPOINT_EVERY_SEC = 30

def collect_cycle(sources, repo, wal):
    results = [None] * len(sources)

    def worker(i, src):
        try:
            results[i] = src.poll()
        except Exception as e:
            print(f"[source {i}] ошибка: {e}")

    threads = [threading.Thread(target=worker, args=(i, s)) for i, s in enumerate(sources)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=1.0)

    valid_rows = []
    invalid_count = 0

    for batch in results:
        if batch is None:
            continue
        for obj in batch:
            if is_valid(obj["value"]):
                valid_rows.append(obj)
            else:
                invalid_count += 1
                trend_id = pick_trend(obj["object_id"])
                reason = f"invalid type: {type(obj['value']).__name__}"
                wal.append(
                    trend_id=trend_id,
                    source_id=obj["source_id"],
                    object_id=obj["object_id"],
                    value=obj["value"],
                    reason=reason,
                    ts=obj["timestamp"],
                )

    repo.insert_valid_batch(valid_rows)
    return len(valid_rows), invalid_count


def main():
    repo = Repository(str(DB_PATH))
    wal = Wal(str(WAL_PATH), repo)
    wal.replay()

    sources = [Source(i) for i in range(1, 5)]
    print(f"[start] 4 источника, БД={DB_PATH}, WAL={WAL_PATH}")

    last_checkpoint = time.monotonic()
    try:
        while True:
            t0 = time.monotonic()
            valid_n, invalid_n = collect_cycle(sources, repo, wal)
            elapsed = time.monotonic() - t0
            print(f"[tick] валидных={valid_n}, невалидных={invalid_n}, время={elapsed:.3f}с")

            if time.monotonic() - last_checkpoint >= CHECKPOINT_EVERY_SEC:
                wal.checkpoint()
                last_checkpoint = time.monotonic()
                print("[WAL] checkpoint выполнен")

            sleep_for = max(0.0, 1.0 - elapsed)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("\n[stop] завершение, сохраняем...")
    finally:
        repo.close()


if __name__ == "__main__":
    main()