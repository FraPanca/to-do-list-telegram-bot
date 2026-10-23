def parse_positive_int(args) -> int | None:
    if len(args) != 1:
        return None
    try:
        value = int(args[0])
        return value if value > 0 else None
    except ValueError:
        return None
    