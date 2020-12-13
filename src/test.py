from src.models import SubwayStation, TrainLine, Schedule
from src.service import MapService, ScheduleService
from src.repository import MapRepository, ScheduleRepository
from src.database import init_map_db, init_schedule_db
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import timeit

# TODO
# Deal with reroutes at the end of a line

# init_schedule_db()
init_map_db()
map_service = MapService()
map_repository = MapRepository()
schedule_repository = ScheduleRepository()
schedule_service = ScheduleService()

temp = map_service.get_station_by_name_and_entrance("Eastchester - Dyre Av", "3812 Dyre Avenue")
start = map_service.get_station_by_name_and_entrance("Union Sq - 14 St", "East 14th Street")
map_service.set_station_status_out_of_order(start)
stop = map_service.get_station_by_name_and_entrance("Grand Central - 42 St", "107 E 42 St")
map_service.set_station_status_out_of_order(stop)

map_service.set_station_status_normal(stop)

map_service.get_stations_by_line("5")

# stop = map_service.get_station_by_name_and_entrance("86 St", "1280 Lexington Avenue")



# path = map_service.get_shortest_path(start, stop)
# print(path)

# test = schedule_service.get_next_train_by_station_name_and_line(start_station=start,
#                                                                 end_station=stop,
#                                                                 line='6',
#                                                                 time=datetime(year=1900, month=1,
#                                                                               day=1, hour=19,
#                                                                               minute=23))

# test = Schedule.from_mongo(test)
# schedule_service.remove_delay(schedule=test)


# schedule_service.delay_train(test, start.station_name, delay=timedelta(minutes=10))

# delays = schedule_service.get_delays()

# print(delays)

# schedule_service.get_next_train_by_station_name_and_line("Grand Central - 42 St", "5 Av", "7X")
