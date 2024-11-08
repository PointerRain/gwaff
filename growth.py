from datetime import datetime, timedelta

from plotter import Plotter
from database import DatabaseReader


class Growth(Plotter):
    def get_data(self, limit: int, include: set[int] = None) -> list[tuple]:
        dbr = DatabaseReader()
        return dbr.get_growth_in_range(self.start_date, limit, include)

    def configure(self) -> None:
        super().configure()

        self.ax.set_ylabel("XP Growth")
        self.ax.set_ylim([0, self.max_xp * 1.05])


if __name__ == '__main__':
    plot = Growth(start_date=datetime.now() - timedelta(days=30))
    plot.draw()
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()
