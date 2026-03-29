from fastapi import APIRouter, HTTPException, Header
from app.db import read_json, write_json
from app.auth import decode_token
from app.models import ToggleAvailabilityRequest
from typing import Optional

router = APIRouter(prefix="/cooks", tags=["Cooks"])


def get_current_user(authorization: str):
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# ─── GET ALL COOKS ─────────────────────────────────────────
@router.get("/")
def get_all_cooks(food_type: Optional[str] = None, max_price: Optional[int] = None, open_only: Optional[bool] = None):
    cooks = read_json("cooks.json")

    if food_type and food_type != "all":
        cooks = [c for c in cooks if c["food_type"] == food_type]
    if max_price:
        cooks = [c for c in cooks if c["price_from"] <= max_price]
    if open_only:
        cooks = [c for c in cooks if c["is_open"]]

    # Return summary (not full menu details)
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "kitchen_name": c["kitchen_name"],
            "location": c["location"],
            "cuisine_types": c["cuisine_types"],
            "food_type": c["food_type"],
            "rating": c["rating"],
            "total_orders": c["total_orders"],
            "trust_score": c["trust_score"],
            "is_open": c["is_open"],
            "price_from": c["price_from"],
        }
        for c in cooks
    ]


# ─── GET SINGLE COOK PROFILE ───────────────────────────────
@router.get("/{cook_id}")
def get_cook(cook_id: str):
    cooks = read_json("cooks.json")
    cook = next((c for c in cooks if c["id"] == cook_id), None)
    if not cook:
        raise HTTPException(status_code=404, detail="Cook not found")

    reviews = read_json("reviews.json")
    cook_reviews = [r for r in reviews if r["cook_id"] == cook_id]

    return {**cook, "reviews": cook_reviews}


# ─── TOGGLE COOK AVAILABILITY ──────────────────────────────
@router.patch("/{cook_id}/availability")
def toggle_availability(cook_id: str, data: ToggleAvailabilityRequest, authorization: str = Header(...)):
    user = get_current_user(authorization)
    cooks = read_json("cooks.json")

    cook_index = next((i for i, c in enumerate(cooks) if c["id"] == cook_id and c["user_id"] == user["sub"]), None)
    if cook_index is None:
        raise HTTPException(status_code=403, detail="Not authorized or cook not found")

    cooks[cook_index]["is_open"] = data.is_open
    write_json("cooks.json", cooks)
    return {"message": "Availability updated", "is_open": data.is_open}


# ─── GET COOK DASHBOARD DATA ───────────────────────────────
@router.get("/{cook_id}/dashboard")
def get_cook_dashboard(cook_id: str, authorization: str = Header(...)):
    get_current_user(authorization)
    cooks = read_json("cooks.json")
    cook = next((c for c in cooks if c["id"] == cook_id), None)
    if not cook:
        raise HTTPException(status_code=404, detail="Cook not found")

    orders = read_json("orders.json")
    cook_orders = [o for o in orders if o["cook_id"] == cook_id]

    today_orders = [o for o in cook_orders if o.get("status") != "delivered"]
    weekly_earnings = sum(o["cook_earnings"] for o in cook_orders if o.get("status") == "delivered")

    return {
        "cook": cook,
        "stats": {
            "today_orders": len(today_orders),
            "weekly_earnings": weekly_earnings,
            "rating": cook["rating"],
            "active_subscribers": 8,  # fake for now
        },
        "orders": today_orders,
    }
