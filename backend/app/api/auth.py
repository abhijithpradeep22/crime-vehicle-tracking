from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

FAKE_USERS = {
    "officer1": "1234",
    "admin": "admin123"
}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest):
    if data.username in FAKE_USERS and FAKE_USERS[data.username] == data.password:
        return {"message": "Login successful", "username": data.username}
    raise HTTPException(status_code=401, detail="Invalid credentials")