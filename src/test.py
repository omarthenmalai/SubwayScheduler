from src.models import SubwayStation, TrainLine
from src.service import MapService
from src.repository import MapRepository
from src.database import init_map_db, init_schedule_db
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

init_schedule_db()


# map_service = MapService()
# map_repository = MapRepository()

# print(map_repository.stations_with_line_without_relationship("4"))


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

# Testing
user_service = UserService()
user_service.add_user('4', 'Patrick', 'wewfefdfd', 0)

user_data = [{"user_id": 1, "email": "Fred Flinstone", "password": 13, "is_admin": 0},
                 {"user_id": 2, "email": "Fred Flinstone", "password": 14, "is_admin": 0},
				 {"user_id": 3, "email": "Patrick", "password": 14, "is_admin": 1},]

user_service.add_many_users(user_data)

query = user_service.get_user_by_email('Fred Flinstone')

user_service.add_user('6', 'Whipper', 'efefefe', 0)

print(query)
print(type(query))

query2 = user_service.login_user('Whipper','efefefe')
print(query2)
