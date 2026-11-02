from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import User
from rule_engine.graph import diagnose, load_graph

app = FastAPI()
Base.metadata.create_all(bind=engine)
graph = load_graph()
latest_capture = None
latest_diagnosis = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/captures")
def receive_capture(capture: dict):
    global latest_capture, latest_diagnosis
    session = capture["session"]
    print(f"Got capture {session['session_id']} from {session['vehicle']}: {len(capture['readings'])} readings", flush=True)
    latest_capture = capture
    latest_diagnosis = diagnose(graph, capture)
    return latest_diagnosis

class UserCreate(BaseModel):
    username: str
    email: str

#Expects a JSON body with "username" and "email" fields
@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "userid": new_user.userid,
        "username": new_user.username,
        "email": new_user.email,
        "is_active": new_user.is_active
    }