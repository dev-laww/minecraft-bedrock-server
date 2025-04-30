seconds_per_unit = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}


def convert_to_seconds(s: str) -> int:
    return int(s[:-1]) * seconds_per_unit[s[-1]]


def convert_from_seconds(n: int) -> str:
    units = [('w', 604800), ('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    parts = []
    for suf, val in units:
        q, n = divmod(n, val)
        if q:
            parts.append(f"{q}{suf}")
    return ' '.join(parts) or '0s'
