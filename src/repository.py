from __future__ import annotations

from neo4j.graph import Relationship

from src.models import *
from src import login_manager
from typing import List
import pymongo
from bson import SON
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from datetime import timedelta
from src import mysql_engine, neo4j_driver, mongo_client


mongo_client.start_session()
collection = mongo_client['Train']['schedule']



Session = sessionmaker(bind=mysql_engine)
session = Session()
metadata = MetaData(mysql_engine)



@login_manager.user_loader
def load_user(id):
    u = session.query(User).get(id)
    return u


class UserRepository:
    """
    Class that handles all queries to the Users table in the MySQL database
    """
    def __init__(self):
        self.session = session

    def add_user(self, user: User):
        """
        Adds a user
        :param user: the User
        :return: the User
        """
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_user_by_email(self, email: str):
        """
        Get the User corresponding to the given email
        :param email: the user's email
        :return: the User
        """
        query = self.session.query(User).filter(User.email == email).first()
        return query


class MapRepository:
    """
    Class that handles all queries to the Neo4j graph database
    """
    def create_station(self, station: SubwayStation) -> Node:
        """
        Creates a station node in the graph based on 'station'
        :param station: SubwayStation object
        :return: the Node that was created
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_station, station)
        return transact

    @staticmethod
    def _create_station(tx, station):
        result = tx.run(
            '''
            MERGE (s:SubwayStation{
                station_name: $station_name,
                borough: $borough, 
                entrances: $entrances, 
                lines: $lines,
                status: $status
            }) 
            SET s.latitude = $latitude
            SET s.longitude = $longitude

            RETURN s
            ''',
            station_name=station.station_name,
            borough=station.borough,
            entrances=station.entrances,
            lines=station.lines,
            status=station.status,
            latitude=station.latitude,
            longitude=station.longitude
        )
        return result.single()

    def get_stations_by_line(self, line: str) -> List[Node]:
        """
        Gets all of the stations that have the given line in their list of lines
        :param line: the line
        :return: List of Node and Relationship objects
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_stations_by_line, line)
        return transact

    @staticmethod
    def _get_stations_by_line(tx, line):
        result = tx.run(
            '''
            MATCH path=(a:SubwayStation)-[r]->()
            WHERE $line = r.line
            RETURN nodes(path) as nodes, r
            ''',
            line=line
        )
        return [x for x in result]


    def get_station_by_name_and_entrance(self, station_name: str, entrance: str) -> List[Node]:
        """
        Gets a station by its station_name and entrances values. This combination of values is a unique
        identifier in the graph database
        :param station_name: the station name
        :param entrance: the entrance
        :return:
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_station_by_name_and_entrance, station_name, entrance)
        return transact

    @staticmethod
    def _get_station_by_name_and_entrance(tx, station_name, entrance):
        result = tx.run(
            '''
            MATCH (s:SubwayStation{station_name: $station_name, entrances: $entrance})
            RETURN s
            ''',
            station_name=station_name,
            entrance=entrance
        )
        return result.single()

    def create_connection(self, train_line: TrainLine) -> List[Node,Node,Relationship]:
        """
        Create a connection between two stations for a given line
        :param train_line: TrainLine object
        :return: list containing the two Nodes and the Relationship that was created
        """
        if train_line is None:
            return None
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_connection, train_line)

        return transact

    @staticmethod
    def _create_connection(tx, train_line):
        result = tx.run(
            '''
            MATCH (a:SubwayStation),
            (b:SubwayStation)
            WHERE $line IN a.lines AND $line IN b.lines
            AND a.station_name=$start_name AND a.borough=$start_borough
            AND b.station_name=$stop_name AND b.borough=$stop_borough
            AND $start_entrance in a.entrances AND $stop_entrance in b.entrances
            CREATE (a)-[r:CONNECTS { line: $line, cost:1 }]->(b)
            RETURN a, b, r
            ''',
            start_name=train_line.start.station_name,
            start_borough=train_line.start.borough,
            start_entrance=train_line.start.entrances,
            stop_name=train_line.stop.station_name,
            stop_borough=train_line.stop.borough,
            stop_entrance=train_line.stop.entrances,
            line=train_line.line
        )
        temp = result.single()
        return temp

    def get_connections_between_stations(self, station_1, station_2) -> List[Relationship]:
        """
        Gets all of the connections between two SubwayStation nodes
        :param station_1: the first SubwayStation object
        :param station_2: the second subwayStation object
        :return: a list of Relationships corresponding to the given nodes
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_connections_between_stations, station_1, station_2)
        return transact

    @staticmethod
    def _get_connections_between_stations(tx, station_1, station_2):
        result = tx.run(
            '''
            MATCH (a:SubwayStation)-[r]-(b:SubwayStation)
            WHERE a.station_name=$s1_name AND a.borough=$s1_borough AND a.entrances=$s1_entrances
            AND b.station_name=$s2_name AND b.borough=$s2_borough AND b.entrances=$s2_entrances
            RETURN r.line as line
            ''',
            s1_name=station_1.station_name,
            s1_borough=station_1.borough,
            s1_entrances=station_1.entrances,
            s2_name=station_2.station_name,
            s2_borough=station_2.borough,
            s2_entrances=station_2.entrances
        )
        return [x['line'] for x in result]

    def shortest_path(self, start_station: SubwayStation, stop_station: SubwayStation):
        """
        Gets the shortest, unweighted paths between two nodes.
        :param start_station:
        :param stop_station:
        :return: a list of the shortest paths
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._shortest_path, start_station, stop_station)
        return transact

    @staticmethod
    def _shortest_path(tx, start_station, stop_station):
        result = tx.run(
            '''
            MATCH (start:SubwayStation{station_name: $start_name, entrances: $start_entrance}),
             (end:SubwayStation{station_name:$stop_name, entrances: $stop_entrance})
            CALL gds.alpha.kShortestPaths.stream({
                nodeQuery: 'MATCH(n:SubwayStation{status:"Normal"}) RETURN id(n) AS id',
                relationshipQuery:'MATCH(n:SubwayStation)-[r]-(m:SubwayStation) RETURN id(n) AS source, id(m) AS target,
                                r.cost as cost',
                startNode: start,
                endNode: end,
                k: 1,
                relationshipWeightProperty: 'cost',
                path: true
            })
            YIELD path
            RETURN path
            ''',
            start_name=start_station.station_name,
            stop_name=stop_station.station_name,
            start_entrance=start_station.entrances,
            stop_entrance=stop_station.entrances
        )
        return [x for x in result]

    def all_stations(self) -> List[Node]:
        """
        Gets all of the SubwayStation nodes in the graph
        :return: the list of SubwayStation nodes
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._all_stations)
        return transact

    @staticmethod
    def _all_stations(tx):
        result = tx.run(
            '''
            MATCH (s:SubwayStation) 
            RETURN s
            '''
        )
        return [x for x in result]

    def get_all_active_stations(self):
        """
        Gets all stations whose status is "normal"
        :return: list of SubwayStation nodes
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_all_active_stations)
        return transact

    @staticmethod
    def _get_all_active_stations(tx):
        result = tx.run(
            '''
            MATCH (s:SubwayStation{status: "Normal"})
            RETURN s
            '''
        )
        return [x for x in result]

    def create_reroute(self, train_line, reroute):
        """
        Creates a REROUTES relationships between two SubwayStations. REROUTES keep track of the stations that are
        being rerouted to ensure that the graph can be properly reconstructed.
        :param train_line:
        :param reroute:
        :return:
        """
        if train_line is None:
            return None
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._create_reroute, train_line, reroute)
        return transact

    @staticmethod
    def _create_reroute(tx, train_line, reroute):
        result = tx.run(
            '''
            MATCH (a:SubwayStation),(b:SubwayStation)
            WHERE a.station_name = $start AND b.station_name = $stop
            AND $line IN a.lines AND $line IN b.lines 
            CREATE (a)-[r:REROUTES{line:$line, cost:1, reroute:$reroute}]->(b)
            RETURN a, b, r
            ''',
            start=train_line.start.station_name,
            stop=train_line.stop.station_name,
            line=train_line.line,
            reroute=reroute
        )
        return result.single()

    def detach_node(self, station):
        """
        Removes all connections to the given SubwayStation
        :param station: SubwayStation Object
        :return: None
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._detach_node, station)
        return transact

    @staticmethod
    def _detach_node(tx, station):
        result = tx.run(
            '''
            MATCH (a:SubwayStation{
                station_name: $station_name,
                borough: $borough,
                entrances: $entrances
            }), (a)-[r]-()
            SET a.status = "Out of Order"
            DELETE r
            ''',
            station_name=station.station_name,
            borough=station.borough,
            entrances=station.entrances
        )
        return result.single()

    def get_reroutes(self, reroute: str):
        """
        Returns all REROUTES relationships for the given node
        :param reroute: the reroute key for the SubwayStation
        :return: the starting nodes, ending nodes, and relationship for all of the relevant REROUTES
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_reroutes, reroute)
        return transact

    @staticmethod
    def _get_reroutes(tx, reroute):
        result = tx.run(
            '''
            MATCH ()-[r:REROUTES]->()
            WHERE $subway_station in r.reroute
            RETURN 
                startNode(r) as start, 
                endNode(r) as end, 
                r.line AS line, 
                r.reroute as reroute
            ''',
            subway_station=reroute
        )
        return [x for x in result]


    def remove_reroute(self, reroute: SubwayStation):
        """
        Removes all REROUTES relationships for the given SubwayStation. Sets that station's status to "normal"
        :param reroute:
        :return:
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._remove_reroute, reroute)
        return transact

    @staticmethod
    def _remove_reroute(tx, reroute):
        info = reroute.split("?")
        result = tx.run(
            '''
            MATCH (s:SubwayStation{ station_name: $station_name, entrances: $entrances})
            MATCH ()-[r:REROUTES]->()
            WHERE $reroute in r.reroute
            SET s.status = "Normal"
            DELETE r
            ''',
            station_name=info[0],
            entrances=info[1],
            reroute=reroute
        )
        return [x for x in result]

    def all_connections(self, station: SubwayStation):
        """
        Gets all connections to and from the given SubwayStation
        :param station: SubwayStation object
        :return: List of starting nodes, ending nodes, lines, and reroutes
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._all_connections, station)
        return transact

    @staticmethod
    def _all_connections(tx, station):
        result = tx.run(
            '''
            MATCH (a:SubwayStation{station_name: $station_name, entrances: $entrances}), (b:SubwayStation)
            MATCH (a)-[r]-(b)
            RETURN 
                startNode(r) as start, 
                endNode(r) as end, 
                r.line AS line, 
                r.reroute as reroute
            ''',
            station_name=station.station_name,
            entrances=station.entrances
        )
        return [x for x in result]

    @staticmethod
    def stations_with_line_without_relationship(line):
        """
        For debugging-Gets all stations that have a line in their lines property but don't have a connection for that line
        :param line: the line
        :return:
        """
        with neo4j_driver.session() as s:
            result = s.run(
                '''
                MATCH (s:SubwayStation)-[r]-()
                WHERE r.line IN s.lines
                RETURN s
                ''',
                line=line
            )
            return [x for x in result]

    def get_distinct_lines(self):
        """
        Gets all of the unique lines in the graph
        :return:
        """
        with neo4j_driver.session() as s:
            transact = s.write_transaction(self._get_distinct_lines)
        return transact

    @staticmethod
    def _get_distinct_lines(tx):
        result = tx.run(
            '''
            MATCH ()-[r]-()
            WITH DISTINCT r.line AS lines
            return lines
            '''
        )
        return [x for x in result]

    @staticmethod
    def clear_db():
        """
        Clears the graph
        :return:
        """
        with neo4j_driver.session() as s:
            s.run('''
                MATCH (n) DETACH DELETE n
            ''')


class ScheduleRepository:
    """
    Class that manages all queries to the Schedule collection in the MongoDB database
    """
    def __init__(self):
        self.collection = collection

    def get_schedules_by_line(self, line: str) -> pymongo.CursorType:
        """
        Gets all of the schedules for the given line.
        :param line: the line
        :return: Pymongo Cursor for the query
        """
        schedules = []
        result = self.collection.find(
            {"Line": line},
            {"_id": 0}
        )
        return result

    def get_next_train_by_station_name_and_line(self, start_station: SubwayStation,
                                                end_station: SubwayStation,
                                                line: str,
                                                time: datetime.datetime):
        """
        Gets the next train, after 'time', going from 'start_station' to 'end_station' on 'line'
        :param start_station: SubwayStation
        :param end_station: SubwayStation
        :param line: the ling
        :param time: the time
        :return: time when the next train arrives at starting_station and arrives at ending_station
        """
        pipeline = [
            {
                "$match":
                    {
                        "Line": str(line).upper(),
                        "Schedule.{}".format(start_station): {"$gte": time},
                        "$expr": {"$gt": ["$Schedule.{}".format(end_station),
                                          "$Schedule.{}".format(start_station)]},
                    }
            },
            {
                "$sort": SON([("Schedule.{}".format(end_station), 1)])
            },
            {
                "$limit": 1
            },
            {
                "$project":
                    {
                        "Schedule.{}".format(start_station): 1,
                        "Schedule.{}".format(end_station): 1
                    }
            }
        ]
        result = self.collection.aggregate(pipeline=pipeline)
        return result

    def get_train_by_line_direction_station_and_start_time(self, line, direction, starting_station, time):
        """
        Gets a train on the given line, going in the given direction, with the given start time
        :param line: the line
        :param direction: the direction
        :param starting_station: the name of the starting station
        :param time: the time
        :return: the schedule corresponding to that train
        """
        result = self.collection.find_one({
            "Line": str(line),
            "Direction": direction,
            "Schedule.{}".format(starting_station): {"$eq": time}
        })
        return result

    def delay_train(self, schedule: Schedule, station_name: str, delay: timedelta) -> Schedule:
        """
        Delays a train starting at the station specified by station_name. Adds the "Delay" property to the schedule,
        indicating the delay amount and the starting station. Adds the delay amount to all stations after the starting station.
        :param schedule: The schedule that will be delayed
        :param station_name: the starting station
        :param delay: the amount of delay
        :return:
        """
        update = \
            {
                "$set":
                    {
                        "Delay":
                            {
                                "start": station_name,
                                "time": int(delay.seconds / 60)
                            }
                    }
            }

        for stop in schedule.schedule:
            if schedule.schedule[station_name] < schedule.schedule[stop]:
                update["$set"]["Schedule.{}".format(stop)] = schedule.schedule[stop] + delay

        result = self.collection.update(
            {
                "Line": schedule.line,
                "Direction": schedule.direction,
                "Schedule.{}".format(station_name): {"$eq": schedule.schedule[station_name]}
            },
            update

        )

        return result

    def remove_delay(self, schedule: Schedule) -> Schedule:
        """
        Removes the delay from the given Schedule. Uses the "Delay" property to properly subtract from arrival times.
        Unsets the "Delay" property
        :param schedule: the delayed Schedule
        :return: the updated Schedule
        """

        update = \
            {
                "$set": {
                    # Reset times to pre-delay
                },
                "$unset": {"Delay": ""}  # Remove delay property
            }
        start = schedule.delay['start']
        delay = schedule.delay['time']
        for stop in schedule.schedule:
            if schedule.schedule[start] < schedule.schedule[stop]:
                update["$set"]["Schedule.{}".format(stop)] = schedule.schedule[stop] - timedelta(minutes=delay)
        result = self.collection.find_one_and_update(
            {
                "Line": schedule.line,
                "Direction": schedule.direction,
                "Schedule.{}".format(start): {"$eq": schedule.schedule[start]}
            },
            update,
            return_document=pymongo.ReturnDocument.AFTER
        )
        return result

    def get_delays(self):
        """
        Gets all of the delays on the system
        :return: Pymongo Cursor
        """
        result = self.collection.find(
            {
                "Delay": {"$exists": True}
            }
        )
        return result

    def get_schedules_by_line_direction(self, line: str, direction: str) -> pymongo.CursorType:
        """
        Gets all of the schedules for the given line and direction
        :param line: the line
        :param direction: the direction
        :return: Pymongo Cursor
        """
        result = self.collection.find(
            {
                "Line": str(line.upper()),
                "Direction": direction
            },
            {"Schedule": 1, "Delay": 1, "_id": 0}
        )
        return result

    def get_unique_line_direction(self):
        """
        Gets the unique set of lines and directions
        :return:
        """
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "Line": "$Line",
                        "Direction": "$Direction"
                    }
                }
            },
            {
                "$project": {
                    "Line": 1,
                    "Direction": 1
                }
            }
        ]
        result = self.collection.aggregate(pipeline)
        return result

    def bulk_insert_schedules(self, schedules):
        """
        Bulk inserts schedule documents into the Schedule collection
        :param schedules: an array of schedule documents
        :return: None
        """
        self.collection.insert_many(schedules)

    def clear_db(self):
        """
        Clears out the Schedule collection
        :return: None
        """
        self.collection.delete_many({})


class TripRepository:
    """
    Class that manages the queries made to the Trips table in the MySQL database
    """
    def __init__(self):
        self.session = session

    def add_trip(self, trip: Trip):
        """
        Adds a new trip
        :param trip:
        :return:
        """
        self.session.add(trip)
        self.session.commit()

    def get_trips_by_user_id(self, user_id: int):
        """
        Gets all of the trips for the User with the given user_id
        :param user_id: the user_id
        :return: a cursor for the query
        """
        query = self.session.query(Trip) \
            .filter(Trip.user_id == user_id) \
            .order_by(Trip.timestamp.desc())
        return query
