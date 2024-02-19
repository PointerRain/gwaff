import pandas as pd
from datetime import datetime, timedelta

from plotter import Plotter

GAP_MIN_SIZE = 3


class Growth(Plotter):
    def sort(self):
        data = [self.read_row(row)[0] for index, row in self.data.iterrows()]
        self.data['Change'] = [row[-1] - row[0] for row in data]
        self.data.sort_values(by='Change', inplace=True, ascending=False)

    def read_row(self, row: pd.Series) -> tuple[list[int], list[tuple[list[datetime], list[int]]]]:
        '''
        Read dates and values that have xp data.
        '''
        xs = []
        ys = []
        values = []
        lines = []
        missing = 0

        startval = None
        for i in self.dates:
            date = datetime.fromisoformat(i)
            if self.start_date and date < self.start_date:
                continue
            if self.end_date and date > self.end_date:
                continue

            if row[i] is None or pd.isna(row[i]):
                missing += 1
                if missing >= GAP_MIN_SIZE and len(xs) >= 2:
                    lines.append((xs, ys))
                    xs = []
                    ys = []
                    missing = 0
            else:
                missing = 0
                startval = startval or row[i]
                values.append(row[i] - startval)
                xs.append(date)
                ys.append(row[i] - startval)

        if len(xs) >= 2:
            lines.append((xs, ys))

        if len(values) <= 1:
            return [0, 0], []

        return values, lines

    def configure(self) -> None:
        super().configure()

        self.ax.set_ylabel("XP Growth")
        self.ax.set_ylim([0, self.maxxp * 1.05])


if __name__ == '__main__':
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Growth(data, start_date=datetime.now() - timedelta(days=7))
    plot.draw()
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()
