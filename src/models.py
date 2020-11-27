from sqlalchemy import create_engine, Integer, Float, String, Column, ForeignKey, PrimaryKeyConstraint, func, text, desc
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True) # User ID
    email = Column(String(50))
    password = Column(String(128))

    def __repr__(self):
        return "<User(user_id={0}, email={1}, password={2}>".format(self.user_id, self.email, self.password)


class Administrator(Base):
    __tablename__ = 'administrators'

    admin_id = Column(Integer, primary_key=True) # User ID
    email = Column(String(50))
    password = Column(String(128))

    def __repr__(self):
        return "<User(admin_id={0}, email={1}, password={2}>".format(self.admin_id, self.email, self.password)


class SubwayStation:
    '''
    Nodes on the graph
    '''
    def __init__(self, station_name=None, entrances=None, lines=None, status=None):
        self._station_name = station_name
        self._entrances = entrances
        self._lines = lines
        self._status = status # "Normal" or "Out of Order"

    @property
    def station_name(self):
        return self._station_name

    @station_name.setter
    def station_name(self, value):
        self._station_name = value
        return self

    @property
    def entrances(self):
        return self._entrances

    @entrances.setter
    def entrances(self, value):
        self._entrances = value
        return self

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, value):
        self._lines = value
        return self

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        return self

    def append_line(self, line):
        self._lines.append(line)
        return self

    def remove_line(self, line):
        self._lines = [x for x in self._lines if x != line]
        return self





class TrainLine:
    '''
    Edges on the graph
    '''
    def __init__(self, start, stop, line):
        self._start = start
        self._stop = stop
        self._line = line

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = value
        return self

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value
        return self

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, value):
        self._line = value
        return self

    def __repr__(self):
        return "<TrainLine(start={0}, stop={1}, line={2})>".format(self.start, self.stop, self.line)

class Schedule:

    def __init__(self,
                 start_station: str,
                 stop_station: str,
                 depart,
                 arrive):
        self.start_station = start_station
        self. stop_station = stop_station
        self.depart = depart
        self.arrive = arrive

    def get_cost(self):
        return self.arrive-self.depart
