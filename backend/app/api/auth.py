from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

FAKE_USERS = {
    "officer1": {"password": "1234", "user_id": 1},
    "officer2": {"password": "officer2123", "user_id": 2},
    "officer3": {"password": "officer3123", "user_id": 3},
    "officer4": {"password": "officer4123", "user_id": 4}
}

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):

    user = FAKE_USERS.get(data.username)

    if user and user["password"] == data.password:
        return {
            "message": "Login successful",
            "username": data.username,
            "user_id": user["user_id"]
        }

    raise HTTPException(status_code=401, detail="Invalid credentials")