import pandas as pd
from datetime import datetime, timedelta
import discord


class Truerank:
    def __init__(self, data, period=30, threshold=1):
        self.data = data

        self.period = period
        if period <= 0:
            raise ZeroDivisionError
        self.start_date = datetime.now() - timedelta(days=period)

        self.threshold = threshold

        self.dates = data.columns
        self.dates = list(self.dates)[4:]
        self.dates.sort()

        self.values = self.get_data()

        self.sort()
        # self.growth = growth or self.growth

        # if self.value is None or self.growth is None:
        #     raise ValueError

    def get_data(self):
        values = []
        for index, row in list(self.data.iterrows()):
            startxp = None
            finalxp = 0
            for i in self.dates:
                date = datetime.fromisoformat(i)
                if self.start_date and date < self.start_date:
                    continue
                if row[i] is None or pd.isna(row[i]):
                    continue

                startxp = startxp or row[i]
                startxp = min(row[i], startxp)
                finalxp = max(row[i], finalxp)
            if startxp is None:
                continue
            finalgrowth = finalxp - startxp
            if finalgrowth > self.threshold:
                item = (row['ID'], row['Name'], finalxp)
                values.append(item)
        return values

    def sort(self):
        self.values.sort(key=lambda x: x[2], reverse=True)

    def find_index(self, member):
        for index, item in enumerate(self.values):
            if item[0] == member:
                if index <= 0:
                    return index, item[2], 0, item[2]
                return index, item[2], self.values[index - 1][0], self.values[
                    index - 1][2], self.values[index - 1][1]
        raise IndexError
