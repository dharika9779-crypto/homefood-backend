from pydantic import BaseModel
from typing import Optional, List


# ─── AUTH MODELS ───────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    password: str
    role: str  # "student" | "cook" | "delivery"


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: str


# ─── ORDER MODELS ──────────────────────────────────────────
class OrderItem(BaseModel):
    item_id: str
    name: str
    quantity: int
    price: float


class PlaceOrderRequest(BaseModel):
    cook_id: str
    items: List[OrderItem]
    order_type: str  # "one-time" | "subscription"
    plan_id: Optional[str] = None
    delivery_address: str
    promo_code: Optional[str] = None


# ─── REVIEW MODELS ─────────────────────────────────────────
class SubmitReviewRequest(BaseModel):
    cook_id: str
    order_id: str
    rating: int
    taste: int
    hygiene: int
    quantity: int
    comment: Optional[str] = ""
    tags: Optional[List[str]] = []


# ─── POLL MODELS ───────────────────────────────────────────
class VoteRequest(BaseModel):
    poll_id: str
    option_id: str


class CreatePollRequest(BaseModel):
    title: str
    options: List[str]  # list of dish names


# ─── COOK MODELS ───────────────────────────────────────────
class ToggleAvailabilityRequest(BaseModel):
    is_open: bool


class UpdateOrderStatusRequest(BaseModel):
    order_id: str
    status: str  # "preparing" | "ready" | "delivered"
