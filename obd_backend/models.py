from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"

    userid = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=False, index=True)
    
    #Column for if a user is banned, suspended, etc. Used to whitelist certain users
    is_active = Column(Boolean, default=True, nullable=False)

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicleid = Column(Integer, primary_key=True, index=True)
    userid = Column(String, ForeignKey("users.userid", ondelete="CASCADE"), nullable=False, index=True)
    vin = Column(String, nullable=False)
    make = Column(String, nullable=False)
    model = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
