import pandas as pd
from datetime import datetime

import matplotlib.pyplot as plt

from matplotlib.cbook import get_sample_data
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.dates import DateFormatter
from PIL import Image
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
    def __init__(self, data, start_date=None, active_threshold=True, exclude_missing=True):
        self.data = data

        self.fig, self.ax = plt.subplots()

        self.active_threshold = active_threshold
        self.exclude_missing = exclude_missing

        self.dates = data.columns
        self.dates = list(self.dates)[4:]

        self.annotations = {}

        self.start_date = start_date

    def sort(self):
        # Find final value for xp using the read_row function
        data = [self.read_row(row)[1] for index, row in self.data.iterrows()]
        self.data['Final'] = [row[-1] for row in data]
        self.data.sort_values(by='Final', inplace=True, ascending=False)
        print(self.data.head())

    def read_row(self, row, start_date=None):
        xs = []
        values = []
        for i in self.dates:
            date = datetime.fromisoformat(i)
            if self.start_date and date < self.start_date:
                continue
            if row[i] is None or pd.isna(row[i]):
                continue

            values.append(row[i])
            xs.append(date)
        if len(values) <= 1:
            return None, [0,0]

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
            
            if values[-1]-values[0] <= self.active_threshold:
                continue

            if pd.isna(row['Name']):
                name = ''
                colour = '#505050'
                avatar = None
            else:
                name = row['Name']
                colour = row['Colour']
                avatar = row['Avatar']

            self.annotations[values[-1]] = (name, colour, avatar, values[0])
            plt.plot(xs, values, color=colour)

            count += 1
            if count >= max_count:
                break

    def annotate(self, seperator=0.03):
        '''
        Adds names to the graph.
        Ensures the names are seperated by at least 'seperator'.

        '''
        # Determine how to convert from xp to axes fraction.
        print(self.annotations)
        self.maxxp = sorted(self.annotations)[-1]
        self.minxp = sorted(self.annotations)[0]
        if len(self.annotations) > 1:
            def xp_to_axes(xp): return (xp-self.minxp)/(self.maxxp-self.minxp)
            def axes_to_data(h): return h*(self.maxxp-self.minxp)+self.minxp

        # Each point defaults to next to line.
        # Moves up to avoid lower labels.
        heights = [-seperator]
        for index, key in enumerate(sorted(self.annotations)):
            height = key
            if len(self.annotations) > 1:
                height = xp_to_axes(key)
                if height - heights[-1] < seperator:
                    height = heights[-1] + seperator
                heights.append(height)
                height = axes_to_data(height)
            # print(self.annotations[key][0])
            plt.annotate(self.annotations[key][0], (1.005, height), (1.005, height),
                         xycoords=('axes fraction', 'data'),
                         color=self.annotations[key][1], va='center')
            self.annotate_image(self.annotations[key][2], height)

    def annotate_image(self, avatar, height):
        image = getimg(avatar)
        if image is None:
            return
        image = plt.imread(image, format='jpeg')
        self.ax.add_artist(AnnotationBbox(OffsetImage(image, zoom=0.1), (0.993, height),
                           xycoords=('axes fraction', 'data'), frameon=False))


    def configure(self):
        self.ax.set_xlabel("Date (YYYY-MM-DD)", color="white")
        self.ax.set_ylabel("Total XP", color="white")

        # date_form = DateFormatter("%d-%m")
        # self.ax.xaxis.set_major_formatter(date_form)

        # self.fig.figure(facecolor='')
        self.fig.patch.set_facecolor('#2F3136')
        self.ax.set_facecolor('#36393F')

        self.ax.tick_params(color='#FFFFFF', labelcolor='#FFFFFF')
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#36393F')

        self.fig.subplots_adjust(left=0.05, bottom=0.08, top=0.94, right=0.84)

    def show(self): plt.show()


if __name__ == '__main__':
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Plotter(data)
    plot.sort()
    plot.draw(max_count=10, include=[344731282095472641,974288645047599164])
    plot.annotate(seperator=0.03)
    plot.configure()

    # im = plt.imread(get_sample_data())
    

    plt.show()

