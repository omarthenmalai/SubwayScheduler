from src.models import SubwayStation, TrainLine
from src.service import MapService
from src.repository import MapRepository
from src.database import init_db
import timeit

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
reroute = map_service.get_station_by_station_name("Grand Central 42 St")
start = map_service.get_station_by_station_name("14 St-Union Sq")
stop = map_service.get_station_by_station_name("Woodlawn")

map_service.set_station_status_out_of_order(reroute)


res = map_service.get_shortest_path(start, stop)
print(res)

