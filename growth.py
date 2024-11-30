from datetime import datetime, timedelta

from database import DatabaseReader
from plotter import Plotter


class Growth(Plotter):
    def get_data(self, limit: int, include: set[int] = None) -> list[tuple]:
        dbr = DatabaseReader()
        return dbr.get_growth_in_range(self.start_date, self.end_date, limit=limit, include=include)

    def configure(self) -> None:
        super().configure()

        self.ax.set_ylabel("XP Growth")
        self.ax.set_ylim([0, self.max_xp * 1.05])


if __name__ == '__main__':
    # plot = Growth(start_date=datetime(year=2020, month=6, day=28),
    #               end_date=datetime(year=2021, month=3, day=22))
    plot = Growth(start_date=datetime.now() - timedelta(days=7))
    plot.draw()
    plot.draw_events()
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()

# end_date=datetime(year=2021, month=3, day=22)
