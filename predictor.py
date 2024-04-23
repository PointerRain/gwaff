import pandas as pd
from datetime import datetime, timedelta
import discord
from math import floor, ceil

PREDICTION_DEFAULT_DAYS: int = 30       # The default number of days to be used
#  in a prediction
MAX_TARGET_DISTANCE: int = 100 * 365    # The number of days before a target is
#  too far away


class NoDataError(Exception):
    '''
    Thrown when there is no data, or not enough
    recent data to make a prediction.
    '''
    pass


class ZeroGrowthError(Exception):
    '''
    Thrown when a user has had no growth within the timeframe.
    '''
    pass


class InvalidTargetError(Exception):
    '''
    Thrown when an invalid target format is chosen.
    '''
    pass


class TargetBoundsError(Exception):
    '''
    Thrown when the target is too far away.
    > MAX_TARGET_DISTANCE
    '''
    pass


def lvl_to_xp(lvl: int) -> int:
    '''
    Converts a level to the equivalent xp value.

    lvl: The level to convert to an xp value.

    Returns: The xp value required for the given level.
    '''
    return (1.667*lvl**3)+(22.5*lvl**2)+(75.833*lvl)


def xp_to_lvl(xp: int) -> int:
    '''
    Converts an xp value to the equivalent level.
    Behaviour is only correct when xp>6859 and level<100.
    xp: The xp value to convert to a level.
    '''
    A = 3.582
    B = 2.861
    C = 6859
    if xp <= C:
        return 0
        A = 6.204
        B = 2.724
        C = 2079
    return floor(((xp-C)/A)**(1/B))


def remove_suffix(value: str) -> int:
    '''
    Converts a string representation of a number with a suffix to an int.
     - k = thousand
     - M = Million
     - B = Billion
    (Trillions could be added and will not conflict with user ids)

    value: A string of a number containing a suffix to be removed.

    Returns: the equivalent int with the suffix removed.
    '''
    if value.endswith('k'):
        return int(value[:-1]) * 1000
    if value.endswith('M'):
        return int(value[:-1]) * 1000000
    if value.endswith('B'):
        return int(value[:-1]) * 1000000000
    return int(value)


class Prediction:
    '''
    Class to process and evaluate predictions
    '''

    def __init__(self, data: pd.DataFrame,
                 member: int,
                 target: str,
                 period: int = PREDICTION_DEFAULT_DAYS,
                 growth: int = None):
        self.data = data
        self.member = int(member)

        # Determine the target type and level
        self.parse_target(target)

        # Find period to check
        self.period = period
        if period <= 0:
            raise NoDataError('Period must be greater than 0')
        self.start_date = datetime.now()-timedelta(days=period)

        self.dates = data.columns
        self.date = [d for d in list(self.dates)[4:]
                     if d > str(self.start_date)]
        self.dates.sort()

        # Get growth data for the member
        self.value, self.growth = self.get_data(member)
        if growth != None:
            self.growth = growth

        # If it is a relative prediction, set the target according to their
        #  current stats.
        if self.relative:
            if self.target_type == 'xp':
                self.target = self.value + self.target
            if self.target_type == 'level':
                self.target = xp_to_lvl(self.value) + self.target

    def parse_target(self, target: str) -> tuple:
        # Determine if the target is relative
        if type(target) is str and target.startswith('+'):
            self.relative = True
            self.target = target[1:]
        elif type(target) is str and target.startswith('-'):
            self.relative = True
            self.target = target
        else:
            self.relative = False

        # Determine type from simple clues
        if type(target) is str and target.endswith('xp'):
            self.target_type = 'xp'
            self.target = remove_suffix(target[:-2])
        elif type(target) is str and target.startswith('lvl'):
            self.target_type = 'level'
            self.target = remove_suffix(target[3:])
        elif type(target) is str and target.startswith('level'):
            self.target_type = 'level'
            self.target = remove_suffix(target[5:])
        elif type(target) is str and target.startswith('<@'):
            self.target_type = 'user'
            self.target = int(target[2:-1])

        # Determine type from size
        elif remove_suffix(target) <= 1000:
            self.target_type = 'level'
            self.target = remove_suffix(target)
        elif remove_suffix(target) <= 100000000:
            self.target_type = 'xp'
            self.target = remove_suffix(target)
        elif remove_suffix(target) >= 10000000000:
            self.target_type = 'user'
            self.target = int(target)

        else:
            raise InvalidTargetError('The target does not match a known format')

        return (self.target_type, self.target)

    def get_data(self, user: int) -> tuple:
        start_xp = None
        start_date = None
        final_xp = None
        final_date = None

        for index, row in list(self.data.iterrows()):
            if row['ID'] == int(user):
                for i in self.dates:
                    date = datetime.fromisoformat(i)
                    if self.start_date and date < self.start_date:
                        continue
                    if row[i] is None or pd.isna(row[i]):
                        continue

                    # Update values if not already set
                    start_xp = start_xp or row[i]
                    start_date = start_date or date
                    final_xp = final_xp or row[i]
                    final_date = final_date or date
                    # Overwrite previous values if needed
                    start_xp = min(row[i], start_xp)
                    start_date = min(date, start_date)
                    final_xp = max(row[i], final_xp)
                    final_date = max(date, final_date)

                if final_date is None:
                    raise NoDataError(
                        'There is no data for this user within range')

                final_growth = final_xp-start_xp

                if final_growth <= 0:
                    raise ZeroGrowthError

                # Find the actual period the data was taken from
                actual_period = (final_date - start_date) / timedelta(days=1)

                return final_xp, final_growth/actual_period
        raise NoDataError('The specified user could not be found')

    def simple_target(self, target: int) -> float:
        '''
        Finds the intercept of an unmoving target.
        y = mx+c
        x = (y-c)/m
        '''
        return (target-self.value)/self.growth

    def complex_target(self, target) -> float:
        '''
        Finds the intercept of a linearly moving target.
        m1x+c1 = m2x+c2
        x = (c2-c1)/(m1-m2)
        '''
        other_value, other_growth = self.get_data(target)
        return (other_value-self.value)/(self.growth-other_growth)

    def evaluate(self) -> float:
        days = None
        if self.target_type == 'xp':
            days = self.simple_target(self.target)
        elif self.target_type == 'level':
            days = self.simple_target(lvl_to_xp(self.target))
        elif self.target_type == 'user':
            days = self.complex_target(self.target)
        else:
            raise InvalidTargetError
        if abs(days) >= 100 * 365:
            raise TargetBoundsError
        return days


if __name__ == '__main__':
    print(xp_to_lvl(183734))
    print(lvl_to_xp(43))
    print(xp_to_lvl(177375))
    print(xp_to_lvl(188870))
    # Some test cases
    assert xp_to_lvl(183734) == 43
    assert lvl_to_xp(43) >= 177373
    assert xp_to_lvl(177390) == 43
    assert xp_to_lvl(188870) == 44
