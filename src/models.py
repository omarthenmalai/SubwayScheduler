from __future__ import annotations
from sqlalchemy import create_engine, Integer, Float, String, Column, ForeignKey, PrimaryKeyConstraint, func, text, desc
from sqlalchemy.ext.declarative import declarative_base
from neo4j.graph import Node
import numpy as np

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)  # User ID
    email = Column(String(50))
    password = Column(String(128))

    def __repr__(self):
        return "<User(user_id={0}, email={1}, password={2}>".format(self.user_id, self.email, self.password)


class Administrator(Base):
    __tablename__ = 'administrators'

    admin_id = Column(Integer, primary_key=True)  # User ID
    email = Column(String(50))
    password = Column(String(128))

    def __repr__(self):
        return "<User(admin_id={0}, email={1}, password={2}>".format(self.admin_id, self.email, self.password)


class SubwayStation:
    '''
    Nodes on the graph
    '''

    def __init__(self,
                 station_name: str = None,
                 borough: str = None,
                 entrances: str = None,
                 lines: list = None,
                 status: str = None,
                 latitude: float = None,
                 longitude: float = None) -> SubwayStation:
        self._station_name = station_name
        self._entrances = entrances
        self._lines = lines
        self._status = status  # "Normal" or "Out of Order"
        self._borough = borough
        self._latitude = latitude
        self._longitude = longitude

    @property
    def station_name(self):
        return self._station_name

    @station_name.setter
    def station_name(self, value):
        self._station_name = value
        return self

    @property
    def borough(self):
        return self._borough

    @borough.setter
    def borough(self, value: str):
        self._borough = value
        return self

    @property
    def entrances(self):
        return self._entrances

    @entrances.setter
    def entrances(self, value: str):
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

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        self._latitude = value
        return self

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        self._longitude = value
        return self

    def append_line(self, line):
        self._lines.append(line)
        return self

    def remove_line(self, line):
        self._lines = [x for x in self._lines if x != line]
        return self

    @classmethod
    def from_node(cls, node: Node) -> SubwayStation:
        '''
        Creates a SubwayStation object from a Neo4j Node object
        :param node: a Neo4j Node object
        :return: A SubwayStation object with properties equal to the property of the node
        '''
        return cls(
            station_name=node['station_name'],
            borough=node['borough'],
            entrances=node['entrances'],
            lines=node['lines'],
            status=node['status'],
            latitude=node['latitude'],
            longitude=node['longitude']
        )

    @classmethod
    def from_csv_row(cls, row: list) -> SubwayStation:
        lines = row['lines']
        if len(lines) > 1:
            lines = sorted([line.upper() for line in lines.split(',')])
        else:
            lines = [lines.upper()]

        borough = row['borough']
        if row['borough'] == np.nan:
            borough = 'No Borough Found'

        entrance = row['entrance']
        if row['entrance'] == np.nan:
            entrance = 'No Entrance Found'

        return cls(
            station_name=row['station_name'],
            borough=borough,
            entrances=entrance,
            lines=lines,
            status='Normal',
            latitude=row['latitude'],
            longitude=row['longitude']
        )

    def to_dict(self):
        return {
            "station_name": self.station_name,
            "borough": self.borough,
            "entrances": self.entrances,
            "lines": self.lines,
            "status": self.status,
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    def __eq__(self, other: SubwayStation) -> bool:
        '''
        Overload == operator
        :param other: the thing being compared
        :return: True if equal, False otherwise
        '''
        if (self.station_name == other.station_name
                and self.borough == other.borough
                and self.entrances == other.entrances
                and self.lines == other.lines):
            return True
        else:
            return False

    def __repr__(self):
        return "<SubwayStation(station_name={0}, borough={1}, entrances={2}, lines={3}, status={4})>" \
            .format(self.station_name, self.borough, self.entrances, self.lines, self.status)


class TrainLine:
    '''
    Edges on the graph
    '''

    def __init__(self,
                 start: SubwayStation = None,
                 stop: SubwayStation = None,
                 line: str = None) -> TrainLine:
        '''

        :param start: The 'starting' SubwayStation for the given edge
        :param stop: The 'stopping' SubwayStation for the given edge
        :param line: The line for the given edge
        '''
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
                 line: str = None,
                 direction: str = None,
                 schedule: [] = None):
        self.line = line
        self.direction = direction
        self.schedule = schedule

    @property
    def line(self):
        return self.line

    @line.setter
    def line(self, value):
        self.line = value
        return self

    @property
    def direction(self):
        return self.direction

    @direction.setter
    def direction(self, value):
        self.direction = value
        return self

    @property
    def schedule(self):
        return self.schedule

    @schedule.setter
    def schedule(self, value):
        self.schedule = value
        return self

    @classmethod
    def from_mongo(cls, query: {}) -> Schedule:
        '''
        Creates a Schedule object from Mongo query result
        :param schedule: a Mongo db querey result
        :return: A SubwayStation object with properties equal to the property of the node
        '''
        return cls(
            line=query['Line'],
            direction=query['Direction'],
            schedule=query['Schedule']
        )