import os
import zlib
from pathlib import Path


class Wal:
    """Самописный WAL для трендов."""

    def __init__(self, wal_path: str, repo):
        self.path = Path(wal_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.repo = repo
        self.seq = repo.get_wal_seq()

    @staticmethod
    def _checksum(fields: list[str]) -> str:
        return format(zlib.crc32("|".join(fields).encode("utf-8")), "08x")

    def append(self, trend_id, source_id, object_id, value, reason, ts) -> int:
        self.seq += 1
        fields = [
            str(self.seq), str(trend_id), str(source_id), object_id,
            "" if value is None else str(value), reason or "", f"{ts:.6f}",
        ]
        line = "|".join(fields) + "|" + self._checksum(fields) + "\n"

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

        self._apply(trend_id, source_id, object_id, value, reason, ts)
        return self.seq

    def _apply(self, trend_id, source_id, object_id, value, reason, ts):
        self.repo.insert_trend_value(trend_id, source_id, object_id, value, reason, ts)
        self.repo.trim_trend_window(trend_id, window=3600)
        self.repo.set_wal_seq(self.seq)
        self.repo.commit()

    def replay(self):
        if not self.path.exists():
            return
        last = self.repo.get_wal_seq()
        applied = 0
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) != 8:
                    continue
                *fields, crc = parts
                if self._checksum(fields) != crc:
                    continue
                seq = int(fields[0])
                if seq <= last:
                    continue
                trend_id = int(fields[1])
                source_id = int(fields[2])
                object_id = fields[3]
                value = fields[4] if fields[4] != "" else None
                reason = fields[5]
                ts = float(fields[6])
                self.seq = seq
                self._apply(trend_id, source_id, object_id, value, reason, ts)
                applied += 1
        print(f"[WAL] replay: восстановлено {applied} записей")

    def checkpoint(self):
        with open(self.path, "w", encoding="utf-8"):
            pass