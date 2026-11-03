from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from database import SessionLocal, Base, engine
from models import User
import firebase_admin
from firebase_admin import credentials, auth

app = FastAPI()
Base.metadata.create_all(bind=engine)

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
    session = capture["session"]
    readings = capture["readings"]
    print(f"Got capture {session['session_id']} from {session['vehicle']}: {len(readings)} readings", flush=True)
    return {"status": "received", "session_id": session["session_id"], "readings": len(readings)}

#Authenticate token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    id_token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


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