from datetime import datetime, timedelta
from math import floor

from database import DatabaseReader

PREDICTION_DEFAULT_DAYS: int = 30  # The default number of days to be used in a prediction.
MAX_TARGET_DISTANCE: int = 100 * 365  # The number of days before a target is too far away.


class NoDataError(Exception):
    """Thrown when there is no data, or not enough recent data to make a prediction."""
    ...


class ZeroGrowthError(Exception):
    """Thrown when a user has had no growth within the timeframe."""
    ...


class InvalidTargetError(Exception):
    """Thrown when an invalid target format is chosen."""
    ...


class TargetBoundsError(Exception):
    """Thrown when the target is too far away (> MAX_TARGET_DISTANCE)."""
    ...


def lvl_to_xp(lvl: int) -> int:
    """
    Converts a level to the equivalent xp value.

    lvl: The level to convert to an xp value.

    Returns: The xp value required for the given level.
    """
    xp = (1.667 * lvl ** 3) + (22.5 * lvl ** 2) + (75.833 * lvl)
    return 5 * round(xp / 5)


def xp_to_lvl(xp: int) -> int:
    """
    Converts an xp value to the equivalent level.
    Behaviour is only correct when xp>12017 and level<100.

    Args:
        xp (int): The xp value to convert to a level.

    Returns: The level at the given xp.
    """
    if xp <= 145000:
        # If xp is relatively low (<=lvl39) use this approximation
        A, B, C = 6.204, 2.724, 2079
    else:
        # If xp is relatively high (>lvl39) use separate approximation
        A, B, C = 3.266, 2.881, 12017

    return floor(((xp - C) / A) ** (1 / B))


def remove_suffix(value: str) -> int:
    """
    Converts a string representation of a number with a suffix to an int.
     - k = thousand
     - M = Million
     - B = Billion
    (Trillions could be added and will not conflict with user ids)

    value: A string of a number containing a suffix to be removed.

    Returns: the equivalent int with the suffix removed.
    """
    value = value.lower()
    if value.endswith('k'):
        return int(float(value[:-1]) * 1_000)
    if value.endswith('m'):
        return int(float(value[:-1]) * 1_000_000)
    if value.endswith('b'):
        return int(float(value[:-1]) * 1_000_000_000)

    return int(value)


def parse_target(target: str) -> tuple:
    # Determine if the target is relative
    target = target.strip()
    relative = target.startswith(('+', '-'))

    if target.endswith('xp'):
        target_type = 'xp'
        target_value = remove_suffix(target[:-2])
    elif target.startswith(('lvl', 'level')):
        target_type = 'level'
        target_value = remove_suffix(target.lstrip('level').lstrip('lvl'))
    elif target.startswith('<@'):
        target_type = 'user'
        target_value = int(target[2:-1])
    else:
        target_value = remove_suffix(target)
        target_type = 'level' if target_value <= 1000 else 'xp'

    if target_type not in {'xp', 'level', 'user'}:
        raise InvalidTargetError(f"Unknown target format: {target}")

    return target_type, target_value, relative


class Prediction:
    """
    Class to process and evaluate predictions
    """

    def __init__(self, member: int,
                 target: str,
                 period: int = PREDICTION_DEFAULT_DAYS,
                 growth: int = None):
        self.member = member
        self.period = period
        self.start_date = datetime.now() - timedelta(days=period)

        # Validate and process the target
        self.target_type, self.target, self.relative = parse_target(target)

        # Get growth data for the member
        self.value, self.growth = self.get_data(member)
        if growth is not None:
            self.growth = growth

        # If it is a relative prediction, set the target according to their
        #  current stats.
        if self.relative:
            if self.target_type == 'xp':
                self.target = self.value + self.target
            if self.target_type == 'level':
                self.target = xp_to_lvl(self.value) + self.target

    def get_data(self, user: int) -> tuple:
        dbr = DatabaseReader()
        row = dbr.get_row(user, self.start_date)

        if len(row) <= 1:
            raise NoDataError('There is no data for this user within range')

        start_xp, start_date = row[0].value, row[0].timestamp
        final_xp, final_date = row[-1].value, row[-1].timestamp

        final_growth = final_xp - start_xp

        if final_growth <= 0:
            raise ZeroGrowthError('The user has no activity during this period')

        # Find the actual period the data was taken from
        actual_period = (final_date - start_date) / timedelta(days=1)

        return final_xp, final_growth / actual_period

    def simple_target(self, target: int) -> float:
        """
        Finds the intercept of an unmoving target.
        y = mx+c
        x = (y-c)/m
        """
        return (target - self.value) / self.growth

    def complex_target(self, target) -> float:
        """
        Finds the intercept of a linearly moving target.
        m1x+c1 = m2x+c2
        x = (c2-c1)/(m1-m2)
        """
        other_value, other_growth = self.get_data(target)
        return (other_value - self.value) / (self.growth - other_growth)

    def evaluate(self) -> float:
        if self.target_type == 'xp':
            days = self.simple_target(self.target)
        elif self.target_type == 'level':
            days = self.simple_target(lvl_to_xp(self.target))
        elif self.target_type == 'user':
            days = self.complex_target(self.target)
        else:
            raise InvalidTargetError("Invalid target type.")

        if abs(days) >= MAX_TARGET_DISTANCE:
            raise TargetBoundsError(
                f"Target exceeds the maximum distance of {MAX_TARGET_DISTANCE} days.")

        return days


if __name__ == '__main__':
    # Some test cases
    assert xp_to_lvl(183734) == 43
    assert lvl_to_xp(43) >= 177373
    assert xp_to_lvl(180000) == 43
    assert xp_to_lvl(189870) == 44

    print(Prediction(344731282095472641, '100').evaluate())
