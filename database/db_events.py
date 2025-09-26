from datetime import datetime, timedelta

from gwaff.database.db_base import BaseDatabase
from gwaff.database.structs import *

EVENT_SIZE_THRESHOLD = 0.01


class EventExistsError(Exception):
    """
    Thrown when an event already exists.
    """
    pass


class DatabaseEvents(BaseDatabase):
    def get_current_event(self) -> Event:
        """
        Returns the current event.
        """
        return self.session.query(Event).filter_by(end_time=None).first()

    def create_event(self, start_time, end_time=None, multiplier: float = None) -> None:
        """
        Creates a new event with the given start_time, end_time, and multiplier.
        """
        if self.get_current_event():
            raise EventExistsError("There is already an event in progress.")

        new_event = Event(start_time=start_time, end_time=end_time, multiplier=multiplier)
        self.session.add(new_event)
        self.session.commit()

    def end_event(self, end_time) -> None:
        """
        Ends the oldest event with the given end_time.
        """
        event = self.get_current_event()
        event.end_time = end_time
        self.session.commit()

    def get_events(self) -> list[Event]:
        """
        Gets all events.
        """
        return self.session.query(Event).all()

    def get_events_in_range(self, start_date, end_date=None):
        """
        Gets all events in the given date range.
        """
        if end_date is None:
            end_date = datetime.now()

        events = self.session.query(Event).filter(Event.start_time <= end_date).all()
        output = []
        for event in events:
            if event.end_time is not None and event.end_time < start_date:
                continue

            if (event.end_time is not None and
                    event.end_time - event.start_time <= EVENT_SIZE_THRESHOLD * (
                            end_date - start_date)):
                continue
            output.append(event)
        return output


if __name__ == '__main__':
    dbe = DatabaseEvents()

    # dbe.create_event(datetime.now(), multiplier=1.5)
    # dbe.end_event(datetime.now() + timedelta(hours=24))
    # dbe.create_event(datetime.now(), multiplier=2)
    # dbe.end_event(datetime.now() + timedelta(hours=1))
    #
    # # print(dbe.get_events())
    #
    # print(dbe.get_current_event())
    # dbe.end_event(datetime.now())
    # print(dbe.get_current_event())
    events = dbe.get_events_in_range(datetime.now() - timedelta(days=7),
                                     datetime.now() + timedelta(days=3))
    print(len(events))
    for event in events:
        print(event)
