import pandas as pd
from datetime import datetime, timedelta
import discord

def lvl_to_xp(lvl):
    return (1.667*lvl**3)+(22.5*lvl**2)+(75.833*lvl)

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
        elif int(target) >= 10000000000:
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
        self.growth = growth or self.growth

        if self.value is None or self.growth is None:
            raise ValueError

    def get_data(self, user):

        startxp = None
        finalxp = 0

        for index, row in list(self.data.iterrows()):
            if row['ID'] == int(user):
                for i in self.dates:
                    date = datetime.fromisoformat(i)
                    if self.start_date and date < self.start_date:
                        continue
                    if row[i] is None or pd.isna(row[i]):
                        continue

                    startxp = startxp or row[i]
                    startxp = min(row[i], startxp)
                    finalxp = max(row[i], finalxp)
                    
                finalgrowth = row[i]-startxp
                return finalxp, finalgrowth/self.period
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
