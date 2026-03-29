from fastapi import APIRouter, HTTPException
from app.models import RegisterRequest, LoginRequest, TokenResponse
from app.auth import hash_password, verify_password, create_access_token
from app.db import read_json, write_json
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest):
    users = read_json("users.json")

    # Check if phone already exists
    existing = next((u for u in users if u["phone"] == data.phone), None)
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Create new user
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    new_user = {
        "id": user_id,
        "name": data.name,
        "phone": data.phone,
        "email": data.email or "",
        "password": hash_password(data.password),
        "role": data.role,
    }
    users.append(new_user)
    write_json("users.json", users)

    # If registering as cook, create a basic cook profile
    if data.role == "cook":
        cooks = read_json("cooks.json")
        cook_id = f"cook_{uuid.uuid4().hex[:8]}"
        cooks.append({
            "id": cook_id,
            "user_id": user_id,
            "name": data.name,
            "kitchen_name": f"{data.name}'s Kitchen",
            "location": "",
            "cuisine_types": [],
            "food_type": "veg",
            "rating": 0,
            "total_orders": 0,
            "trust_score": 0,
            "is_open": False,
            "delivery_mode": "partner",
            "price_from": 0,
            "bio": "",
            "cooking_since": "",
            "ratings_breakdown": {"taste": 0, "hygiene": 0, "quantity": 0},
            "menu": [],
            "plans": []
        })
        write_json("cooks.json", cooks)

    token = create_access_token({"sub": user_id, "role": data.role, "name": data.name})
    return TokenResponse(access_token=token, role=data.role, name=data.name, user_id=user_id)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    users = read_json("users.json")
    user = next((u for u in users if u["phone"] == data.phone), None)

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    token = create_access_token({"sub": user["id"], "role": user["role"], "name": user["name"]})
    return TokenResponse(access_token=token, role=user["role"], name=user["name"], user_id=user["id"])
