import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from growth import Growth
from plotter import Plotter


class Ranking(Growth):
    def sort(self):
        # Find final value for xp using the read_row function
        data = [Plotter.read_row(self, row)[1] for index, row in self.data.iterrows()]
        self.data['Final'] = [row[-1] for row in data]
        self.data.sort_values(by='Final', inplace=True, ascending=False)

    def draw(self, start=0, max_count=500, include=None, included_ids=None):
        self.sort()

        xs = []
        values = []

        # Counts out how many users have been displayed.
        count = 1
        for index, row in list(self.data.iterrows())[start:]:
            if self.exclude_missing and pd.isna(row['Name']):
                continue
            if include is not None and row['ID'] not in include:
                continue

            xs.append(count)
            values.append(self.read_row(row)[1][-1])
            
            if values[-1]-values[0] <= self.active_threshold:
                continue

            self.annotations.append((values[-1], None, None, None, None))

            count += 1
            if count >= max_count:
                break
        print(xs, values)
        plt.plot(xs, values, color='#FFFFFF')

    def annotate(self):
        # Determine maxxp.
        self.maxxp = sorted(self.annotations, key=lambda x: x[0])[-1][0]
        # self.minxp = sorted(self.annotations, key=lambda x: x[4])[0][-1]

    def configure(self):
        super().configure()
        plt.title("Top chatters XP growth", color='#FFFFFF')
        self.ax.set_ylabel("XP Growth")
        self.ax.set_xlabel("Ranking", color="white")
        self.ax.set_xlim([1, 100])
        self.ax.set_ylim([0, self.maxxp*1.05])

if __name__ == '__main__':
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Ranking(data, start_date=datetime.now()-timedelta(days=7))
    plot.draw(max_count=100)
    plot.annotate()
    plot.configure()

    plot.show()
