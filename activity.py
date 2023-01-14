import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from plotter import Plotter

class Activity(Plotter):
    def __init__(self, data, start_date, active_threshold=False, exclude_missing=True):
        super().__init__(data, active_threshold, exclude_missing)
        self.start_date = start_date

    def sort(self):
        data = [self.read_row(row)[1] for index, row in self.data.iterrows()]
        self.data['Change'] = [row[-1] - row[0] for row in data]
        self.data.sort_values(by='Change', inplace=True, ascending=False)

    def read_row(self, row):
        xs = []
        values = []
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
                print('first')
            else:
                difference = date - xs[-1]
                difference = difference.total_seconds()/(60*60)
                print(difference)
            values.append((row[i]-prior)/difference)
            prior = row[i]
            xs.append(date)
        if len(values) <= 1:
            return None, [0,0]
        
        return xs, values

    def annotate(self, seperator=0.03):
        '''
        Adds names to the graph.
        Ensures the names are seperated by at least 'seperator'.

        '''
        for index, item in enumerate(sorted(self.annotations, key=lambda x: x[0])):
            height = item[0]
            plt.annotate(item[1], (1.005, height), (1.005, height),
                         xycoords=('axes fraction', 'data'),
                         color=item[2], va='center')
        self.annotate_image(item[3], height)

    def configure(self):
        super().configure()
        plt.title("Top chatters XP per hour", color='#FFFFFF')
        self.ax.set_ylabel("XP per hour")
        self.ax.set_xlabel("Date (YYYY-MM-DD)", color="white")
        self.ax.set_xlim([self.start_date, datetime.now()])
        # self.ax.set_ylim([0, self.maxxp*1.05])


if __name__ == '__main__':
    data = pd.read_csv("gwaff2.csv", index_col=0)

    plot = Activity(data, start_date=datetime.now()-timedelta(days=7))
    plot.draw()
    plot.annotate(seperator=0.06)
    plot.configure()

    plot.show()
