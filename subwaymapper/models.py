from __future__ import annotations
from sqlalchemy import create_engine, Integer, String, Column, Date, ForeignKey, \
    PrimaryKeyConstraint, func, desc, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, backref, relationship
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.types import LargeBinary

from subwaymapper import login_manager
from flask_login import UserMixin

Base = declarative_base()

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

class User(Base, UserMixin):
	__tablename__ = 'users'

	id = Column(Integer, primary_key=True, unique =True)
	email = Column(String(50))
	password = Column(LargeBinary())
	is_admin = Column(Integer)

	def __repr__(self):
		obj = {
			'id': self.id,
			'email': self.email,
			'password': self.password,
			'is_admin': self.is_admin
		}
		return "{0},{1},{2},{3}".format(self.id, self.email, self.password, self.is_admin)


class Schedule:
    def __init__(self,
                 line: str = None,
                 direction: str = None,
                 schedule: [] = None):
        self.line = line
        self.direction = direction
        self.schedule = schedule

    @classmethod
    def from_mongo(cls, query: {}) -> Schedule:
        '''
        Creates a Schedule object from Mongo query result
        :param schedule: a Mongo db querey result
        :return: A SubwayStation object with properties equal to the property of the node
        '''
        return cls(
            line=query['Line'],
            direction=query['Direction'],
            schedule=query['Schedule']
        )