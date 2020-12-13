from __future__ import annotations
from src.repository import *
from src.models import *
import pandas as pd
import numpy as np
import itertools
import os
import hashlib
from datetime import datetime, timedelta


class MapService:

    def __init__(self):
        self.repository = MapRepository()

    def create_station(self,
                       station: SubwayStation):
        result = self.repository.create_station(station)
        if result is None:
            return None
        else:
            return result

    def create_connection(self,
                          train_line: TrainLine):
        result = self.repository.create_connection(train_line)
        if result is None:
            return None
        else:
            return result

    def get_shortest_path(self,
                          start_station: SubwayStation,
                          stop_station: SubwayStation):

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
        for t in itertools.product(*lines):
            paths.append(t)

        path_df = MapService._calculate_shortest_path(stations, paths)

        return path_df

    @staticmethod
    def _simplify_paths(path, stations):
        j = 1
        new_path = []
        new_stations = [stations[0]]
        while j < len(path):
            if path[j] != path[j - 1]:
                new_path.append(path[j])
                new_stations.append(stations[j])
            j += 1
        print(new_path)
        print(new_stations)
        return path

    @staticmethod
    def _calculate_shortest_path(stations, paths):
        schedule_service = ScheduleService()

        fastest_path = paths[0]
        fastest_time_taken = timedelta(minutes=100000)
        fastest_path_times = []
        # start_time = datetime.now().replace(year=1900,  month=1, day=1)
        start_time = datetime(year=1900, month=1, day=1, hour=12, minute=20)

        visited_paths = {}

        for path in paths:
            evaluate = True
            # time = datetime.now().replace(year=1900, month=1, day=1, hour=19, minute=23)
            time = start_time
            path_times = [time]
            for i in range(0, len(path)):
                cur_start_station = stations[i]
                cur_end_station = stations[i + 1]

                # F ix path: temporary fix until we deal with express pathing later
                curr_path = path[i]
                if path[i] == "7X":
                    curr_path = "7"
                elif path[i] == "6X":
                    curr_path = "6"

                if cur_start_station.station_name + "/" + cur_end_station.station_name in visited_paths and \
                        curr_path in visited_paths[cur_start_station.station_name + "/" + cur_end_station.station_name]:
                    time = visited_paths[cur_start_station.station_name + "/" + cur_end_station.station_name][curr_path]
                else:
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
                        print("ERROR: Couldn't Resolve the current path --> {}".format(path))
                        evaluate = False
                        break

                    time = sched['Schedule'][cur_end_station.station_name]
                    if not cur_start_station.station_name + "/" + cur_end_station.station_name in visited_paths:
                        visited_paths[cur_start_station.station_name + "/" + cur_end_station.station_name] = {
                            curr_path: time}
                    else:
                        visited_paths[cur_start_station.station_name + "/" + cur_end_station.station_name][
                            curr_path] = time
                path_times.append(time)
            if time - start_time < fastest_time_taken and evaluate:
                fastest_time_taken = time - start_time
                fastest_path = path
                fastest_path_times = path_times

        stations = np.array([name.station_name for name in stations]).T
        fastest_path_times = np.array(fastest_path_times).T
        fastest_path = [fastest_path[i] for i in range(len(fastest_path))]
        fastest_path.append("")
        fastest_path = np.array(fastest_path).T
        train_lines = []
        for i in range(0, len(stations) - 1):
            train_line = TrainLine(start=stations[i], stop=stations[i + 1], line=fastest_path[i])
            train_lines.append(train_line)

        return train_lines, fastest_path_times

    def get_station_by_station_name(self,
                                    station_name: str):

        result = self.repository.get_station_by_station_name(station_name)
        return [SubwayStation.from_node(record['s']) for record in result][0]

    def get_all_stations(self):
        result = self.repository.all_stations()
        result = [SubwayStation.from_node(record['s']) for record in result]
        return result

    def get_all_active_stations(self):
        result = self.repository.get_all_active_stations()
        result = [SubwayStation.from_node(record['s']) for record in result]
        return result

    def get_stations_by_line(self,
                             line: str):

        result = self.repository.get_stations_by_line(line)
        start = []
        stop = []
        for record in result:
            reroutes = record["r"]["reroute"]
            if reroutes:
                prev_reroute = None

                for i in range(0, len(reroutes)):
                    rerouted_station = self.get_station_by_name_and_entrance(reroutes[i].split("?")[0],
                                                                             reroutes[i].split("?")[1])
                    if len(reroutes) > 1:
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

        start_station = None

        for station in start:
            if station not in stop:
                start_station = station
        ordered_stations = [start_station]
        prev_station = start_station
        i = 1
        while i < len(start):
            index = start.index(prev_station)
            prev_station = stop[index]
            ordered_stations.append(prev_station)
            i += 1
        return ordered_stations

    def get_connections_between_stations(self,
                                         station_1: SubwayStation,
                                         station_2: SubwayStation):

        result = self.repository.get_connections_between_stations(station_1, station_2)
        return result

    def get_station_by_name_and_entrance(self, station_name, entrance):
        result = self.repository.get_station_by_name_and_entrance(station_name, entrance)
        node = result['s']
        subway_station = SubwayStation.from_node(node=node)
        return subway_station

    def set_station_status_out_of_order(self,
                                        station: SubwayStation):
        """
        TODO: Add support for when the station being set out of order is the last on the line
        :param station:
        :return:
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
                        if station == start:
                            reroute = [station.reroute()] + reroute
                        elif station == end:
                            reroute = reroute + [station.reroute()]
                    # Not the first reroute found for the given SubwayStation and line.
                    elif reroute is not None:
                        if station.station_name == start.station_name:
                            reroute = reroute + record['reroute']
                        elif station.station_name == end.station_name:
                            reroute = record['reroute'] + reroute

                # Set the end_node and start_node based on where the SubwayStation station appears in the relationship
                if start == station:
                    end_node = end
                elif end == station:
                    start_node = start
                else:
                    print('ERROR: set_station_status_out_of_order -> given station is neither or starting or ending '
                          'node')

            # CASE: End of the line
            train_line = TrainLine()
            if start_node is None or end_node is None:
                if end_node is not None:
                    train_line = TrainLine(start=end_node, stop=end_node, line=line)
                elif start_node is not None:
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

        return True

    def set_station_status_normal(self,
                                  station: SubwayStation):
        '''
        TODO: Deal with the case where the station is at the end of a line
        :param station:
        :return:
        '''

        # Get all reroutes associated with the given station
        reroutes = self.repository.get_reroutes(station)
        # Remove all reroutes and set the station status to "Normal"
        self.repository.remove_reroute(station)

        # Iterate through reroutes and restore them to the given station
        for r in reroutes:
            # The line for the given REROUTES relationship
            line = r['line']
            # The station_names for the given REROUTES relationship
            rerouted_stations = r['reroute']

            # Index of station in the reroute array for a given REROUTES relationship
            station_index = rerouted_stations.index(station.reroute())

            start = SubwayStation.from_node(r['start'])
            end = SubwayStation.from_node(r['end'])

            # Create the TrainLine objects going into and out of the reintroduced SubwayStation
            line_in = TrainLine(start=start, stop=station, line=line)
            line_out = TrainLine(start=station, stop=end, line=line)

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

        return True


class ScheduleService:

    def __init__(self):
        self.repository = ScheduleRepository()

    def get_schedules_by_line(self,
                              line: str):
        result = self.repository.get_schedules_by_line(line)
        array = []

        for record in result:
            array.append(Schedule.from_mongo(record))

        return array

    def get_next_train_by_station_name_and_line(self, start_station, end_station, line, time):
        result = self.repository.get_next_train_by_station_name_and_line(start_station.station_name,
                                                                         end_station.station_name,
                                                                         line,
                                                                         time)
        result = [res for res in result][0]
        return result

    def delay_train(self, schedule: Schedule, station_name: str, delay: timedelta):
        if schedule.delay is not None:
            self.remove_delay(schedule=schedule)
        result = self.repository.delay_train(schedule=schedule, station_name=station_name, delay=delay)
        return result

    def remove_delay(self, schedule: Schedule):
        if schedule.delay is None:
            print("ERROR: Current train does not have a delay to remove")
            return None
        else:
            result = self.repository.remove_delay(schedule=schedule)
            return result

    def get_delays(self):
        result = self.repository.get_delays()
        schedules = [x for x in result]

        output = [["Line", "Direction", "Time", "Starting Station", "Delay"]]
        for schedule in schedules:
            line = schedule["Line"]
            direction = schedule["Direction"]
            starting_station = schedule["Delay"]["start"]
            delay = schedule["Delay"]["time"]
            time = schedule["Schedule"][min(schedule["Schedule"], key=schedule["Schedule"].get)]
            output.append([line, direction, time, starting_station, delay])
        df = pd.DataFrame(output[1:], columns=output[0]).sort_values(by=["Line", "Time"])
        return df


class UserService:
    def __init__(self):
        self.repository = UserRepository()

    def add_user(self, user: User):
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',  # The hash digest algorithm for HMAC
            user.password.encode('utf-8'),  # Convert the password to bytes
            salt,  # Provide the salt
            100000,  # It is recommended to use at least 100,000 iterations of SHA-256
            dklen=128  # Get a 128 byte key
        )
        user.password = salt + key

        # print(len(storage))
        # print(type(storage))

        self.repository.add_user(user=user)

    def add_many_users(self, user_array: []):
        self.repository.add_many_users(user_array)

    def get_user_by_email(self,
                          email: User):
        result = self.repository.get_user_by_email(email)[0].__dict__
        return result

    def login_user(self,
                   email: User,
                   password: User):
        user = self.get_user_by_email(email)
        actual_password_salt = user['password']
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
            print('Password is correct')
            x = True
        else:
            print('Password is incorrect')
            x = False
        return x
