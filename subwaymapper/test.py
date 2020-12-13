from subwaymapper.models import User
from subwaymapper.service import *
from subwaymapper.repository import *

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