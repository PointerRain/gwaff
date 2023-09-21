import pandas as pd
from datetime import datetime, timedelta
import discord
from math import floor, ceil

def lvl_to_xp(lvl):
    return (1.667*lvl**3)+(22.5*lvl**2)+(75.833*lvl)

def xp_to_lvl(xp):
    A = 3.582
    B = 2.861
    C = 6859
    if xp <= C:
        return 0
    return floor(((xp-C)/A)**(1/B))

def remove_suffix(value):
    if value.endswith('k'):
        return int(value[:-1])*1000
    if value.endswith('M'):
        return int(value[:-1])*1000000
    if value.endswith('B'):
        return int(value[:-1])*1000000000
    return int(value)

class Prediction:
    def __init__(self, data, member, target, period=30, growth=None):
        self.data = data
        self.member = int(member)

        if type(target) is str and target.startswith('+'):
            self.relative = True
            target = target[1:]
        else:
            self.relative = False

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
            self.target_type = None
            self.target = target

        self.period = period
        if period <= 0:
            raise ZeroDivisionError
        self.start_date = datetime.now()-timedelta(days=period)

        self.dates = data.columns
        self.dates = list(self.dates)[4:]
        self.dates.sort()

        self.value, self.growth = self.get_data(member)
        if growth != None:
            self.growth = growth

        if self.value is None or self.growth is None:
            raise ValueError

        if self.relative:
            if self.target_type == 'xp':
                self.target = self.value + self.target
                print(self.target)
            if self.target_type == 'level':
                self.target = xp_to_lvl(self.value) + self.target
                print(self.target)

    def get_data(self, user):

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

                    start_xp = start_xp or row[i]
                    start_date = start_date or date
                    final_xp = final_xp or row[i]
                    final_date = final_date or date
                    
                    start_xp = min(row[i], start_xp)
                    start_date = min(date, start_date)
                    final_xp = max(row[i], final_xp)
                    final_date = max(date, final_date)
                    
                final_growth = final_xp-start_xp
                actual_period = (final_date - start_date) / timedelta(days=1)
                
                return final_xp, final_growth/actual_period
        raise IndexError

    def simple_target(self, target):
        return (target-self.value)/self.growth

    def complex_target(self):
        other_value, other_growth = self.get_data(self.target)
        return (other_value-self.value)/(self.growth-other_growth)

    def evaluate(self):
        if self.target_type == 'xp':
            return self.simple_target(self.target)
        elif self.target_type == 'level':
            return self.simple_target(lvl_to_xp(self.target))
        elif self.target_type == 'user':
            return self.complex_target()
        else:
            return 'target'


if __name__ == '__main__':
    print(xp_to_lvl(183734))
    print(lvl_to_xp(43))
    print(xp_to_lvl(177375))
    print(xp_to_lvl(188870))