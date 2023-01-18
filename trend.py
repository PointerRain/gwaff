import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from plotter import Plotter

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

class Trend(Plotter):
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


            m = (values[-1]-values[0])/((xs[-1]-xs[0]).total_seconds()/(60*60))
            print(m)
            c = values[-1]

            # y = np.linspace(0,10,120)
            x = list(range(0,1000,10))
            y = [24*m*v+c for v in x]

            if pd.isna(row['Name']):
                name = ''
                colour = '#505050'
                avatar = None
            else:
                name = row['Name']
                colour = row['Colour']
                avatar = row['Avatar']

            self.annotations.append((values[-1], name, colour, avatar, values[0]))
            plt.plot(x, y, color=colour)

            count += 1
            if count >= max_count:
                break

        def configure(self):
            super().configure()
            self.ax.set_ylim([0, 1899250])


if __name__ == '__main__':
    data = pd.read_csv("gwaff.csv", index_col=0)

    plot = Trend(data, start_date=datetime.now()-timedelta(days=7))
    plot.draw(max_count=20)
    plot.annotate()
    plot.configure()

    # im = plt.imread(get_sample_data())
    

    plot.show()

