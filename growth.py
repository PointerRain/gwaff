from datetime import datetime, timedelta

from plotter import Plotter
from database import DatabaseReader

class Growth(Plotter):
    def get_data(self, limit):
        dbr = DatabaseReader()
        return dbr.get_growth_in_range(self.start_date)

    def configure(self) -> None:
        super().configure()

        self.ax.set_ylabel("XP Growth")
        self.ax.set_ylim([0, self.maxxp * 1.05])


if __name__ == '__main__':
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Growth(data, start_date=datetime.now() - timedelta(days=30))
    plot.draw()
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()
