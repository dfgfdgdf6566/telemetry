import sqlite3
from pathlib import Path


class Repository:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id  INTEGER NOT NULL,
                object_id  TEXT    NOT NULL,
                value      TEXT    NOT NULL,
                value_type TEXT    NOT NULL,
                timestamp  REAL    NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry(timestamp);")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS trend_values (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                trend_id  INTEGER NOT NULL,
                source_id INTEGER NOT NULL,
                object_id TEXT    NOT NULL,
                value     TEXT,
                reason    TEXT,
                timestamp REAL    NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_trend_tid ON trend_values(trend_id, id);")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS wal_meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.conn.commit()

    def insert_valid_batch(self, rows: list[dict]):
        if not rows:
            return
        cur = self.conn.cursor()
        cur.executemany(
            "INSERT INTO telemetry(source_id, object_id, value, value_type, timestamp) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                (r["source_id"], r["object_id"], str(r["value"]),
                 type(r["value"]).__name__, r["timestamp"])
                for r in rows
            ],
        )
        self.conn.commit()

    def insert_trend_value(self, trend_id, source_id, object_id, value, reason, ts):
        self.conn.execute(
            "INSERT INTO trend_values(trend_id, source_id, object_id, value, reason, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (trend_id, source_id, object_id, str(value), reason, ts),
        )

    def trim_trend_window(self, trend_id: int, window: int = 3600):
        self.conn.execute(
            """
            DELETE FROM trend_values
            WHERE trend_id = ?
              AND id NOT IN (
                  SELECT id FROM trend_values
                  WHERE trend_id = ?
                  ORDER BY id DESC
                  LIMIT ?
              )
            """,
            (trend_id, trend_id, window),
        )

    def get_wal_seq(self) -> int:
        cur = self.conn.execute("SELECT value FROM wal_meta WHERE key='last_seq'")
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def set_wal_seq(self, seq: int):
        self.conn.execute(
            "INSERT INTO wal_meta(key, value) VALUES('last_seq', ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(seq),),
        )

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()