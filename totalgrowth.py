import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from activity import Activity

class TotalGrowth(Activity):
    # def sort(self):
    #     data = [self.read_row(row) for index, row in self.data.iterrows()]
    #     data = [row[list(row)[-1]] for row in data]
    #     self.data['Change'] = [row[-1] - row[0] for row in data]
    #     self.data.sort_values(by='Change', inplace=True, ascending=False)

    def read_row(self, row):
        values = {}
        xs = []
        prior = None

        for i in self.dates:
            date = datetime.fromisoformat(i)
            if self.start_date and date < self.start_date:
                continue
            if row[i] is None or pd.isna(row[i]):
                continue

            # prior = prior or row[i]
            if prior is None:
                prior = row[i]
                difference = 1
            else:
                difference = date - xs[-1]
                difference = difference.total_seconds()/(60*60)
            values[date] = (row[i]-prior)/difference
            xs.append(date)
            prior = row[i]
        
        return values

    def draw(self, start=0, max_count=10, include=None, included_ids=None):
        # self.sort()

        xs = []
        values = []

        for i in self.dates:
            date = datetime.fromisoformat(i)
            print(date)
            bin = 0


            # Counts out how many users have been displayed.
            count = 0
            for index, row in list(self.data.iterrows())[start:]:
                # print(row)
                if self.exclude_missing and pd.isna(row['Name']):
                    continue
                if include is not None and row['ID'] not in include:
                    continue

                val = self.read_row(row)
                
                # if values[-1]-values[0] < self.active_threshold:
                #     continue

                try:
                    bin += val[date]
                except KeyError:
                    pass
            

                count += 1
                if count >= max_count:
                    break
            xs.append(date)
            values.append(bin)
        plt.plot(xs, values, color='#FFFFFF')

    def configure(self):
        super().configure()
        plt.title("Total activity per hour", color='#FFFFFF')


if __name__ == '__main__':
    data = pd.read_csv("gwaff2.csv", index_col=0)

    plot = TotalGrowth(data, start_date=datetime.now()-timedelta(days=14))
    plot.draw(max_count=10000)
    plot.configure()

    plot.show()
