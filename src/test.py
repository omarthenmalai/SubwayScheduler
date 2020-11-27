from src.models import SubwayStation, TrainLine
from src.service import MapService
from src.repository import MapRepository
from src.database import init_db

# Fully Mapped:
# 1
# 1 Express
# 2
# 2 Express
# 4
# 4 Express
# 6
# 6 Express

# TODO:
# Fix split in Bronx 5 line
# Fix "7 Av" station for B-line. There are two instances with the same name

MapRepository.clear_db()
init_db()


map_service = MapService()
map_repository = MapRepository()

start = SubwayStation("170 St",
                      '''
                      Utica Ave and Eastern Parkway, Schenectady Ave and Eastern Parkway
                      ''',
                      None)
stop = SubwayStation('176 St',
                     '''
                     Jerome Ave and Burnside Ave
                     ''',
                     None)

stat = SubwayStation(station_name="Grand Central 42 St")
stat2 = SubwayStation(station_name="14 St-Union Sq")

map_service.set_station_status_out_of_order(stat)
# map_service.set_station_status_normal(stat)
map_service.set_station_status_out_of_order(stat2)

