import pandas as pd
from datetime import datetime, timedelta

from custom_logger import Logger
logger = Logger('gwaff.reduce')


class Reducer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.dates = data.columns
        self.dates = list(self.dates)[4:]

    def sort(self) -> None:
        # Find final value for xp using the read_row function
        data = [self.read_row(row)[1] for index, row in self.data.iterrows()]
        self.data['Final'] = [row[-1] for row in data]
        self.data.sort_values(by='Final', inplace=True, ascending=False)

    def read_row(self, row: pd.Series,
                 start_date: datetime = None) -> tuple[list[datetime], list[int]]:
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

    def reduce_cols(self) -> None:
        # If something goes wrong, abort the change
        try:
            self.sort()
            new_columns = [column for column in self.data][:4]
            dates = [datetime.fromisoformat(date) for date in self.dates]
            now = datetime.now()

            index = 1
            self.del_count = 0
            while index < len(dates)-1:
                column = dates[index]

                diff = dates[index+1] - dates[index-1]
                age = now - column

                if any([age > timedelta(days=1) and diff/2 < timedelta(hours=2),
                    age > timedelta(days=7) and diff/2 < timedelta(hours=6),
                    age > timedelta(days=30) and diff/2 < timedelta(hours=12),
                    age > timedelta(days=100) and diff/2 < timedelta(hours=24)
                ]):
                    self.del_count += 1
                    dates.remove(column)
                else:
                    index += 1
            new_columns = new_columns + [str(date) for date in dates]
            # new_columns.delete('Final')
            self.data = self.data[new_columns]
            logger.warning(f'Deleting {self.del_count} columns')
            return f'Deleting {self.del_count} columns'
        except Exception as e:
            logger.error(f'Could not reduce columns\n{e}')
            return False


    def save(self) -> None:
        # self.data.drop(['Final'], axis=1, inplace=True)
        try:
            self.data.to_csv('gwaff.csv', encoding='utf-8')
            logger.warning(f'Deleted {self.del_count} columns')
            return True
        except Exception as e:
            logger.error(f'Could not save deleted columns\n{e}')
            return e

if __name__ == '__main__':
    df = pd.read_csv("gwaff.csv", index_col=0)
    reducer = Reducer(df)
    confirm = input('Do you want to run the reducer? (Y or n)\n')
    # confirm = 'Y'
    if confirm == 'Y':
        reducer.reduce_cols()
    else:
        print('Aborted')
    confirm = input('Are you really sure? (Y or n)\n')
    if confirm == 'Y':
        reducer.save()
    else:
        print('Aborted')
