from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

app = FastAPI()

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

@app.post("/captures")
def receive_capture(capture: dict):
    session = capture["session"]
    readings = capture["readings"]
    print(f"Got capture {session['session_id']} from {session['vehicle']}: {len(readings)} readings", flush=True)
    return {"status": "received", "session_id": session["session_id"], "readings": len(readings)}

class UserCreate(BaseModel):
    username: str
    email: str
    #Firebase should handle password
    #hashed_password: str

#Expects a JSON body with "username" and "email" fields
@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(username = user.username, email = user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "userid": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "is_active": new_user.is_active
    }
    
    
