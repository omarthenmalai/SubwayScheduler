from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

#Start up the database stuff here
from subwaymapper import routes
from subwaymapper import models
from subwaymapper import service
from subwaymapper import database
from subwaymapper.database import *

init_schedule_db()
