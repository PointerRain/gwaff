# Reduces unnecessary entries and columns based on the following rules:
# If a column is over 48h old, only store every 2nd hour
# If a column is over a week old, only store every 4th hour
# If a column is over a month old, only store every 24th hour
# TODO:
# If a value is the same as before and after, remove it
# If a value is the same as before and last, remove it


import pandas as pd
from datetime import datetime, timedelta


class Reducer:
    def __init__(self, data):
        self.data = data
        self.dates = data.columns
        self.dates = list(self.dates)[4:]

    def sort(self):
        # Find final value for xp using the read_row function
        data = [self.read_row(row)[1] for index, row in self.data.iterrows()]
        self.data['Final'] = [row[-1] for row in data]
        self.data.sort_values(by='Final', inplace=True, ascending=False)

    def read_row(self, row, start_date=None):
        xs = []
        values = []
        for i in self.dates:
            date = datetime.fromisoformat(i)
            # if self.start_date and date < self.start_date:
            #     continue
            if row[i] is None:
                continue

            values.append(row[i])
            xs.append(date)
        xs.append(self.dates[-1])
        values.append(values[-1])

        return xs, values

    def reduce_cols(self):
        self.sort()
        new_columns = [column for column in self.data][:4]
        dates = [datetime.fromisoformat(date) for date in self.dates]
        now = datetime.now()

        index = 1
        del_count = 0
        while index < len(dates)-1:
            column = dates[index]
            
            diff = dates[index+1] - dates[index-1]
            age = now - column

            if age > timedelta(days=2) and diff/2 < timedelta(hours=1):
                del_count += 1
                dates.remove(column)
            elif age > timedelta(days=7) and diff/2 < timedelta(hours=4):
                del_count += 1
                dates.remove(column)
            elif age > timedelta(days=30) and diff/2 < timedelta(hours=12):
                del_count += 1
                dates.remove(column)
            elif age > timedelta(days=100) and diff/2 < timedelta(hours=24):
                del_count += 1
                dates.remove(column)
            else:
                index += 1
        new_columns = new_columns + [str(date) for date in dates]
        # new_columns.delete('Final')
        self.data = self.data[new_columns]
        print('Deleted', del_count, 'columns')

    def save(self):
        # self.data.drop(['Final'], axis=1, inplace=True)
        self.data.to_csv('gwaff.csv', encoding='utf-8')
        print('saved')


df = pd.read_csv("gwaff.csv", index_col=0)
reducer = Reducer(df)
reducer.reduce_cols()
reducer.save()
