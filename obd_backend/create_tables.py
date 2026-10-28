from database import Base, engine
from models import User, Vehicle

Base.metadata.create_all(bind=engine)

print("Users table created successfully!")
