import sys

from src.models import User
from src.service import UserService


"""
Short script to add an admin user. The command line parsing is bad but does the job...
"""

argv = sys.argv

if "-e" not in argv or "-p" not in sys.argv:
    print("Invalid arguments")
else:
    user = User(email=argv[argv.index("-e")+1], password=argv[argv.index("-p")+1], is_admin=True)
    user_service = UserService()
    user_service.add_user(user)
