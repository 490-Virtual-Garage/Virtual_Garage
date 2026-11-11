from fastapi import FastAPI, Depends, HTTPException
<<<<<<< HEAD
from fastapi.middleware.cors import CORSMiddleware
=======
>>>>>>> origin/backend
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import User
<<<<<<< HEAD
from rule_engine.graph import diagnose, load_graph
=======
import firebase_admin
from firebase_admin import credentials, auth
>>>>>>> origin/backend

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


#Need firebase-service-account.json
#Don't commit this file
cred = credentials.Certificate("firebase-service-account.json")
firebase_admin.initialize_app(cred)

security = HTTPBearer()

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


#Authenticate token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    id_token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


<<<<<<< HEAD

# Expects a JSON body with "username" and "email" fields
=======
>>>>>>> origin/backend
@app.post("/users")
def create_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    firebase_uid = user["uid"]
    #Remove if not using username
    username = user.get("username")
    email = user["email"]

    existing_user = db.query(User).filter(User.userid == firebase_uid).first()

    if existing_user:
        return {
            "message": "User already exists",
            "userid": existing_user.userid
        }
    
    new_user = User(
        userid=firebase_uid,
        username=username,
        email=email
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": "User created successfully",
        "userid": new_user.userid,
<<<<<<< HEAD
        "username": new_user.username,
        "email": new_user.email,
        "is_active": new_user.is_active,
    }
=======
    }

#@app.get("/users/{user_id}")
#@app.patch("/users/{user_id}")
#@app.delete("/users/{user_id}")

#@app.post("/vehicles")
#@app.get("/vehicles/{vehicle_id}")
#@app.patch("/vehicles/{vehicle_id}")
#@app.delete("/vehicles/{vehicle_id}")

#@app.post("/captures")
#@app.get("/captures/{capture_id}")
#@app.patch("/captures/{capture_id}")
#@app.delete("/captures/{capture_id}")
>>>>>>> origin/backend
