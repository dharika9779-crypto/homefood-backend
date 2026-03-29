from fastapi import APIRouter, HTTPException, Header
from app.db import read_json, write_json
from app.auth import decode_token
from app.models import SubmitReviewRequest
import uuid
from datetime import datetime

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def get_current_user(authorization: str):
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# ─── GET REVIEWS FOR A COOK ────────────────────────────────
@router.get("/{cook_id}")
def get_reviews(cook_id: str):
    reviews = read_json("reviews.json")
    return [r for r in reviews if r["cook_id"] == cook_id]


# ─── SUBMIT REVIEW ─────────────────────────────────────────
@router.post("/")
def submit_review(data: SubmitReviewRequest, authorization: str = Header(...)):
    user = get_current_user(authorization)
    reviews = read_json("reviews.json")
    cooks = read_json("cooks.json")

    cook_idx = next((i for i, c in enumerate(cooks) if c["id"] == data.cook_id), None)
    if cook_idx is None:
        raise HTTPException(status_code=404, detail="Cook not found")

    new_review = {
        "id": f"review_{uuid.uuid4().hex[:8]}",
        "cook_id": data.cook_id,
        "student_name": user["name"],
        "rating": data.rating,
        "taste": data.taste,
        "hygiene": data.hygiene,
        "quantity": data.quantity,
        "comment": data.comment,
        "tags": data.tags,
        "created_at": datetime.utcnow().isoformat(),
    }
    reviews.append(new_review)
    write_json("reviews.json", reviews)

    # Recalculate cook average rating
    cook_reviews = [r for r in reviews if r["cook_id"] == data.cook_id]
    avg_rating = round(sum(r["rating"] for r in cook_reviews) / len(cook_reviews), 1)
    avg_taste = round(sum(r["taste"] for r in cook_reviews) / len(cook_reviews), 1)
    avg_hygiene = round(sum(r["hygiene"] for r in cook_reviews) / len(cook_reviews), 1)
    avg_quantity = round(sum(r["quantity"] for r in cook_reviews) / len(cook_reviews), 1)

    cooks[cook_idx]["rating"] = avg_rating
    cooks[cook_idx]["ratings_breakdown"] = {
        "taste": avg_taste,
        "hygiene": avg_hygiene,
        "quantity": avg_quantity
    }
    write_json("cooks.json", cooks)

    return {"message": "Review submitted", "review": new_review}
