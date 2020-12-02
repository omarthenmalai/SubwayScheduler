from src.models import SubwayStation, TrainLine, Schedule
from src.service import MapService, ScheduleService
from src.repository import MapRepository
from src.database import init_map_db, init_schedule_db
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import timeit

# init_schedule_db()

map_service = MapService()
map_repository = MapRepository()
schedule_service = ScheduleService()

start = map_service.get_station_by_station_name("Union Sq - 14 St")
end = map_service.get_station_by_station_name("125 St")

start_time = timeit.default_timer()
test = schedule_service.get_next_train_by_station_name_and_line(start_station=start,
                                                                end_station=end,
                                                                line='5',
                                                                time=datetime(year=1900, month=1,
                                                                              day=1, hour=19,
                                                                              minute=23))
test = Schedule.from_mongo(test)
schedule_service.remove_delay(schedule=test)

# schedule_service.delay_train(test, start.station_name, delay=timedelta(minutes=10))

# schedule_service.get_next_train_by_station_name_and_line("Grand Central - 42 St", "5 Av", "7X")
