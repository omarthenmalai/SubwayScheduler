from src.models import SubwayStation, TrainLine, Schedule, User
from src.service import MapService, ScheduleService, UserService
from src.repository import MapRepository, ScheduleRepository, UserRepository
from src.database import init_map_db, init_schedule_db
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import timeit
import pymongo

# init_schedule_db()
# init_map_db()

# Start node None -> start
# End node none --> end

map_service = MapService()
map_repository = MapRepository()
schedule_repository = ScheduleRepository()
schedule_service = ScheduleService()
user_service = UserService()

stat = map_service.get_station_by_name_and_entrance("Astor Pl", "East 8th Street")
stop = map_service.get_station_by_name_and_entrance("Union Sq - 14 St", "East 14th Street")
test = schedule_service.get_next_train_by_station_name_and_line(stat, stop, "6", datetime(year=1900,
                                                                                            month=1,
                                                                                            day=1,
                                                                                            hour=13,
                                                                                            minute=48,
                                                                                            second=0))

print(test)
# start = map_service.get_station_by_name_and_entrance("Dekalb Av", "340 Flatbush Ave Extension")
# stop = map_service.get_station_by_name_and_entrance("Atlantic Av - Barclays Ctr", "590 Atlantic Ave")
# start_time = datetime.now().replace(year=1900, month=1, day=1, hour=10, minute=1, second=0)

# stations = schedule_service.get_next_train_by_station_name_and_line(start, stop, 'N', time=start_time)




map_service.get_stations_by_line("1")



# user = User("admin@gmail.com", 'test', True)
# user_service.add_user(user)

