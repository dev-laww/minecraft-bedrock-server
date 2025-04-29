seconds_per_unit = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}


def convert_to_seconds(s: str) -> int:
    return int(s[:-1]) * seconds_per_unit[s[-1]]
