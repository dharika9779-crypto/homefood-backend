from fastapi import APIRouter, HTTPException, Header
from app.db import read_json, write_json
from app.auth import decode_token
from app.models import PlaceOrderRequest, UpdateOrderStatusRequest
import uuid
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["Orders"])

PLATFORM_FEE = 10
DELIVERY_FEE = 25
PROMO_CODES = {"SAVE10": 0.10, "FIRST50": 0.50}


def get_current_user(authorization: str):
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# ─── PLACE ORDER ───────────────────────────────────────────
@router.post("/")
def place_order(data: PlaceOrderRequest, authorization: str = Header(...)):
    user = get_current_user(authorization)
    orders = read_json("orders.json")
    cooks = read_json("cooks.json")

    cook = next((c for c in cooks if c["id"] == data.cook_id), None)
    if not cook:
        raise HTTPException(status_code=404, detail="Cook not found")

    # Calculate pricing
    items_total = sum(item.price * item.quantity for item in data.items)
    discount = 0
    if data.promo_code and data.promo_code in PROMO_CODES:
        discount = items_total * PROMO_CODES[data.promo_code]

    delivery_fee = 0 if cook["delivery_mode"] == "self" else DELIVERY_FEE
    total = items_total - discount + PLATFORM_FEE + delivery_fee

    order_id = f"order_{uuid.uuid4().hex[:8]}"
    new_order = {
        "id": order_id,
        "student_id": user["sub"],
        "student_name": user["name"],
        "cook_id": data.cook_id,
        "cook_name": cook["name"],
        "items": [item.dict() for item in data.items],
        "order_type": data.order_type,
        "delivery_address": data.delivery_address,
        "status": "preparing",
        "items_total": items_total,
        "discount": discount,
        "platform_fee": PLATFORM_FEE,
        "delivery_fee": delivery_fee,
        "total": total,
        "cook_earnings": items_total - discount,
        "promo_code": data.promo_code or "",
        "created_at": datetime.utcnow().isoformat(),
    }

    orders.append(new_order)
    write_json("orders.json", orders)
    return {"message": "Order placed successfully", "order": new_order}


# ─── GET STUDENT ORDER HISTORY ─────────────────────────────
@router.get("/my-orders")
def get_my_orders(authorization: str = Header(...)):
    user = get_current_user(authorization)
    orders = read_json("orders.json")
    my_orders = [o for o in orders if o["student_id"] == user["sub"]]
    return my_orders


# ─── UPDATE ORDER STATUS (cook/delivery) ───────────────────
@router.patch("/status")
def update_order_status(data: UpdateOrderStatusRequest, authorization: str = Header(...)):
    get_current_user(authorization)
    orders = read_json("orders.json")

    idx = next((i for i, o in enumerate(orders) if o["id"] == data.order_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Order not found")

    orders[idx]["status"] = data.status
    write_json("orders.json", orders)
    return {"message": "Status updated", "status": data.status}


# ─── GET DELIVERY PARTNER ORDERS ───────────────────────────
@router.get("/available-deliveries")
def get_available_deliveries(authorization: str = Header(...)):
    get_current_user(authorization)
    orders = read_json("orders.json")
    cooks = read_json("cooks.json")

    available = [o for o in orders if o["status"] == "ready"]
    result = []
    for order in available:
        cook = next((c for c in cooks if c["id"] == order["cook_id"]), {})
        result.append({
            **order,
            "pickup_location": cook.get("location", ""),
            "delivery_earnings": order["delivery_fee"],
        })
    return result
