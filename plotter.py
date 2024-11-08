import os.path
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager, FontProperties
from matplotlib.dates import DateFormatter
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from custom_logger import Logger
from database import DatabaseReader
from utils import request_img

logger = Logger('gwaff.plotter')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRIMARY_FONT_PATH = os.path.join(BASE_DIR, 'assets/gg sans Semibold.ttf')
EMOJI_FONT_PATH = os.path.join(BASE_DIR, 'assets/NotoEmoji-Regular.ttf')
fontManager.addfont(PRIMARY_FONT_PATH)  # gg sans
fontManager.addfont(EMOJI_FONT_PATH)  # Noto Emoji

p_font = FontProperties(fname=PRIMARY_FONT_PATH)
e_font = FontProperties(fname=EMOJI_FONT_PATH)

fonts = [FontProperties(fname=PRIMARY_FONT_PATH).get_name(),
         FontProperties(fname=EMOJI_FONT_PATH).get_name()]

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = fonts + plt.rcParams['font.sans-serif']

MAX_RETRIES = 5
WINDOW_SIZE = (15, 7)
GAP_MIN_SIZE = 3
GRAPH_DEFAULT_USERS = 15
GRAPH_SEPERATOR = 0.03
GRAPH_IMAGE_WIDTH = 0.018
RANK_DEFAULT_THRESHOLD = 30


class Colours:
    """
    A class to hold color constants used in the plot.
    """
    missing = '#505050'
    text = '#FFFFFF'
    outside = '#2B2D31'
    inside = '#313338'


class ResponsiveDateFormat:
    """
    A class to determine the date format based on the range of dates.

    Attributes:
        start_date (datetime): The start date of the range.
        end_date (datetime): The end date of the range.
        difference (int): The difference in days between start_date and end_date.
        formatter (DateFormatter): The date formatter based on the difference.
    """

    def __init__(self, start_date, end_date):
        """
        Initializes the ResponsiveDateFormat with start and end dates.

        Args:
            start_date (datetime): The start date of the range.
            end_date (datetime): The end date of the range.
        """
        self.start_date = start_date
        self.end_date = end_date
        self.difference = abs((end_date - start_date).days)

        if self.difference <= 3:
            self.formatter = DateFormatter('%d %H')
        elif self.difference <= 180:
            self.formatter = DateFormatter('%y-%m-%d')
        elif self.difference <= 365:
            self.formatter = DateFormatter('%Y-%m')
        else:
            self.formatter = DateFormatter('%Y-%m')

    def __str__(self):
        """
        Returns a string representation of the date format.

        Returns:
            str: The date format as a string.
        """
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


class Plotter:
    """
    A class to create and manage plots of XP data over time.

    Attributes:
        fig (Figure): The matplotlib figure object.
        ax (Axes): The matplotlib axes object.
        active_threshold (int): The threshold for active users.
        annotations (list): A list to store annotations.
        start_date (datetime): The start date for the plot.
        end_date (datetime): The end date for the plot.
        special (bool): A flag for special plots.
        title (str): The title of the plot.
    """

    def __init__(self,
                 start_date: datetime = None,
                 end_date: datetime = None,
                 active_threshold: int = RANK_DEFAULT_THRESHOLD,
                 special: bool = False,
                 title: str = "XP Over Time"):
        """
        Initializes the Plotter with optional parameters.

        Args:
            start_date (datetime, optional): The start date for the plot. Defaults to None.
            end_date (datetime, optional): The end date for the plot. Defaults to None.
            active_threshold (int, optional): The threshold for active users. Defaults to RANK_DEFAULT_THRESHOLD.
            special (bool, optional): A flag for special plots. Defaults to False.
            title (str, optional): The title of the plot. Defaults to "XP Over Time".
        """
        self.fig, self.ax = plt.subplots(figsize=WINDOW_SIZE)

        self.active_threshold = active_threshold

        self.annotations = []

        self.start_date = start_date
        self.end_date = end_date

        self.special = special
        self.title = title

        self.max_xp = 0
        self.min_xp = 0

    def get_data(self, limit: int, include: set[int] = None) -> list:
        """
        Retrieves data from the database within the specified range.

        Args:
            limit (int): The maximum number of data points to retrieve.
            include (list[int], optional): A list of user IDs to include. Defaults to None.

        Returns:
            list: The data retrieved from the database.
        """
        dbr = DatabaseReader()
        return dbr.get_data_in_range(self.start_date, limit, include)

    def draw(self, start: int = 0,
             limit: int = GRAPH_DEFAULT_USERS,
             include: set[int] = None) -> None:
        """
        Draws the plot with the specified parameters.

        Args:
            start (int, optional): The starting index for data. Defaults to 0.
            limit (int, optional): The maximum number of users to plot. Defaults to GRAPH_DEFAULT_USERS.
            include (list[int], optional): A list of user IDs to include. Defaults to None.
        """
        max_count = limit if not include else len(include)

        count: int = 0
        for profile, xs, ys in self.get_data(max_count, include):
            id, name, colour, avatar = profile

            if include and id not in include:
                continue
            if len(xs) <= 1:
                continue
            if id in {1013000925385871451, 479575918600388609, 1115004793224704070,
                      1230458949308776498}:
                ys = [round(0.9 * y) for y in ys]

            self.annotations.append(
                (ys[-1], name, colour, avatar, ys[0]))
            plt.plot(xs, ys, color=colour)

            count += 1
            if count >= max_count:
                break
        if count < max_count:
            logger.info(f"{count} profiles shown")

    def annotate(self) -> None:
        """
        Adds names to the graph.
        Ensures the names are separated by at least 'GRAPH_SEPERATOR'.
        Requires at least 1 annotation.
        """
        # Determine how to convert from xp to axes fraction.
        sorted_annotations = sorted(self.annotations, key=lambda x: x[0])
        self.max_xp = sorted_annotations[-1][0]
        self.min_xp = sorted_annotations[0][4]

        if len(self.annotations) > 1:
            def xp_to_axes(xp):
                return (xp - self.min_xp) / (self.max_xp - self.min_xp)

            def axes_to_data(h):
                return h * (self.max_xp - self.min_xp) + self.min_xp

        # Each point defaults to next to line.
        # Moves up to avoid lower labels.
        heights = [-GRAPH_SEPERATOR]
        for item in sorted_annotations:
            height = item[0]
            position = 1.001 + GRAPH_IMAGE_WIDTH

            if len(self.annotations) > 1:
                label_height = xp_to_axes(height)
                if label_height - heights[-1] < GRAPH_SEPERATOR:
                    label_height = heights[-1] + GRAPH_SEPERATOR
                heights.append(label_height)
                label_height = axes_to_data(label_height)
            else:
                label_height = height

            did_img = self.annotate_image(item[3], label_height)

            label_position = position if did_img else position - GRAPH_IMAGE_WIDTH

            plt.annotate(item[1], (position, height),
                         xytext=(label_position, label_height),
                         xycoords=('axes fraction', 'data'),
                         color=item[2],
                         va='center',
                         family=fonts)

    def annotate_image(self, avatar: str, height: float) -> bool:
        """
        Adds an image at the given height.

        Args:
            avatar (str): URL to the avatar image.
            height (float): Height in data units to position the image.

        Returns:
            bool: True if the image was added successfully, False otherwise.
        """
        image = request_img(avatar)
        if image is None:
            return False

        image = plt.imread(image, format='jpeg')
        image = OffsetImage(image, zoom=0.1)
        annotation = AnnotationBbox(image, (1 + GRAPH_IMAGE_WIDTH / 2, height),
                                    xycoords=('axes fraction', 'data'),
                                    frameon=False)
        self.ax.add_artist(annotation)
        return True

    def configure(self) -> None:
        """
        Configures the plot with labels, colors, and other settings.
        """
        end = self.end_date or datetime.now()
        self.ax.set_xlim([self.start_date, end])

        dateformat = ResponsiveDateFormat(self.start_date, end)
        self.ax.xaxis.set_major_formatter(dateformat.formatter)

        self.ax.set_xlabel(f"Date ({str(dateformat)})", color=Colours.text)
        self.ax.set_ylabel("Total XP", color=Colours.text)

        self.fig.patch.set_facecolor(Colours.outside)
        self.ax.set_facecolor(Colours.inside)
        self.ax.tick_params(colors=Colours.text)

        for spine in self.ax.spines.values():
            spine.set_visible(False)
        plt.grid(visible=True, axis='y', color=Colours.outside)

        self.fig.subplots_adjust(left=0.06, bottom=0.08, top=0.94, right=0.83)

        if self.title:
            plt.title(self.title, color=Colours.text)

    def show(self):
        """
        Displays the plot.
        """
        plt.show()

    def save(self, name="out.png"):
        """
        Saves the plot to a file.

        Args:
            name (str, optional): The name of the file. Defaults to "out.png".
        """
        name = os.path.join(BASE_DIR, 'generated', name)
        plt.savefig(name)
        return name

    def close(self):
        """
        Closes the plot.
        """
        plt.close()


if __name__ == '__main__':
    plot = Plotter(start_date=datetime.now() - timedelta(days=365))
    plot.draw()
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()
    plot.close()