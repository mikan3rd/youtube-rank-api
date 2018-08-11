from . import data, line


blueprints = [
    data.stats_daily,
    data.charge,
    data.gnavi,
    line.face_search,
    line.av_sommelier,
]


def get_blueprints() -> list:
    return blueprints
