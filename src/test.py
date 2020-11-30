from src.models import SubwayStation, TrainLine
from src.service import MapService
from src.repository import MapRepository
from src.database import init_db
import matplotlib.pyplot as plt

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



map_service = MapService()
map_repository = MapRepository()

print(map_repository.stations_with_line_without_relationship("4"))


# stat = map_service.get_station_by_station_name("Liberty Av")

# stations = map_service.get_stations_by_line("S")
# longitude = [station.longitude for station in stations if isinstance(station.longitude, float)]
# latitude = [station.latitude for station in stations if isinstance(station.longitude, float)]

# reroute = map_service.get_station_by_station_name("Grand Central 42 St")
# start = map_service.get_station_by_station_name("14 St-Union Sq")
# stop = map_service.get_station_by_station_name("Woodlawn")
#
# map_service.set_station_status_out_of_order(reroute)
#
#
# res = map_service.get_shortest_path(start, stop)
# print(res)

