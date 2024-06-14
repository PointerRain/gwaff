from __future__ import annotations
import pandas as pd
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from urllib.request import Request, urlopen
from urllib.error import HTTPError

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


def getimg(url: str):
    count = 0
    while True:
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urlopen(request)
        except HTTPError as e:
            print("[WARN][PLOTTER] Could not retrieve", str(count))
            print(url)
            print(e)
            if count < MAX_RETRIES:
                count += 1
            else:
                return None


class Plotter:
    def __init__(self,
                 data: pd.DataFrame,
                 start_date: datetime = None,
                 end_date: datetime = None,
                 active_threshold: int = RANK_DEFAULT_THRESHOLD,
                 exclude_missing: bool = True,
                 special: bool = False,
                 title: str = "XP Over Time"):
        self.data = data

        self.fig, self.ax = plt.subplots()
        self.fig.set_size_inches(*WINDOW_SIZE)

        self.active_threshold = active_threshold
        self.exclude_missing = exclude_missing

        self.dates = data.columns
        self.dates = list(self.dates)[4:]

        self.annotations = []

        self.start_date = start_date
        self.end_date = end_date

        self.special = special
        self.title = title

    def sort(self) -> None:
        # Find final value for xp using the read_row function
        data = [self.read_row(row)[0] for index, row in self.data.iterrows()]
        self.data['Final'] = [row[-1] for row in data]
        self.data.sort_values(by='Final', inplace=True, ascending=False)

    def read_row(self, row: pd.Series) -> tuple[list[int], list[tuple[list[datetime], list[int]]]]:
        '''
        Read dates and values that have xp data.

        Returns:
        Array of all values regardless of 
        Array of all (roughly) continuous lines
        '''
        xs = []
        ys = []
        values = []
        lines = []
        missing = 0
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
                values.append(row[i])
                xs.append(date)
                ys.append(row[i])

        if len(xs) >= 2:
            lines.append((xs, ys))

        if len(values) <= 1:
            return [0, 0], []
        return values, lines

    def draw(self, start: int = 0,
             max_count: int = GRAPH_DEFAULT_USERS,
             include: list[int] = None) -> None:
        '''
        Draws a plot.
        start: the number of users to skip over at the start.
        max_count: the number of users to show.
        include: if specified, only the specified users are shown.
        '''
        self.sort()

        # Counts out how many users have been displayed.
        count = 0
        for index, row in list(self.data.iterrows())[start:]:
            if self.exclude_missing and pd.isna(row['Name']):
                continue
            if include is not None and row['ID'] not in include:
                continue
            if int(row['ID']) in [483515866319945728]:
                continue

            values, lines = self.read_row(row)

            if values[-1] - values[0] <= self.active_threshold:
                continue

            name: str;
            colour: str;
            avatar: str;
            if pd.isna(row['Name']):
                name = ''
                colour = Colours.missing
                avatar = None
            else:
                name = row['Name']
                colour = row['Colour']
                avatar = row['Avatar']

            self.annotations.append(
                (values[-1], name, colour, avatar, values[0]))
            for xs, ys in lines:
                plt.plot(xs, ys, color=colour)

            count += 1
            if count >= max_count:
                break
        if count < max_count:
            print("[PLOTTER] " + str(count) + " shown")

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
        self.ax.set_xlabel("Date (YYYY-MM)", color=Colours.text)
        self.ax.set_ylabel("Total XP", color=Colours.text)

        end = self.end_date or datetime.now()
        self.ax.set_xlim([self.start_date, end])

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
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Plotter(data, start_date=datetime.now() - timedelta(days=365))
    plot.draw()
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()
    plot.close()
