import zlib

NUM_TRENDS = 20
TREND_NAMES = [f"trend_{i:02d}" for i in range(NUM_TRENDS)]


def pick_trend(object_id: str) -> int:
    """Детерминированно выбирает тренд 0..19 по object_id."""
    h = zlib.crc32(object_id.encode("utf-8"))
    return h % NUM_TRENDS