import pandas as pd
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def getimg(url):
    count = 0
    while True:
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urlopen(request)
        except HTTPError as e:
            print("Could not retrieve", str(count))
            print(url)
            print(e)
            if count < 10:
                count += 1
            else:
                return None


class Plotter:
    def __init__(self,
                 data,
                 start_date=None,
                 end_date=None,
                 active_threshold=True,
                 exclude_missing=True,
                 special=False,
        self.data = data

        self.fig, self.ax = plt.subplots()
        self.fig.set_size_inches(15, 7)

        self.active_threshold = active_threshold
        self.exclude_missing = exclude_missing

        self.dates = data.columns
        self.dates = list(self.dates)[4:]

        self.annotations = []

        self.start_date = start_date
        self.end_date = end_date

        self.special = special

    def sort(self):
        # Find final value for xp using the read_row function
        data = [self.read_row(row)[1] for index, row in self.data.iterrows()]
        self.data['Final'] = [row[-1] for row in data]
        self.data.sort_values(by='Final', inplace=True, ascending=False)

    def read_row(self, row):
        '''
        Read dates and values that have xp data.
        '''
        xs = []
        values = []
        for i in self.dates:
            date = datetime.fromisoformat(i)
            if self.start_date and date < self.start_date:
                continue
            if self.end_date and date > self.end_date:
                continue
            if row[i] is None or pd.isna(row[i]):
                continue

            values.append(row[i])
            xs.append(date)
        if len(values) <= 1:
            return None, [0, 0]

        return xs, values

    def draw(self, start=0, max_count=10, include=None, included_ids=None):
        self.sort()

        # Counts out how many users have been displayed.
        count = 0
        for index, row in list(self.data.iterrows())[start:]:
            if self.exclude_missing and pd.isna(row['Name']):
                continue
            if include is not None and row['ID'] not in include:
                continue

            xs, values = self.read_row(row)

            if values[-1] - values[0] <= self.active_threshold:
                continue

            if pd.isna(row['Name']):
                name = ''
                colour = '#505050'
                avatar = None
            else:
                name = row['Name']
                colour = row['Colour']
                avatar = row['Avatar']

            self.annotations.append(
                (values[-1], name, colour, avatar, values[0]))
            plt.plot(xs, values, color=colour)

            count += 1
            if count >= max_count:
                break
        if count < max_count:
            print(str(count) + " shown")

    def annotate(self, seperator=0.03):
        '''
        Adds names to the graph.
        Ensures the names are seperated by at least 'seperator'.

        '''
        # Determine how to convert from xp to axes fraction.
        self.maxxp = sorted(self.annotations, key=lambda x: x[0])[-1][0]
        self.minxp = sorted(self.annotations, key=lambda x: x[4])[0][-1]
        if len(self.annotations) > 1:

            def xp_to_axes(xp):
                return (xp - self.minxp) / (self.maxxp - self.minxp)

            def axes_to_data(h):
                return h * (self.maxxp - self.minxp) + self.minxp

        # Each point defaults to next to line.
        # Moves up to avoid lower labels.
        heights = [-seperator]
        for index, item in enumerate(
                sorted(self.annotations, key=lambda x: x[0])):
            height = item[0]
            position = 1.019
            new_height = height
            if len(self.annotations) > 1:
                new_height = xp_to_axes(height)
                if new_height - heights[-1] < seperator:
                    new_height = heights[-1] + seperator
                heights.append(new_height)
                new_height = axes_to_data(new_height)
            did_img = self.annotate_image(item[3], new_height)
            if not did_img:
                position -= 0.015
            plt.annotate(item[1], (position, height), (position, new_height),
                         xycoords=('axes fraction', 'data'),
                         color=item[2],
                         va='center')

    def annotate_image(self, avatar, height):
        image = getimg(avatar)
        if image is None:
            return False
        image = plt.imread(image, format='jpeg')
        self.ax.add_artist(
            AnnotationBbox(OffsetImage(image, zoom=0.1), (1.008, height),
                           xycoords=('axes fraction', 'data'),
                           frameon=False))
        return True

    def configure(self):
        self.ax.set_xlabel("Date (YYYY-MM-DD AEST)", color="white")
        self.ax.set_ylabel("Total XP", color="white")

        if self.end_date:
            end = min(datetime.now(), self.end_date)
        else:
            end = datetime.now()
        self.ax.set_xlim([self.start_date, end])

        # date_form = DateFormatter("%d-%m")
        # self.ax.xaxis.set_major_formatter(date_form)

        # self.fig.figure(facecolor='')
        self.fig.patch.set_facecolor('#2F3136')
        self.ax.set_facecolor('#36393F')

        self.ax.tick_params(color='#FFFFFF', labelcolor='#FFFFFF')
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#36393F')

        self.fig.subplots_adjust(left=0.05, bottom=0.08, top=0.94, right=0.82)


    def show(self):
        plt.show()

    def save(self, name="out.png"):
        plt.savefig(name)

    def close(self):
        plt.close()


if __name__ == '__main__':
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Plotter(data,
                   start_date=datetime.now() - timedelta(days=30),
                   active_threshold=True)
    plot.draw(max_count=15)
    plot.annotate()
    plot.configure()

    plot.save()
    plot.show()
    plot.close()
