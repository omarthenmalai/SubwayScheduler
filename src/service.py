from src.repository import *
from src.models import *
import pandas as pd
import numpy as np
import itertools


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

        return paths

    def get_station_by_station_name(self,
                                    station_name: SubwayStation):

        result = self.repository.get_station_by_station_name(station_name)
        return [SubwayStation.from_node(record['s']) for record in result][0]

    def get_all_stations(self):
        result = self.repository.all_stations()
        return result

    def get_stations_by_line(self,
                             line: str):

        result = self.repository.stations_by_line(line)
        return result

    def get_connections_between_stations(self,
                                         station_1: SubwayStation,
                                         station_2: SubwayStation):

        result = self.repository.get_connections_between_stations(station_1, station_2)
        return result

    def set_station_status_out_of_order(self,
                                        station: SubwayStation):
        '''
        TODO: Add support for when the station being set out of order is the last on the line
        :param station:
        :return:
        '''

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
                            reroute = [station.station_name] + reroute
                        elif station == end:
                            reroute = reroute + [station.station_name]
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
                self.repository.create_reroute(train_line=train_line, reroute=[station.station_name])

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
        self.repository.remove_reroute(station.station_name)

        # Iterate through reroutes and restore them to the given station
        for r in reroutes:
            # The line for the given REROUTES relationship
            line = r['line']
            # The station_names for the given REROUTES relationship
            rerouted_stations = r['reroute']
            # Index of station in the reroute array for a given REROUTES relationship
            station_index = rerouted_stations.index(station.station_name)

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
