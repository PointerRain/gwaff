from flask import Flask
from threading import Thread
import random
# from datetime import datetime, timedelta
# from pandas import read_csv

# from growth import Growth

app = Flask('')


@app.route('/')
def home():
    # data = read_csv("gwaff.csv", index_col=0)
    # plot = Growth(data, start_date=datetime.now() - timedelta(days=7))
    # plot.draw()
    # plot.annotate()
    # plot.configure()
    # plot.save('static/images/out.png')
    # plot.close()

    return "I'm in"


def run():
    app.run(host='0.0.0.0', port=random.randint(2000, 9000))


def keep_alive():
    '''
	Creates and starts new thread that runs the function run.
	'''
    t = Thread(target=run)
    t.start()
