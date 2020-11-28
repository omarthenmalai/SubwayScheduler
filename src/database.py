from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import os

# Local imports
from src.models import SubwayStation, TrainLine
from src.service import MapService
from src.station_scraper import VALID_LINES






def init_db():
    # print(os.getcwd())

    # Dataframe of subway stations
    subway_stations = pd.read_csv("data/subway_stations.csv")

    # Collate stations with the same names
    collated_stations = collate_stations(subway_stations)

    # Initialize MapService to add nodes and edges
    map_service = MapService()


    collated_stations.to_csv('test.csv', index=False)
    # Create a node for each station with the station name, entrances, and lines
    for index, row in collated_stations.iterrows():
        lines = row['Lines'].split(',')
        lines = [x for x in lines if x != '']
        subway_station = SubwayStation(station_name=row['Station'],
                                       borough=row['Borough'],
                                       entrances=row['Entrances'],
                                       lines=lines,
                                       status="Normal")
        map_service.create_station(subway_station)


    # Create the edges for each line between the relevant stations
    # csvs = os.listdir('data')
    # csvs = [x for x in csvs if len(x) == 5]
    # csvs = csvs[1:]
    # csvs = ['2.csv', '3.csv', '4.csv', '6.csv']
    csvs = VALID_LINES
    for csv in csvs:
        line = pd.read_csv('data/' + csv + '.csv')
        for i in range(0, len(line)-1):

            # Create the SubwayStation for the start of the connection
            start_name = line.loc[i, 'Station']
            start_entrances = line.loc[i, 'Entrances']
            start = SubwayStation(station_name=start_name,
                                  borough=line.loc[i, 'Borough'],
                                  entrances=start_entrances,
                                  lines=line.loc[i, 'Lines'])

            # Create the SubwayStation for the local stop connection
            local_stop_name = line.loc[i+1, 'Station']
            local_stop_entrances = line.loc[i+1, 'Entrances']
            local_stop = SubwayStation(station_name=local_stop_name,
                                       borough=line.loc[i+1, 'Borough'],
                                       entrances=local_stop_entrances,
                                       lines=line.loc[i, 'Lines'])

            # Line that will be used for the connection
            primary_line = str(line.loc[i, 'Primary Line'])


            # Create the TrainLine that represents the connections between the two stations
            train_line = TrainLine(start=start, stop=local_stop, line=primary_line)
            result = map_service.create_connection(train_line)
            if result is None:
                pass
            if line.loc[i, 'Express']:
                for j in range(i+1, len(line)):
                    if line.loc[j, 'Express']:

                        # Name and Entrances for the express stop
                        express_stop_name = line.loc[j, 'Station']
                        express_stop_entrances = line.loc[j, 'Entrances']

                        # Add 'Express' to the line name
                        primary_line += ' Express'

                        # Change the line and the stop of the TrainLine object
                        train_line.line = primary_line
                        train_line.stop = SubwayStation(station_name=express_stop_name,
                                                        borough=line.loc[j, 'Borough'],
                                                        entrances=express_stop_entrances)

                        # Create the connection between the start and the express_stop
                        map_service.create_connection(train_line)
                        break

    return None



def collate_stations(stations):
    entrance_collated_stations = pd.DataFrame(columns=['Station', 'Borough', 'Entrances', 'Lines'])

    for entrance in stations['Entrances'].unique():
        temp = stations.loc[stations['Entrances'] == entrance]

        # Only one instance
        if len(temp) == 1:
            entrance_collated_stations = pd.concat([entrance_collated_stations, temp[['Station', 'Borough', 'Entrances', 'Lines']]])
        # Multiple instances of the same entrance
        else:
            lines = ','.join(sorted(list(set(','.join(temp['Lines'].values.tolist()).split(',')))))
            station_name = temp['Station'].values.tolist()[0]
            borough = temp['Borough'].values.tolist()[0]
            primary_line = ','.join(sorted(temp['Primary Line'].astype(str).values.tolist()))
            entrance_collated_stations = pd.concat([entrance_collated_stations,
                                                    pd.DataFrame([[station_name, borough, entrance, lines]],
                                                                 columns=['Station', 'Borough', 'Entrances', 'Lines'])])

    collated_stations = pd.DataFrame(columns=['Station', 'Borough', 'Entrances', 'Lines'])
    for station in entrance_collated_stations['Station'].unique():
        temp = entrance_collated_stations.loc[entrance_collated_stations['Station'] == station]

        # Only one instance of the given station name. Station has been completely collated
        if len(temp) == 1:
            collated_stations = pd.concat([collated_stations, temp])
        # More than one instance of the given station name, If the lines match then they are the same station
        else:
            cleaned_lines = []
            for lines in temp['Lines']:
                temp_lines = lines.split(',')
                temp_lines = [x for x in temp_lines if 'Express' not in x and x != '']
                cleaned_lines.append([set(sorted(temp_lines))])

            collate = [x for x in range(0, len(cleaned_lines))]
            for i in range(0, len(cleaned_lines)):
                for j in range(0, len(cleaned_lines)):
                    if i == j:
                        continue
                    if cleaned_lines[i] == cleaned_lines[j] and collate[i] != collate[j]:
                        collate[j] = i

            temp2 = temp.copy()
            temp2['collate'] = collate

            for unq in temp2['collate'].unique():
                temp3 = temp2[temp2['collate'] == unq]
                if len(temp3) == 1:
                    del temp3['collate']
                    collated_stations = pd.concat([collated_stations, temp3])
                else:
                    combined_entrances = temp3['Entrances'].tolist()
                    borough = temp3['Borough'].tolist()[0]
                    lines = ','.join(sorted(list(set(','.join(temp3['Lines'].values.tolist()).split(',')))))
                    collated_stations = pd.concat([
                        collated_stations,
                        pd.DataFrame([[station, borough, combined_entrances, lines]],
                                     columns=['Station', 'Borough', 'Entrances', 'Lines'])
                    ])

    return collated_stations
