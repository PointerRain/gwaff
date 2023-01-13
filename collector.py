from urllib.request import Request, urlopen
import requests
import json
import time

import pandas as pd

from datetime import datetime


def request_api(url):
    count = 0
    while True:
        try:
            request = Request(url)
            request.encoding = 'utf-8'
            data = urlopen(request).read()
            return json.loads(data)
        except Exception as e:
            print("Could not retrieve", str(count))
            print(e)
            if count < 10:
                count += 1
                time.sleep(1)
            else:
                raise e
                return


def url_constructor(base, **kwargs):
    if kwargs:
        keys = list(kwargs.keys())
        url = base+'?'+keys[0]+'='+str(kwargs[keys[0]])
        for kw in keys[1:]:
            url += '&'+kw+'='+str(kwargs[kw])
    return url


server = "377946908783673344"
base_url = "https://gdcolon.com/polaris/api/leaderboard/" + server


def record_data(pages=range(1, 6), min_time=2):
    '''
    Record the current xp data to gwaff.csv.
    Ensures records are seperated by at least min_time.
    '''

    ids = []
    names = []
    colours = []
    avatars = []

    xps = {}

    # Open the last copy of the data.
    last = pd.read_csv("gwaff.csv", index_col=0)

    for page in pages:
        url = url_constructor(base_url, page=page)
        print(url)

        data = request_api(url)
        leaderboard = data['leaderboard']

        for member in leaderboard:
            if not 'missing' in member:
                # Save xp and ids
                id = int(member['id'])
                ids.append(id)
                xp = member['xp']
                xps[id] = xp
                # Update names, colours, and avatars
                name = member['nickname'] or member['username']
                last.loc[last['ID'] == id, 'Name'] = name
                colour = member['color']
                last.loc[last['ID'] == id, 'Colour'] = colour
                avatar = member['avatar']
                last.loc[last['ID'] == id, 'Avatar'] = avatar
                # Also append to lists
                names.append(name)
                colours.append(colour)
                avatars.append(avatar)
    print()


    # Below saves the data
    struct = {
        'ID': ids,
        'Name': names,
        'Colour': colours,
        'Avatar': avatars
    }

    lasttime = last.columns[-1]
    lasttime = datetime.fromisoformat(lasttime)
    print("Last:", lasttime)
    now = datetime.now()
    print(" Now:", now)
    difference = now - lasttime
    print("Diff:", difference)
    print()

    # Checks before saving. Could be improved
    if difference.total_seconds() > min_time*60*60:
        other = pd.DataFrame(struct)
        df = pd.concat([last, other])
        df = df.drop_duplicates('ID', keep='first')

        newxp = []
        for index, row in df.iterrows():
            if row['ID'] in xps:
                newxp.append(xps[row['ID']])
            else:
                newxp.append(None)
        df[now] = newxp

        print(df)
        df.to_csv('gwaff.csv', encoding='utf-8')
        print('saved')

    else:
        print('Too soon')
        print(difference.total_seconds()//60, min_time*60)


if __name__ == '__main__':
    # Checks every hour while running
    while True:
        record_data(min_time=2)

        print()
        for i in range(6):
            print("slept", i*10)
            time.sleep(10*60)
        print()
