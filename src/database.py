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

# Local imports
from src.models import SubwayStation, TrainLine, Schedule
from src.service import MapService, ScheduleService
from src.repository import ScheduleRepository, MapRepository


def init_map_db():
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


# mongodb://localhost:27017/
def init_schedule_db():
    # myclient = MongoClient(
    #     'mongodb+srv://m001-student:m001-mongodb-basics@sandbox.wweug.mongodb.net/<dbname>?retryWrites=true&w=majority')

    # db = myclient["Train"]
    # collection = db["schedule"]

    schedule_repository = ScheduleRepository()
    schedule_repository.clear_db()

    onlyfiles = ['{}/{}'.format('Trains', f) for f in listdir('Trains') if isfile(join('Trains', f))]
    filtered = list(filter(lambda k: 'csv' in k, onlyfiles))

    for i in range(len(filtered)):
        filename = str(filtered[i])
        df = pd.read_csv(filename)
        df.dropna(inplace=True)
        stations = df.columns.values.tolist()
        stations = [' '.join(station.rstrip().split(" ")[:-1]) for station in stations]
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
                times = [values[i].rstrip()\
                             .replace("#", '')\
                             .replace("*", "")\
                             .replace("+", "")\
                             .replace("^", "")\
                             .lstrip()\
                             .rstrip() for i in good_indices]
                # times = [int(time.split(":")[0])*100 + int(time.split(":")[1]) for time in times]
            except (IndexError, ValueError) as e:
                print(e)
                continue
            curr_stations = [stations[i] for i in good_indices]
            try:
                res = {curr_stations[i]: datetime.strptime(times[i], "%H:%M") for i in range(len(curr_stations))}
                # res = {curr_stations[i]: times[i] for i in range(len(curr_stations))}
            except ValueError:
                continue
            train = {
                "Line": line,
                "Direction": direction,
                "Schedule": res
            }

            documents_array.append(train)

        schedule_repository.bulk_insert_schedules(documents_array)
        # collection.insert_many(documents_array)
