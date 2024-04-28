# from replit import db
import pandas as pd

info = ['Name', 'Colour', 'Avatar']

def saveToDB(mode="quick") -> None:
    '''
    Saves the csv to a replit database.
    mode:
      - quick: only saves new columns and personal info (default)
      - minimal: only saves new columns
      - full: saves all columns and personal info
    '''
    # data = pd.read_csv("gwaff.csv", index_col='ID')
    # db_cols = db.keys()

    # dict_form = data.to_dict()

    # for key in dict_form:
    #     if mode == 'quick':
    #         if key not in info and key in db_cols:
    #             continue
    #     elif mode == 'minimal':
    #         if key in db_cols:
    #             continue
    #     db[key] = dict_form[key]
    pass


def loadFromDB() -> None:
    '''
    Loads the csv from a replit database.
    '''
    # struct = {}
    # keys = list(db.keys())
    # keys.sort()
    # keys = info + keys[:-4]
    # struct['ID'] = list(db['2023-01-02 03:05:56.141261'].keys())
    # struct.update({i: list(db[i].values()) for i in keys})
    # df = pd.DataFrame.from_dict(struct)
    # df.to_csv('gwaff.csv', encoding='utf-8')
    pass