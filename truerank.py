import os
from datetime import datetime, timedelta
from typing import Any

from gwaff.database.db_base import DatabaseReader

PREDICTOR_DEFAULT_DAYS: int = int(os.environ.get("PREDICTOR_DEFAULT_DAYS", 30))
RANK_DEFAULT_THRESHOLD: int = int(os.environ.get("RANK_DEFAULT_THRESHOLD", 30))


class Truerank:
    def __init__(self, period: int = PREDICTOR_DEFAULT_DAYS,
                 threshold: int = RANK_DEFAULT_THRESHOLD):
        self.period = period
        if period <= 0:
            raise ZeroDivisionError
        self.start_date = datetime.now() - timedelta(days=period)

        self.threshold = threshold

        self.values = self.get_data()

    def get_data(self) -> list[dict[str, Any]]:
        dbr = DatabaseReader()
        data = dbr.get_data_in_range(start_date=self.start_date, limit=200)

        values = []
        for row in data:
            if len(row[2]) <= 1:
                continue
            if row[2][-1] - row[2][0] >= self.threshold:
                values.append({
                    'ID': row[0][0],
                    'name': row[0][1],
                    'colour': row[0][2],
                    'avatar': row[0][3],
                    'xp': row[2][-1]
                })

        return values

    def find_index(self, member: int) -> dict[str, Any]:
        '''
        Find information (crucially index) of the given member.
        Returns: dict
            - User's ID
            - User's index
            - User's server nickname
            - User's XP
            - User's avatar url
            If there is a preceding member
            - Previous' ID
            - Previous' server nickname
            - Previous' XP
        '''
        for index, item in enumerate(self.values):
            if item['ID'] == member:
                result = item
                result['rank'] = index
                if index == 0:
                    return result
                result['other_ID'] = self.values[index - 1]['ID']
                result['other_name'] = self.values[index - 1]['name']
                result['other_xp'] = self.values[index - 1]['xp']
                return result
        raise IndexError


if __name__ == '__main__':
    truerank = Truerank()
    # result = truerank.find_index(344731282095472641)
    result = truerank.get_data()
    print(result)
    result = truerank.find_index(309647479178264579)
    print(result)
