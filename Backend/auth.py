import bcrypt
from db import login_collection
import errors
from models import login_dict_create
from fastapi import Depends
import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

def hash_pass(passw:str)->str:
    salt = bcrypt.gensalt() #a random string behind pass to make it unique
    hashed = bcrypt.hashpw(passw.encode('utf-8'),salt) #encoded in utf-8 for bytes
    return hashed.decode('utf-8')

def verify_pass(input_pass:str, hashed_pass:str)->bool:
    return bcrypt.checkpw(input_pass.encode('utf-8'),hashed_pass.encode('utf-8'))

async def sign_in(creds:dict):
    query = await login_collection.find_one({"username":creds["username"]})
    if query:
        raise errors.UserExists
    creds["password"] = hash_pass(creds["password"])
    result = await login_collection.insert_one(creds)
    query = await login_collection.find_one({"_id":result.inserted_id})
    return query


def create_jwt_token(user_id:str)->str:
    payload = {
        "sub":user_id,
        "exp":datetime.now(timezone.utc) + timedelta(minutes=20) #for testing, will increase timedelta for production
    }
    token = jwt.encode(payload=payload,key=JWT_SECRET,algorithm=ALGORITHM)
    return token

async def verify_login(creds:dict) -> str:
    
    query = await login_collection.find_one({"username":creds["username"]})
    if query:
        if verify_pass(creds["password"],query["password"]):
            return create_jwt_token(user_id=str(query["_id"]))
        else:
            raise errors.InvalidPassword
    else:
        raise errors.UserDoesNotExist

def decode_user(token:str)->dict:
    try:
        payload = jwt.decode(token,JWT_SECRET,ALGORITHM)
        return payload
    except:
        return None

oauth_client = OAuth2PasswordBearer(tokenUrl="/login")

def get_curren_user(token:str = Depends(oauth_client)):
    payload = decode_user(token)
    if payload is None:
        raise errors.InvalidToken
    username = payload["sub"]
    if username is None:
        raise errors.InvalidPayload
    return username
