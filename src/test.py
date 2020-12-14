from src.models import SubwayStation, TrainLine, Schedule, User
from src.service import MapService, ScheduleService, UserService
from src.repository import MapRepository, ScheduleRepository, UserRepository
from src.database import init_map_db, init_schedule_db
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import timeit


# init_schedule_db()
# init_map_db()

# Start node None -> start
# End node none --> end

map_service = MapService()
map_repository = MapRepository()
schedule_repository = ScheduleRepository()
schedule_service = ScheduleService()
user_service = UserService()



# start = map_service.get_station_by_name_and_entrance("Van Cortlandt Park - 242 St", "5959 Broadway")
# stop = map_service.get_station_by_name_and_entrance("238 St", "Broadway")
# map_service.set_station_status_out_of_order(start)
# map_service.set_station_status_out_of_order(stop)




# start = map_service.get_station_by_name_and_entrance("South Ferry Loop", "Peter Minuit Plaza")
# stop = map_service.get_station_by_name_and_entrance("Rector St", "69 Greenwich Street")
# map_service.set_station_status_out_of_order(start)
# map_service.set_station_status_out_of_order(stop)


map_service.get_stations_by_line("1")



# user = User("admin@gmail.com", 'test', True)
# user_service.add_user(user)

