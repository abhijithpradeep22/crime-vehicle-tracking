from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

FAKE_USERS = {
    "officer1": {"password": "1234", "user_id": 1},
    "officer2": {"password": "officer2123", "user_id": 2},
    "officer3": {"password": "officer3123", "user_id": 3},
    "officer4": {"password": "officer4123", "user_id": 4},
    "officer5": {"password": "officer5123", "user_id": 5},
    "officer6": {"password": "officer6123", "user_id": 6},
    "officer7": {"password": "officer7123", "user_id": 7},
    "officer8": {"password": "officer8123", "user_id": 8},
    "officer9": {"password": "officer9123", "user_id": 9},
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