# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import UserCreate, UserOut
import auth
import errors
from routes import chat_routes # --- NEW IMPORT ---

app = FastAPI()
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
# --- NEW: Include the chat router ---
app.include_router(chat_routes.server, prefix="/chat", tags=["Chat"])
# ------------------------------------

@app.post("/login")
async def login(user:UserCreate):
    data = user.model_dump()
    try:
        token = await auth.verify_login(data)
        return {"access_token":token, "token_type":"bearer"}
    except errors.InvalidPassword:
        raise HTTPException(status_code=401, detail="Invalid Password")
    except errors.UserDoesNotExist:
        raise HTTPException(status_code=404, detail="User Not Found")

@app.post("/signup", response_model=UserOut)
async def signup(user:UserCreate):
    data = user.model_dump()
    try:
        signin = await auth.sign_in(data)
        if signin:
            return UserOut(id=str(signin["_id"]),username=signin["username"])
    except errors.UserExists:
        raise HTTPException(status_code=409, detail="User Already Exists")