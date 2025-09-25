from fastapi import APIRouter, HTTPException

server = APIRouter()

@server.post("/")