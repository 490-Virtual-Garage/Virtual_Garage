from database import Base, engine
from models import User

Base.metadata.create_all(bind=engine)

print("Users table created successfully!")
