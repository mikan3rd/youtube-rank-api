from . import data


blueprints = [
    data.stats_daily,
    data.charge,
]


def get_blueprints() -> list:
    return blueprints
