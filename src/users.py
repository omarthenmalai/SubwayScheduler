from sqlalchemy import create_engine, Integer, String, Column, Date, ForeignKey, \
    PrimaryKeyConstraint, func, desc, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, backref, relationship

engine = create_engine('mysql+pymysql://root:!57aOxX$sa*l@localhost/ece464-final', echo=True)
connection = engine.connect()

Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()
metadata = MetaData(engine)

users = Table('users', metadata,
				Column('user_id', Integer, primary_key=True),
				Column('email', String(50)),
				Column('password', String(160)),
				Column('is_admin', Integer, default = 0))

class User(Base):
	__tablename__ = 'users'

	user_id = Column(Integer, primary_key=True)
	email = Column(String(50))
	password = Column(String(160))
	is_admin = Column(Integer)

	def __repr__(self):
		return "<User(user_id={0}, email={1}, password={2})>".format(self.user_id, self.email, self.password)


# Clear all existing data to avoid problems when rerunning/debugging
metadata.drop_all()
metadata.create_all()

class UserRepository:
	def add_user(self, user_id, email, password, is_admin):
		# Here would be the password hashing code
		user = {
			"user_id": user_id,
			"email": email,
			"password": password,
			"is_admin": is_admin
		}
		connection.execute(users.insert(), user)
		session.commit()

	def add_many_users(self, user_array):
		connection.execute(users.insert(),user_array)

	def get_user_by_email(self, email: str):
		query = session.query(User).filter(User.email == email).all()
		
		return query


class ScheduleService:

	def __init__(self):
		self.repository = UserRepository()

	def add_user(self, user_id: User, email: User, password: User, is_admin: User):
		self.repository.add_user(user_id, email, password, is_admin)
		print("User created")
	
	def add_many_users(self, user_array: []):
		self.repository.add_many_users(user_array)
		print("Many Users created")

	def get_user_by_email(self,
                               email: User):
		result = self.repository.get_user_by_email(email)
        
		return result

# Testing
schedule_service = ScheduleService()
schedule_service.add_user('4', 'Patrick', 'wewfefdfd', 0)

user_data = [{"user_id": 1, "email": "Fred Flinstone", "password": 13, "is_admin": 0},
                 {"user_id": 2, "email": "Fred Flinstone", "password": 14, "is_admin": 0},
				 {"user_id": 3, "email": "Patrick", "password": 14, "is_admin": 1},]

schedule_service.add_many_users(user_data)

query = schedule_service.get_user_by_email('Fred Flinstone')

print(query[0])