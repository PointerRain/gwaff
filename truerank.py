import pandas as pd
from datetime import datetime, timedelta
# import discord

PREDICTION_DEFAULT_DAYS = 30
RANK_DEFAULT_THRESHOLD = 30


class Truerank:
    def __init__(self, data, period=PREDICTION_DEFAULT_DAYS,
                 threshold=RANK_DEFAULT_THRESHOLD):
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
                item = {
                    'ID': row['ID'],
                    'name': row['Name'],
                    'xp': round(finalxp),
                    'url': row['Avatar']
                }
                values.append(item)
        return values

    def sort(self):
        self.values.sort(key=lambda x: x['xp'], reverse=True)

    def find_index(self, member):
        result = {}
        for index, item in enumerate(self.values):
            if item['ID'] == member:
                result["rank"] = index
                result['name'] = item['name']
                result["xp"] = item['xp']
                result["url"] = item['url']
                if index == 0:
                    return result
                result['other_ID'] = self.values[index - 1]['ID']
                result['other_name'] = self.values[index - 1]['name']
                result['other_xp'] = self.values[index - 1]['xp']
                return result
        raise IndexError

if __name__ == '__main__':
    data = pd.read_csv("gwaff.csv", index_col=0)
    truerank = Truerank(data)
    result = truerank.find_index(344731282095472641)
    print(result)