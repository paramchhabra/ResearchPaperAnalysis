from pydantic import BaseModel, Field
from bson import ObjectId

class UserCreate(BaseModel):
    username:str = Field(description="Username")
    password:str = Field(description="Password")

class UserOut(BaseModel):
    id:str
    username:str

# --- NEW MODELS FOR CHAT ---
class ChatRequest(BaseModel):
    message: str = Field(description="The user's message to the chatbot")

class ChatResponse(BaseModel):
    response: str = Field(description="The chatbot's response")
# ---------------------------

#For testing
def login_dict_create(username:str, password:str)->dict:
    return {"username":username, "password":password}

def login_helper():...