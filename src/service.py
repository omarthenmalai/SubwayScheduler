from src.repository import *
from src.models import *
import pandas as pd

class MapService:

    def __init__(self):
        self.repository = MapRepository()

    def create_station(self, station):
        result = self.repository.create_station(station)
        if result is None:
            return None
        else:
            return result

    def create_connection(self, train):
        result = self.repository.create_connection(train)
        if result is None:
            return None
        else:
            return result

    def get_shortest_path(self, start_station, stop_station):
        result = self.repository.shortest_path(start_station, stop_station)
        return result


    def get_all_stations(self):
        result = self.repository.all_stations()
        return result

    def get_stations_by_line(self, line):
        result = self.repository.stations_by_line(line)
        return result

    def test(self, stat1, stat2):
        result = self.repository.test(stat1, stat2)
        return result

    def get_connections(self, station):
        result = self.repository.all_connections(station)
        return result


    def set_station_status_out_of_order(self, station):
        # Get all connections for the given station and reroute them as necessary
        connections = self.repository.all_connections(station)

        # Detach the station (remove all relationships) and set its status to "Out of Order
        self.repository.detach_node(station)

        # Reroute around the station
        reroutes = [['station', 'line']]
        for connect in connections:
            s = [station_name for station_name in connect['r']['stations'] if station_name != station.station_name][0]
            l = connect['r']['line']
            reroutes.append([s, l])
        reroutes = pd.DataFrame(reroutes[1:], columns=reroutes[0])
        for line in reroutes['line'].unique():
            temp = reroutes[reroutes['line'] == line]
            new_stations = temp['station'].values.tolist()

            # Case: Station is the end of the line. Create a relationship pointing to itself for later re-addition
            if len(temp) == 1:
                train_line = TrainLine(start=station.station_name, stop=station.station_name, line=str(line))
            # Case: Relationship between two stations. Reroute around the station but leave the station_name as
            # reference for future re-addition
            else:
                train_line = TrainLine(start=new_stations[1], stop=new_stations[0], line=str(line))

            # Create the reroute
            self.repository.create_reroute(train_line=train_line, reroute=station.station_name)


        return True

    def set_station_status_normal(self, station):
        # Get all connections for the given station and reroute them as necessary
        connections = self.repository.get_reroutes(station)


        # Remove all reroutes and set the station status to "Normal"
        self.repository.remove_reroute(station.station_name)

        # Restore the initial connections that existed before the given station was rerouted
        for connect in connections:
            s = [station_name for station_name in connect['r']['stations']]
            l = connect['r']['line']
            reroute = connect['r']['reroute']

            train_line_in = TrainLine(start=s[0], stop=station.station_name, line=l)
            train_line_out = TrainLine(start=station.station_name, stop=s[1], line=l)

            self.repository.create_connection(train_line_in)
            self.repository.create_connection(train_line_out)

        return True
