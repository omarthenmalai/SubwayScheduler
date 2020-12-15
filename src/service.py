from __future__ import annotations
from src.repository import *
from src.models import *
import pandas as pd
import numpy as np
import itertools
import os
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError


class MapService:
    """
    Class that handles all intermediate logic for the Neo4j graph database
    """
    def __init__(self):
        self.repository = MapRepository()

    def create_station(self,
                       station: SubwayStation):
        """
        Creates a SubwayStation node from the SubwayStation object
        :param station: SubwayStation object
        :return:
        """
        result = self.repository.create_station(station)
        if result is None:
            return None
        else:
            return result

    def create_connection(self,
                          train_line: TrainLine):
        """
        Creates a CONNECTS relationship from the TrainLine object
        :param train_line: TrainLine object
        :return:
        """
        result = self.repository.create_connection(train_line)
        if result is None:
            return None
        else:
            return result

    def get_shortest_path(self,
                          start_station: SubwayStation,
                          stop_station: SubwayStation) -> List[TrainLine]:
        """
        Gets the shortest paths between two SubwayStation nodes
        :param start_station: the starting node
        :param stop_station: the ending node
        :return: List[TrainLine] objects describing the route taken
        """
        result = self.repository.shortest_path(start_station, stop_station)

        # Iterate through the path and append stations to an array
        stations = []
        for record in result:
            relationships = record['path'].relationships
            for rel in relationships:
                stations.append(SubwayStation.from_node(rel.start_node))
        # Add the stop station to the array
        stations.append(stop_station)


        # Iterate through the stations in the path adding the lines connecting each pair of stations
        # to an array
        lines = []
        for i in range(0, len(stations) - 1):
            connections = self.get_connections_between_stations(stations[i], stations[i + 1])
            lines.append(connections)

        # Use the 2d array of lines to construct all possible paths
        paths = []
        reduced_stations = []

        min_transfers = 10000

        for t in itertools.product(*lines):
            p, s = MapService._reduce_path(list(t), list(stations))
            if len(paths) < min_transfers:
                paths.insert(0, p)
                reduced_stations.insert(0, s)
                min_transfers = len(paths)

            else:
                paths.append(p)
                reduced_stations.append(s)

        shortest_path = MapService._calculate_shortest_path(paths[:100], reduced_stations[:100])

        return shortest_path

    @staticmethod
    def _reduce_path(path, stations):
        """
        Reduces the path by truncating repeating lines
        :param path:
        :param stations:
        :return:
        """
        reduced_paths = []
        reduced_stations = []
        for i in range(0, len(path)):
            # 7X and 6X not supported in schedules db
            if path[i] == "7X":
                path[i] = "7"
            elif path[i] == "6X":
                path[i] = "6"

        reduced_paths = [path[0]]
        reduced_stations = [stations[0]]
        j = 0
        while j < len(path) - 1:
            if path[j] == path[j + 1]:
                j += 1
            else:
                reduced_stations.append(stations[j + 1])
                reduced_paths.append(path[j + 1])
                j += 1
        reduced_stations.append(stations[-1])



        return reduced_paths, reduced_stations

    @staticmethod
    def _calculate_shortest_path(paths, reduced_stations) -> List[TrainLine]:
        """
        Uses the schedules to determine which unweighted path is fastest.
        :param paths: list of paths
        :param reduced_stations: list of stations for those paths
        :return: list of TrainLine objects describing the shortest path
        """
        schedule_service = ScheduleService()
        fastest_path = paths[0]
        fastest_time_taken = timedelta(minutes=100000)
        fastest_path_times = []
        fastest_stations = []
        transfers = 1000

        visited_paths = {}

        start_time = datetime.now().replace(year=1900,  month=1, day=1, hour=13, minute=48)

        for path, stations in zip(paths, reduced_stations):
            evaluate = True
            time = start_time
            path_times = []
            for i in range(0, len(path)):

                cur_start_station = stations[i]
                cur_end_station = stations[i+1]
                curr_path = path[i]


                # Get the schedule with the desired departure and arrival time
                try:
                    sched = schedule_service.get_next_train_by_station_name_and_line(cur_start_station,
                                                                                     cur_end_station,
                                                                                     curr_path,
                                                                                     time)
                except IndexError:
                    evaluate = False
                    break
                if len(sched) == 0:
                    evaluate = False
                    break


                departure_time = sched['Schedule'][cur_start_station.schedule_key()]
                arrival_time = sched['Schedule'][cur_end_station.schedule_key()]
                path_times.append([departure_time, arrival_time])
                time = arrival_time.replace(day=1)

            # Path was not succesfully evaluated. continue
            # if len(path_times) < len(path):
            #     continue


            # If it takes less time, make that path the fastest path
            if evaluate and path_times[-1][1] - path_times[0][0] < fastest_time_taken:
                fastest_path = path
                fastest_path_times = path_times
                fastest_stations = stations
                fastest_time_taken = path_times[-1][1] - path_times[0][0]
                transfers = len(stations)
            # if it takes the same amount of time, choose the path that has the least number of transfers
            elif evaluate and path_times[-1][1] - path_times[0][0] == fastest_time_taken and len(stations) < transfers:
                fastest_path = path
                fastest_path_times = path_times
                fastest_stations = stations
                transfers = len(stations)

        if len(fastest_stations) == 0:
            return None, None


        train_lines = []
        for i in range(0, len(fastest_stations)-1):
            train_line = TrainLine(start=fastest_stations[i],
                                   stop=fastest_stations[i+1],
                                   line=fastest_path[i],
                                   departure_time=fastest_path_times[i][0].strftime("%H:%M"),
                                   arrival_time=fastest_path_times[i][1].strftime("%H:%M"))
            train_lines.append(train_line)

        return train_lines, fastest_path_times

    def get_all_stations(self) -> List[SubwayStation]:
        """
        Gets all of the nodes in the graph and converts them to SubwayStation objects
        :return: List[SubwayStation]
        """
        result = self.repository.all_stations()
        result = [SubwayStation.from_node(record['s']) for record in result]
        return result

    def get_all_active_stations(self) -> List[SubwayStation]:
        """
        Gets all of the SubwayStation nodes in the graph whose status is "normal".
        :return: List[SubwayStation]
        """
        result = self.repository.get_all_active_stations()
        result = [SubwayStation.from_node(record['s']) for record in result]
        return result

    def get_stations_by_line(self,
                             line: str) -> List[SubwayStation]:
        """
        Gets all of the stations, in order, for the given line
        :param line: the line
        :return: List[SubwayStation]
        """
        result = self.repository.get_stations_by_line(line)
        start = []
        stop = []
        for record in result:
            reroutes = record["r"]["reroute"]
            if reroutes:
                prev_reroute = None

                for i in range(0, len(reroutes)):

                    split_reroutes = reroutes[i].split("?")
                    rerouted_station = self.get_station_by_name_and_entrance(reroutes[i].split("?")[0],
                                                                             reroutes[i].split("?")[1])

                    if split_reroutes[-1] == "start":
                        for j in range(0, len(reroutes)):
                            split_reroutes = reroutes[j].split("?")
                            rerouted_station = self.get_station_by_name_and_entrance(split_reroutes[0],
                                                                                     split_reroutes[1])

                            if j == 0:
                                start.append(rerouted_station)
                                try:
                                    next_rerouted_station = self.get_station_by_name_and_entrance(
                                        reroutes[j + 1].split("?")[0],
                                        reroutes[j + 1].split("?")[1])
                                    stop.append(next_rerouted_station)
                                except IndexError:
                                    stop.append(SubwayStation.from_node(record['nodes'][0]))


                            elif j == len(reroutes) - 1:
                                start.append(rerouted_station)
                                stop.append(SubwayStation.from_node(record['nodes'][0]))
                            else:
                                start.append(rerouted_station)
                                stop.append(rerouted_station)
                        break

                    elif split_reroutes[-1] == "end":
                        # if len(reroutes) == 1:
                        for j in range(0, len(reroutes)):
                            rerouted_station = self.get_station_by_name_and_entrance(reroutes[j].split("?")[0],
                                                                                     reroutes[j].split("?")[1])
                            if j == len(reroutes) - 1:
                                stop.append(rerouted_station)
                                if j-1 != -1:
                                    prev_rerouted_station = self.get_station_by_name_and_entrance(
                                        reroutes[j-1].split("?")[0],
                                        reroutes[j-1].split("?")[1])
                                    start.append(prev_rerouted_station)
                                else:
                                    start.append(SubwayStation.from_node(record['nodes'][0]))

                            elif j == 0:
                                start.append(SubwayStation.from_node(record['nodes'][0]))
                                stop.append(rerouted_station)
                            else:
                                start.append(rerouted_station)
                                stop.append(rerouted_station)
                        break

                    elif len(reroutes) > 1:
                        if i == 0:
                            start.append(SubwayStation.from_node(record['nodes'][0]))
                            stop.append(rerouted_station)
                            prev_reroute = rerouted_station
                        elif i == len(reroutes) - 1:
                            start.append(prev_reroute)
                            stop.append(rerouted_station)
                            start.append(rerouted_station)
                            stop.append(SubwayStation.from_node(record['nodes'][1]))
                        else:
                            start.append(prev_reroute)
                            stop.append(rerouted_station)
                            prev_reroute = rerouted_station
                    else:
                        start.append(SubwayStation.from_node(record['nodes'][0]))
                        stop.append(rerouted_station)
                        start.append(rerouted_station)
                        stop.append(SubwayStation.from_node(record['nodes'][1]))
            else:
                start.append(SubwayStation.from_node(record['nodes'][0]))
                stop.append(SubwayStation.from_node(record['nodes'][1]))

        # Get starting station
        start_station = None
        for station in start:
            if station not in stop:
                start_station = station
        ordered_stations = [start_station]
        prev_station = start_station

        # Get stations in order
        i = 0
        while i < len(start):
            index = start.index(prev_station)
            prev_station = stop[index]
            ordered_stations.append(prev_station)
            i += 1

        return ordered_stations

    def get_connections_between_stations(self,
                                         station_1: SubwayStation,
                                         station_2: SubwayStation):
        """
        Gets all of the connections between two SubwayStation nodes
        :param station_1: SubwayStation object
        :param station_2: SubwayStation object
        :return: list containing the starting nodes, ending nodes, and relationships between the two stations
        """
        result = self.repository.get_connections_between_stations(station_1, station_2)
        return result

    def get_station_by_name_and_entrance(self, station_name: str, entrance: str) -> SubwayStation:
        """
        Gets the SubwayStation node corresponding to the given name and entrance
        :param station_name: the station's name
        :param entrance: the entrance
        :return: SubwayStation object
        """
        result = self.repository.get_station_by_name_and_entrance(station_name, entrance)
        node = result['s']
        subway_station = SubwayStation.from_node(node=node)
        return subway_station

    def get_distinct_lines(self):
        """
        Gets a list of the unique lines in the graph
        :return:
        """
        return self.repository.get_distinct_lines()

    def set_station_status_out_of_order(self,
                                        station: SubwayStation):
        """
        Sets the given SubwayStation node's status to "out of order" and detachs it from the graph.
        Creates REROUTES relationships between the connecting SubwayStations to go around the given station.
        :param station: SubwayStation object
        :return: None
        """

        # Get all connections for the given station and reroute them as necessary
        connections = self.repository.all_connections(station)

        # Detach the station (remove all relationships) and set its status to "Out of Order
        self.repository.detach_node(station)

        unique_lines = list(set([c['line'] for c in connections]))

        for line in unique_lines:
            records_for_line = [c for c in connections if c['line'] == line]
            start_node = None
            end_node = None
            reroute = None

            # Station is at the end of the given line (i.e. only connections coming in or coming out

            # Station is between two stations on a given line
            for record in records_for_line:
                start = SubwayStation.from_node(record['start'])
                end = SubwayStation.from_node(record['end'])
                # Check if the relationship is a REROUTE
                if record['reroute'] is not None:
                    # Check if the station is the start or ending node of the reroute.
                    # If the station is the start node, prepend it to the list of reroutes.
                    # If the station is the end node, append it to the end of the list of reroutes.
                    # This process helps to ensure that nodes are properly reconnected when a station is
                    # restored to 'Normal' status.

                    # First reroute found. This check is necessary because
                    # a given station may have reroutes on both sides.

                    if reroute is None:
                        reroute = record['reroute']
                        starting_reroute = record['reroute'][0].split("?")
                        ending_reroute = record['reroute'][-1].split("?")
                        if starting_reroute[-1] == "start":
                            reroute = reroute + [station.reroute()]
                        elif ending_reroute[-1] == "end":
                            reroute = [station.reroute()] + reroute
                        elif station == start:
                            reroute = [station.reroute()] + reroute
                        elif station == end:
                            reroute = reroute + [station.reroute()]
                    # Not the first reroute found for the given SubwayStation and line.
                    elif reroute is not None:
                        starting_reroute = record['reroute'][0].split("?")
                        ending_reroute = record['reroute'][-1].split("?")
                        if starting_reroute[-1] == "start":
                            reroute = record['reroute'] + [station.reroute()]
                        elif ending_reroute[-1]['reroute'] == "end":
                            reroute = [station.reroute()] + record['reroute']
                        elif station.station_name == start.station_name:
                            reroute = reroute + record['reroute']
                        elif station.station_name == end.station_name:
                            reroute = record['reroute'] + reroute
                # Set the end_node and start_node based on where the SubwayStation station appears in the relationship
                if start == station:
                    end_node = end
                elif end == station:
                    start_node = start

            # CASE: End of the line
            train_line = TrainLine()
            if start_node is None or end_node is None:
                if end_node is not None:
                    train_line = TrainLine(start=end_node, stop=end_node, line=line)
                    if reroute is not None and len(reroute[0].split("?")) == 2:
                        reroute[0] = reroute[0] + "?start"
                    elif reroute is None:
                        reroute = [station.reroute() + "?start"]
                elif start_node is not None:
                    train_line = TrainLine(start=start_node, stop=start_node, line=line)
                    if reroute is not None and len(reroute[-1].split("?")) == 2:
                        reroute[-1] = reroute[-1] + "?end"
                    elif reroute is None:
                        reroute = [station.reroute() + "?end"]
            elif start_node == end_node:
                continue
            elif reroute is not None and reroute[0].split("?")[-1] == "start":
                train_line = TrainLine(start=end_node, stop=end_node, line=line)
            elif reroute is not None and reroute[-1].split("?")[-1] == "end":
                train_line = TrainLine(start=start_node, stop=start_node, line=line)
            # CASE: SubwayStation between two other SubwayStations for the given line
            else:
                train_line = TrainLine(start=start_node, stop=end_node, line=line)

            # If the reroute is not None, then we know that we are rerouting a REROUTES relationship.
            if reroute is not None:
                self.repository.create_reroute(train_line=train_line, reroute=reroute)

            # Creating a reroute from two CONNECTS
            else:
                self.repository.create_reroute(train_line=train_line, reroute=[station.reroute()])


    def _get_all_reroutes_and_extras(self, station):
        """
        Gets all of the REROUTES relationships corresponding to the given SubwayStation
        :param station: SubwayStation object
        :return: list of reroutes, and a list of markers that are included if the SubwayStation is the first or last
        on a given line
        """
        normal_reroutes = self.repository.get_reroutes(station.reroute())
        start_reroutes = self.repository.get_reroutes(station.reroute()+"?start")
        end_reroutes = self.repository.get_reroutes(station.reroute()+"?end")


        extras = []
        for reroute in normal_reroutes:
            extras.append("")
        for reroute in start_reroutes:
            extras.append("?start")
            # if reroute[-5:] == "start":
        for reroute in end_reroutes:
            extras.append("?end")

        reroutes = normal_reroutes + start_reroutes + end_reroutes
        return reroutes, extras

    def set_station_status_normal(self,
                                  station: SubwayStation):
        '''
        Sets a SubwayStation's status to "normal". Removes all of the REROUTES relationships for the given SubwayStation
        and reconnects it to the grpah. If the given REROUTES relationship spans multiple SubwayStations, new REROUTES
         must be created as well.
        :param station:
        :return:
        '''

        # Get all reroutes associated with the given station
        reroutes, extras = self._get_all_reroutes_and_extras(station)

        # Remove all reroutes and set the station status to "Normal"
        # Iterate through reroutes and restore them to the given station
        for r, extra in zip(reroutes, extras):
            self.repository.remove_reroute(station.reroute() + extra)
            # The line for the given REROUTES relationship
            line = r['line']
            # The station_names for the given REROUTES relationship
            rerouted_stations = r['reroute']

            # Index of station in the reroute array for a given REROUTES relationship
            station_index = rerouted_stations.index(station.reroute() + extra)

            start = SubwayStation.from_node(r['start'])
            end = SubwayStation.from_node(r['end'])

            if extra == "" and rerouted_stations[station_index-1].split("?")[-1] == "start":
                line_in = TrainLine(start=station, stop=station, line=line)
                line_out = TrainLine(start=station, stop=end, line=line)
            elif extra == "" and rerouted_stations[station_index-1].split("?")[-1] == "end":
                line_in = TrainLine(start=start, stop=station, line=line)
                line_out = TrainLine(start=station, stop=station, line=line)
            elif extra == "":
                # Create the TrainLine objects going into and out of the reintroduced SubwayStation
                line_in = TrainLine(start=start, stop=station, line=line)
                line_out = TrainLine(start=station, stop=end, line=line)
            elif extra == "?start":
                line_in = None
                line_out = TrainLine(start=station, stop=start, line=line)
            elif extra == "?end":
                line_in = TrainLine(start=start, stop=station, line=line)
                line_out = None





            # The given station is the only one being rerouted by the given REROUTES relationship
            if len(rerouted_stations) == 1:
                self.repository.create_connection(line_in)
                self.repository.create_connection(line_out)


            # The given REROUTES relationship has multiple SubwayStation's that it is rerouting
            else:
                # The given SubwayStation is the first station being rerouted
                if station_index == 0:
                    self.repository.create_connection(train_line=line_in)
                    self.repository.create_reroute(train_line=line_out, reroute=rerouted_stations[1:])
                # The given SubwayStation is the last station being rerouted
                elif station_index == len(rerouted_stations) - 1:
                    self.repository.create_reroute(train_line=line_in,
                                                   reroute=rerouted_stations[:station_index])
                    self.repository.create_connection(train_line=line_out)

                # The given SubwayStation is somewhere in the middle of the reroute (will have REROUTES on both sides
                else:
                    self.repository.create_reroute(train_line=line_in,
                                                   reroute=rerouted_stations[0:station_index])
                    self.repository.create_reroute(train_line=line_out,
                                                   reroute=rerouted_stations[station_index + 1:])



class ScheduleService:

    def __init__(self):
        self.repository = ScheduleRepository()

    def get_schedules_by_line(self,
                              line: str) -> List[Schedule]:
        """
        Gets all of the Schedules for the given line
        :param line: the line
        :return: List[Schedule]
        """
        result = self.repository.get_schedules_by_line(line)
        array = []

        for record in result:
            array.append(Schedule.from_mongo(record))

        return array

    def get_next_train_by_station_name_and_line(self,
                                                start_station: SubwayStation,
                                                end_station: SubwayStation,
                                                line: str,
                                                time: datetime) -> Schedule:
        """
        Getes the next train for going from start_station to end_station on the given line, after the time specified
        :param start_station: the starting SubwayStation
        :param end_station: the ending SubwayStation
        :param line: the line
        :param time: the minimum time
        :return: Schedule
        """
        result = self.repository.get_next_train_by_station_name_and_line(start_station.schedule_key(),
                                                                         end_station.schedule_key(),
                                                                         line,
                                                                         time)
        result = [res for res in result][0]
        return result

    def delay_train(self, schedule: Schedule, station_name: str, delay: timedelta):
        """
        Delays the specified schedule by the provided delay starting at station_name. If a delay already exists,
        remove that delay first.
        :param schedule: the Schedule object
        :param station_name: the name of the starting station
        :param delay: the delay amount
        :return:
        """
        if schedule.delay is not None:
            new_sched = self.remove_delay(schedule=schedule)
            schedule = Schedule.from_mongo(new_sched)
        result = self.repository.delay_train(schedule=schedule, station_name=station_name, delay=delay)
        return result

    def get_train_by_line_direction_station_and_start_time(self,
                                                           line: str,
                                                           direction: str,
                                                           starting_station: str,
                                                           time: datetime):
        """
        Gets the Schedule that starts from the given starting_station at the given time, going in the given direction
        on the given line
        :param line: the line
        :param direction: the direction
        :param starting_station: the starting station
        :param time: the time
        :return:
        """
        result = self.repository.get_train_by_line_direction_station_and_start_time(line, direction,
                                                                                    starting_station, time)
        return Schedule.from_mongo(result)

    def remove_delay(self, schedule: Schedule):
        """
        Removes the delay from the given Schedule
        :param schedule: the Schedule object
        :return:
        """
        if schedule.delay is None:
            return None
        else:
            result = self.repository.remove_delay(schedule=schedule)
            return result

    def get_delays(self) -> pd.DataFrame:
        """
        Gets all of the delays on the system
        :return: pd.DataFrame containing the relevant delay information
        """
        result = self.repository.get_delays()
        schedules = [x for x in result]

        output = [["Line", "Direction", "Time", "Starting Station", "Delay"]]
        for schedule in schedules:
            line = schedule["Line"]
            direction = schedule["Direction"]
            starting_station = schedule["Delay"]["start"]
            delay = schedule["Delay"]["time"]
            time = schedule["Schedule"][list(schedule["Schedule"].keys())[0]].strftime("%H:%M")
            output.append([line, direction, time, starting_station, delay])
        df = pd.DataFrame(output[1:], columns=output[0]).sort_values(by=["Line", "Time"])
        return df

    def get_schedules_by_line_direction(self, line, direction) -> (List, List):
        """
        Gets all of the schedules for Trains going in the given direction on the given line
        """
        result = self.repository.get_schedules_by_line_direction(line=line, direction=direction)
        results = [x for x in result]
        if len(results) > 0:
            schedules = sorted(results, key=lambda schedule: schedule['Schedule'][min(schedule['Schedule'],
                                                                                      key=schedule["Schedule"].get)])

            # Get the schedule with a complete set of stations
            stations = []
            for s in schedules:
                keys = list(s["Schedule"].keys())
                if len(keys) > len(stations):
                    stations = keys
            # stations = list(schedules[0]["Schedule"].keys())

            result = []
            i = 0
            for schedule in schedules:
                result.append([])
                for key in stations:
                    if key in schedule["Schedule"]:
                        result[i].append(schedule["Schedule"][key].strftime("%H:%M"))
                    else:
                        result[i].append("--")
                i += 1


            # schedules = [[val.strftime("%H:%M") for val in schedule["Schedule"].values()] for schedule in schedules]
            return stations, result
        else:
            return None

    def get_unique_line_direction(self) -> {}:
        """
        Gets the unique set of line and directions across the Schedules in the Schedule collection
        :return: dictionary mapping lines to directions
        """
        result = self.repository.get_unique_line_direction()
        combinations = [Schedule(line=x['_id']['Line'], direction=x['_id']['Direction']) for x in result]

        line_direction_dict = {}
        for schedule in combinations:
            if schedule.line in line_direction_dict:
                line_direction_dict[schedule.line].append(schedule.direction)
            else:
                line_direction_dict[schedule.line] = [schedule.direction]
        return line_direction_dict


class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def add_user(self, user: User):
        """
        Adds a user to the Users table. Hashes and salts their password
        :param user: the User to add
        :return: the added User
        """
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',  # The hash digest algorithm for HMAC
            user.password.encode('utf-8'),  # Convert the password to bytes
            salt,  # Provide the salt
            100000,  # It is recommended to use at least 100,000 iterations of SHA-256
            dklen=128  # Get a 128 byte key
        )
        user.password = salt + key

        try:
            new_user = self.repository.add_user(user=user)
            return new_user
        except IntegrityError:
            return None

    def login_user(self, email, password):
        """
        Checks if a user with the given email and password exists.
        :param email: the email
        :param password: the password
        :return: If they exists User, else None
        """
        user = self.get_user_by_email(email)
        if user is None:
            return None
        actual_password_salt = user.password
        password_to_check = password

        salt_from_storage = actual_password_salt[:32]  # 32 is the length of the salt
        key_from_storage = actual_password_salt[32:]
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password_to_check.encode('utf-8'),  # Convert the password to bytes
            salt_from_storage,
            100000,
            dklen=128
        )
        if new_key == key_from_storage:
            return user
        else:
            return None

    def get_user_by_email(self, email) -> User:
        """
        Gets a User with the given email
        :param email: the email
        :return: User
        """
        return self.repository.get_user_by_email(email)


class TripService:
    def __init__(self):
        self.repository = TripRepository()

    def add_trip(self, trip: Trip):
        self.repository.add_trip(trip)

    def get_trips_by_user_id(self, user_id):
        trips = self.repository.get_trips_by_user_id(user_id)
        return [x for x in trips]
