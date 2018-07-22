from . import data, line


blueprints = [
    data.stats_daily,
    data.charge,
    data.gnavi,
    line.face_search,
]


def get_blueprints() -> list:
    return blueprints
