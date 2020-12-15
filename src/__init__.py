from flask import Flask
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from pymongo import MongoClient
from neo4j import GraphDatabase


app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


mysql_user = "root"
mysql_password = "123456"

# Database connections
try:
    mysql_engine = create_engine('mysql+pymysql://{}:{}@localhost/ece464_final'.format(mysql_user, mysql_password))
    mysql_engine.connect()
except OperationalError:
    print("Create MySQL database ece464_final")
    exit(0)
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "root"))
mongo_client = MongoClient('mongodb://localhost:27017/')


