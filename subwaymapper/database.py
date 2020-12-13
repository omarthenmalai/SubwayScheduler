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
from subwaymapper.models import *
from subwaymapper.service import *
from subwaymapper.repository import *

def init_schedule_db():
   
    schedule_repository = ScheduleRepository()
    schedule_repository.clear_db()

    onlyfiles = [f for f in listdir('Trains') if isfile(join('Trains', f))]

    filtered = list(filter(lambda k: 'csv' in k, onlyfiles))

    for i in range(len(filtered)):
        filename = str(filtered[i])
        actual_filename = 'Trains/' + filename
        df = pd.read_csv(actual_filename)
        stations = df.columns.values.tolist()

        split_file_name = filename.split('-')

        line = str(split_file_name[0])
        direction = str(split_file_name[-2])
        direction = direction + '-Bound'

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

        schedule_repository.bulk_insert_schedules(documents_array)
        # collection.insert_many(documents_array)
