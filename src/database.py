import pandas as pd
import os
import pymongo
from pymongo import MongoClient
import re
import numpy as np
from os import walk
from os import listdir
from os.path import isfile, join
from datetime import datetime
from sqlalchemy import Table
from sqlalchemy import Integer, String, Column, LargeBinary, DateTime

# Local imports
from src.models import SubwayStation, TrainLine, Schedule
from src.service import MapService, ScheduleService
from src.repository import ScheduleRepository, MapRepository, metadata


def init_map_db():
    """
    Initializes the graph database
    :return: None
    """

    # Initialize MapService to add the SubwayStations and CONNECTS relationships
    map_repo = MapRepository()
    map_repo.clear_db()
    map_service = MapService()

    total_nodes = 0
    total_relationships = 0

    directory = "data"
    csvs = ['{}/{}'.format(directory, csv) for csv in os.listdir(directory)]
    for csv in csvs:
        line = csv.split('/')[1].split('.')[0]

        df = pd.read_csv(csv)
        df.fillna('Not Found', inplace=True)

        for index in range(0, len(df)):
            row = df.loc[index]
            subway_station = SubwayStation.from_csv_row(row)
            subway_station.lines = [line for line in subway_station.lines if line != ""]
            if subway_station.station_name == "World Trade Center":
                subway_station.lines = "1,2,3,A,C,E,N,Q,R,W".split(",")
            elif subway_station.station_name == "Bleecker St":
                subway_station.lines = "4,6,6X,B,D,F,M".split(",")
            elif subway_station.station_name == "45 St":
                subway_station.lines = "N,R".split(",")
            elif subway_station.station_name == "Whitehall St":
                subway_station.lines = "N,Q,R,W".split(",")
            station_res = map_service.create_station(subway_station)
            if index > 0:
                prev_row = df.loc[index - 1]
                prev_subway_station = SubwayStation.from_csv_row(prev_row)
                train_line = TrainLine(start=prev_subway_station, stop=subway_station, line=line)
                train_line_res = map_service.create_connection(train_line)
                total_relationships += 1
            total_nodes += 1


def init_schedule_db():
    schedule_repository = ScheduleRepository()
    schedule_repository.clear_db()

    onlyfiles = ['{}/{}'.format('Trains', f) for f in listdir('Trains') if isfile(join('Trains', f))]
    filtered = list(filter(lambda k: 'csv' in k, onlyfiles))

    for i in range(len(filtered)):
        filename = str(filtered[i])
        df = pd.read_csv(filename)
        df.dropna(inplace=True)
        stations_lines = df.columns.values.tolist()
        stations = [' '.join(station.rstrip().split(" ")[:-1]) for station in stations_lines]
        lines = [lines.rstrip().split(" ")[-1][1:-1] for lines in stations_lines]
        stations = fix_schedule_exceptions(stations, lines)
        split_file_name = filename.split('/')[1].split('-')

        line = str(split_file_name[0])
        direction = str(split_file_name[-2])
        direction = direction + '-bound'

        documents_array = []

        for index, row in df.iterrows():
            values = row.values
            good_indices = [i for i in range(0, len(values)) if values[i] != "—" and values[i] != np.nan
                            and values[i] != "-"]
            try:
                times = [values[i].rstrip() \
                             .replace("#", '') \
                             .replace("*", "") \
                             .replace("+", "") \
                             .replace("^", "") \
                             .lstrip() \
                             .rstrip() for i in good_indices]
            except (IndexError, ValueError) as e:
                print(e)
            curr_stations = [stations[i] for i in good_indices]
            try:
                new_times = [datetime.strptime(time, "%H:%M") for time in times]
                prev_time = new_times[0]
                for j in range(1, len(new_times)):
                    if new_times[j] < prev_time:
                        new_times[j] = new_times[j].replace(year=1900, month=1, day=2)
                        prev_time = new_times[j]

                res = {curr_stations[j]: new_times[j] for j in range(len(curr_stations))}
            except ValueError:
                continue
            train = {
                "Line": line,
                "Direction": direction,
                "Schedule": res
            }

            documents_array.append(train)

        schedule_repository.bulk_insert_schedules(documents_array)


def fix_schedule_exceptions(stations, lines):
    """
    Fixes errors in station names and lines for the Schedule Collection
    :param stations: list of stations
    :param lines: list of lines
    :return:
    """
    for i in range(0, len(stations)):
        station = stations[i]
        if station == "Wtc - Cortlandt" or station == "Park Place Station" or station == "World Trade Center":
            stations[i] = "World Trade Center"
            lines[i] = "1,2,3,A,C,E,N,Q,R,W"
        if station == "51 St" or station == "Lexington Av/53 St":
            stations[i] = "Lexington Av/53 St"
            lines[i] = "4,6,6X,E,M"
        if station == "Lexington Av/63 St" or station == "Lexington Av / 59 St":
            stations[i] = "Lexington Av / 59 St"
            lines[i] = "4,5,6,F,N,Q,R"
        if station == "Broadway-Lafayette St" or station == "Bleecker St":
            stations[i] = "Bleecker St"
            lines[i] = "4,6,6X,B,D,F,M"
        if station == "E 180th":
            lines[i] = "2,5"
        if station == "61 St":
            stations[i] = "New Utrecht Av"
            lines[i] = "D,N,W"
        if station == "Canal St" and "6" in lines[i]:
            lines[i] = "N,Q,R,J,Z,4,6"
        if station == "East 174 Street Station Subway":
            lines[i] = "2,5"
        if station == "Jay St - Metrotech":
            lines[i] = "A,C,F,N,Q,R"
        if station == "45 St":
            lines[i] = "N,R"
        if station == "Court St":
            lines[i] = "N,Q,R"
        if station == "Rector St" and lines[i] == "N,R":
            lines[i] = "N,Q,R"
        if station == "City Hall":
            lines[i] = "N,Q,R"
        if station == "Whitehall St":
            lines[i] = "N,Q,R,W"
        if station == "45 St":
            lines[i] = "N,R"

    stations = ["{} [{}]".format(station, ','.join(sorted(line.split(','))).upper()) for station, line in
                zip(stations, lines)]
    return stations


def init_user_and_trip_db():
    """
    Drops the user and trip tables and then instantiates them
    :return: None
    """
    users = Table('users', metadata,
                  Column('user_id', Integer, primary_key=True),
                  Column('email', String(50)),
                  Column('password', LargeBinary()),
                  Column('is_admin', Integer, default=0))

    trips = Table('trips', metadata,
                  Column('user_id', Integer, primary_key=True),
                  Column('timestamp', DateTime, primary_key=True),
                  Column('start', String(100)),
                  Column('stop', String(100)),
                  Column('time', Integer))


    metadata.drop_all()
    metadata.create_all()


if __name__ == "__main__":
    init_map_db()
    init_schedule_db()
    init_user_and_trip_db()