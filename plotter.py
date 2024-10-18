from urllib.error import HTTPError
from urllib.request import Request, urlopen
from matplotlib.dates import DateFormatter
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from database import DatabaseReader
from custom_logger import Logger
logger = Logger('gwaff.plotter')


MAX_RETRIES = 5
WINDOW_SIZE = (15, 7)
GAP_MIN_SIZE = 3
GRAPH_DEFAULT_USERS = 15
GRAPH_SEPERATOR = 0.03
GRAPH_IMAGE_WIDTH = 0.018
RANK_DEFAULT_THRESHOLD = 30


class Colours:
    missing = '#505050'
    text = '#FFFFFF'
    outside = '#2B2D31'
    inside = '#313338'


class ResponsiveDateFormat:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.difference = abs((end_date-start_date).days)
        print(self.difference)
        if self.difference <= 3:
            self.formatter = DateFormatter('%d %H')
        elif self.difference <= 180:
            self.formatter = DateFormatter('%y-%m-%d')
        elif self.difference <= 365:
            self.formatter = DateFormatter('%Y-%m')
        else:
            self.formatter = DateFormatter('%Y-%m')

    def __str__(self):
        if self.difference <= 3:
            return 'DD HH AEST'
        elif self.difference <= 7:
            return 'YY-MM-DD AEST'
        elif self.difference <= 180:
            return 'YY-MM-DD'
        elif self.difference <= 365:
            return 'YYYY-MM'
        else:
            return 'YYYY-MM'


def getimg(url: str):
    count = 0
    while True:
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urlopen(request)
        except Exception as e:
            logger.warning(f"Could not retrieve image {url} {str(count)} {e}")
            if count < MAX_RETRIES:
                count += 1
            else:
                return None


class Plotter:
    def __init__(self,
                 start_date: datetime = None,
                 end_date: datetime = None,
                 active_threshold: int = RANK_DEFAULT_THRESHOLD,
                 special: bool = False,
                 title: str = "XP Over Time"):

        self.fig, self.ax = plt.subplots()
        self.fig.set_size_inches(*WINDOW_SIZE)

        self.active_threshold = active_threshold

        self.annotations = []

        self.start_date = start_date
        self.end_date = end_date

        self.special = special
        self.title = title

    def get_data(self, limit):
        dbr = DatabaseReader()
        return dbr.get_data_in_range(self.start_date, limit=limit)

    def draw(self, start: int = 0,
             max_count: int = GRAPH_DEFAULT_USERS,
             include: list[int] = None) -> None:
        count = 0

        for profile, xs, ys in self.get_data(max_count):
            if include is not None and row['ID'] not in include:
                continue
            if len(xs) <= 1:
                continue

            id, name, colour, avatar = profile
            print(ys)
            self.annotations.append(
                (ys[-1], name, colour, avatar, ys[0]))
            plt.plot(xs, ys, color=colour)

            count += 1
            if count >= max_count:
                break
        if count < max_count:
            logger.info(f"{count} shown")

    def annotate(self) -> None:
        '''
        Adds names to the graph.
        Ensures the names are seperated by at least 'GRAPH_SEPERATOR'.
        '''
        # Determine how to convert from xp to axes fraction.
        self.maxxp = sorted(self.annotations, key=lambda x: x[0])[-1][0]
        self.minxp = sorted(self.annotations, key=lambda x: x[4])[0][4]
        if len(self.annotations) > 1:

            def xp_to_axes(xp):
                return (xp - self.minxp) / (self.maxxp - self.minxp)

            def axes_to_data(h):
                return h * (self.maxxp - self.minxp) + self.minxp

        # Each point defaults to next to line.
        # Moves up to avoid lower labels.
        heights = [-GRAPH_SEPERATOR]
        for index, item in enumerate(
                sorted(self.annotations, key=lambda x: x[0])):
            height = item[0]
            # position = 1.019
            position = 1.001 + GRAPH_IMAGE_WIDTH
            new_height = height
            if len(self.annotations) > 1:
                new_height = xp_to_axes(height)
                if new_height - heights[-1] < GRAPH_SEPERATOR:
                    new_height = heights[-1] + GRAPH_SEPERATOR
                heights.append(new_height)
                new_height = axes_to_data(new_height)
            did_img = self.annotate_image(item[3], new_height)
            if not did_img:
                position -= GRAPH_IMAGE_WIDTH
            plt.annotate(item[1], (position, height), (position, new_height),
                         xycoords=('axes fraction', 'data'),
                         color=item[2],
                         va='center')

    def annotate_image(self, avatar: str, height: float) -> bool:
        '''
        Add an image at the given height.
        avatar: str url to the avatar image.
        height: height in data units to position the image.

        Returns: bool representing if the image was added successfully.
        '''
        image = getimg(avatar)
        if image is None:
            return False
        image = plt.imread(image, format='jpeg')
        image = OffsetImage(image, zoom=0.1)
        annotation = AnnotationBbox(image, (1 + GRAPH_IMAGE_WIDTH/2, height),
                                    xycoords=('axes fraction', 'data'),
                                    frameon=False)
        self.ax.add_artist(annotation)
        return True

    def configure(self) -> None:

        end = self.end_date or datetime.now()
        self.ax.set_xlim([self.start_date, end])

        dateformat = ResponsiveDateFormat(self.start_date, end)
        self.ax.xaxis.set_major_formatter(dateformat.formatter)

        self.ax.set_xlabel(f"Date ({str(dateformat)})", color=Colours.text)
        self.ax.set_ylabel("Total XP", color=Colours.text)

        # self.fig.figure(facecolor='')
        self.fig.patch.set_facecolor(Colours.outside)
        self.ax.set_facecolor(Colours.inside)

        plt.grid(visible=True, axis='y', color=Colours.outside)

        self.ax.tick_params(color=Colours.text, labelcolor=Colours.text)
        for spine in self.ax.spines.values():
            # spine.set_edgecolor(Colours.inside)
            spine.set_visible(False)

        self.fig.subplots_adjust(left=0.06, bottom=0.08, top=0.94, right=0.83)

        if self.title:
            plt.title(self.title, color=Colours.text)

    def show(self):
        plt.show()

    def save(self, name="out.png"):
        plt.savefig(name)

    def close(self):
        plt.close()


if __name__ == '__main__':
    plot = Plotter(start_date=datetime.now() - timedelta(days=365))
    plot.draw()
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()
    plot.close()
