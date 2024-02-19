from replit import db
import pandas as pd


def saveToDB() -> None:
    data = pd.read_csv("gwaff.csv", index_col='ID')
    data_cols = data.columns
    db_cols = db.keys()

    dict_form = data.to_dict()

    for key in dict_form:
        db[key] = dict_form[key]

    # for key in db_cols:
    #     if key not in data_cols:
    #         del db[key]


def loadFromDB() -> None:
    struct = {}
    keys = list(db.keys())

    control = ['Name', 'Colour', 'Avatar']
    keys = [x for x in keys if x not in control]
    keys.sort()
    keys = control + keys[:-1]

    struct['ID'] = db['2023-01-02 03:05:56.141261'].keys()

    for i in keys:
        struct[i] = db[i].values()
    df = pd.DataFrame.from_dict(struct)
    df.to_csv('gwaff.csv', encoding='utf-8')


# For col in db
# Add to new csv
