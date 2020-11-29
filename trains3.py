import pymongo
from pymongo import MongoClient
import re
import pandas as pd
import numpy as np
from os import walk
from os import listdir
from os.path import isfile, join

#mongodb://localhost:27017/
myclient = MongoClient('mongodb://localhost:27017/')

db = myclient["Train"]
collection = db["schedule"]

collection.delete_many({})

onlyfiles = [f for f in listdir('Trains') if isfile(join('Trains', f))]
#print(onlyfiles)

filtered = list(filter(lambda k: 'csv' in k, onlyfiles))

#print(filtered)


for i in range(len(filtered)):
	filename = str(filtered[i])
	df = pd.read_csv('1-train-forward.csv')
	stations = df.columns.values.tolist()
	#print(stations)
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
	  #res['Line'] = line
	  #res['Direction'] = direction

	  train = {
	  	  "Line":line,
		  "Direction": direction,
		  "Schedule":res
	  }
	  
	  documents_array.append(train)
	  #collection.insert_one(train)
	  #print (res) 
	
	collection.insert_many(documents_array)