from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os
import pymongo
from pymongo import MongoClient
import re
import numpy as np
from os import walk
from os import listdir
from os.path import isfile, join

# Local imports
from src.models import SubwayStation, TrainLine
from src.service import MapService

"""
Lexington Av/63rd St == Lexington Av/59th St
Lexington Av/53rd St == 51 St
Broadway-Lafayette St == Bleecker St
"""


def init_db():
    # Initialize MapService to add the SubwayStations and CONNECTS relationships
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
    myclient = MongoClient(
        'mongodb+srv://m001-student:m001-mongodb-basics@sandbox.wweug.mongodb.net/<dbname>?retryWrites=true&w=majority')

    db = myclient["Train"]
    collection = db["schedule"]

    collection.delete_many({})

    onlyfiles = [f for f in listdir('Trains') if isfile(join('Trains', f))]

    filtered = list(filter(lambda k: 'csv' in k, onlyfiles))

    for i in range(len(filtered)):
        filename = str(filtered[i])
        df = pd.read_csv('1-train-forward.csv')
        stations = df.columns.values.tolist()

        split_file_name = filename.split('-')

        line = str(split_file_name[0])
        direction = str(split_file_name[-2])
        direction = direction + '-bound'

        print(line)
        print(direction)

        documents_array = []

        for index, row in df.iterrows():
            test_keys = stations
            test_values = row
            res = {test_keys[i]: test_values[i] for i in range(len(test_keys))}
            # res['Line'] = line
            # res['Direction'] = direction

            train = {
                "Line": line,
                "Direction": direction,
                "Schedule": res
            }

            documents_array.append(train)

        collection.insert_many(documents_array)
