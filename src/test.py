from src.models import SubwayStation, TrainLine, Schedule, User
from src.service import MapService, ScheduleService, UserService
from src.repository import MapRepository, ScheduleRepository, UserRepository
from src.database import init_map_db, init_schedule_db
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import timeit


init_schedule_db()
init_map_db()
map_service = MapService()
map_repository = MapRepository()
schedule_repository = ScheduleRepository()
schedule_service = ScheduleService()
user_service = UserService()


# user = User("admin@gmail.com", 'test', True)
# user_service.add_user(user)

