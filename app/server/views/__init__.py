from . import data


blueprints = [
    data.stats_daily,
    data.charge,
    data.gnavi,
    data.drinkee,
]


def get_blueprints() -> list:
    return blueprints
