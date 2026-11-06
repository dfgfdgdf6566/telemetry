import random
import time


class Source:
    """Симулятор одного источника телеметрии."""

    def __init__(self, source_id: int):
        self.source_id = source_id

    def poll(self) -> list[dict]:
        """Возвращает пачку объектов: 100–600 штук, значения разные."""
        n = random.randint(100, 600)
        batch = []
        for i in range(n):
            object_id = f"src{self.source_id}_obj{i}"
            kind = random.choices(
                ["int", "float", "bool", "str", "none"],
                weights=[40, 40, 15, 3, 2],
            )[0]

            if kind == "int":
                value = random.randint(-1000, 1000)
            elif kind == "float":
                value = round(random.uniform(-1000, 1000), 3)
            elif kind == "bool":
                value = random.choice([True, False])
            elif kind == "str":
                value = "bad_value"
            else:
                value = None

            batch.append({
                "source_id": self.source_id,
                "object_id": object_id,
                "value": value,
                "timestamp": time.time(),
            })
        return batch