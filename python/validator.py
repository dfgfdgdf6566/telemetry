def is_valid(value) -> bool:
    """True, если значение скалярное: bool или число (int/float)."""
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return True
    return False