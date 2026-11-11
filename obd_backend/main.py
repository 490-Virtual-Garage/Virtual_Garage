from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import User
from rule_engine.graph import diagnose, load_graph

app = FastAPI()

origins = ["http://localhost:5173", "http://127.0.0.1:5173"] #frontend urls, 127... is from compose.yml, localhost from vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    print(
        f"Got capture {session['session_id']} from {session['vehicle']}: {len(capture['readings'])} readings",
        flush=True,
    )
    latest_capture = capture
    latest_diagnosis = diagnose(graph, capture)
    return latest_diagnosis


@app.get("/captures/latest")
def get_latest_capture():
    if latest_capture is None:
        raise HTTPException(status_code=404, detail="No capture data available")
    return latest_capture


@app.get("/diagnosis/latest")
def get_latest_diagnosis():
    if latest_diagnosis is None:
        raise HTTPException(status_code=404, detail="No diagnosis data available")
    return latest_diagnosis


class UserCreate(BaseModel):
    username: str
    email: str


# Expects a JSON body with "username" and "email" fields
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
        "is_active": new_user.is_active,
    }
