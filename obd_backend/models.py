from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"

    userid = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicleid = Column(Integer, primary_key=True, index=True)
    userid = Column(Integer, ForeignKey("users.userid"), ondelete="CASCADE", nullable=False, index=True)
    vin = Column(String, nullable=False)
