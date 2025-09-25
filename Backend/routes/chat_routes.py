# routes/chat_routes.py

from fastapi import APIRouter, Depends, HTTPException
from models import ChatRequest, ChatResponse
import auth
from chatbot import create_chat_executor

server = APIRouter()

@server.post("/", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest, 
    user_id: str = Depends(auth.get_curren_user)
):
    """
    Handles a chat request. Requires user authentication.
    The `user_id` is automatically extracted from the bearer token.
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
        
    # Create an executor with memory specific to this user
    executor = create_chat_executor(user_id)
    
    try:
        # Asynchronously invoke the agent with the user's message
        result = await executor.ainvoke({"input": request.message})
        return ChatResponse(response=result["output"])
    except Exception as e:
        # Handle potential errors during agent execution
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")