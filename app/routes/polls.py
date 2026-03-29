from fastapi import APIRouter, HTTPException, Header
from app.db import read_json, write_json
from app.auth import decode_token
from app.models import VoteRequest, CreatePollRequest
import uuid

router = APIRouter(prefix="/polls", tags=["Polls"])


def get_current_user(authorization: str):
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


# ─── GET ALL ACTIVE POLLS ──────────────────────────────────
@router.get("/")
def get_polls():
    polls = read_json("polls.json")
    return [p for p in polls if p["is_active"]]


# ─── GET SINGLE POLL ───────────────────────────────────────
@router.get("/{poll_id}")
def get_poll(poll_id: str):
    polls = read_json("polls.json")
    poll = next((p for p in polls if p["id"] == poll_id), None)
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll


# ─── VOTE ON POLL ──────────────────────────────────────────
@router.post("/vote")
def vote(data: VoteRequest, authorization: str = Header(...)):
    get_current_user(authorization)
    polls = read_json("polls.json")

    poll_idx = next((i for i, p in enumerate(polls) if p["id"] == data.poll_id), None)
    if poll_idx is None:
        raise HTTPException(status_code=404, detail="Poll not found")

    if not polls[poll_idx]["is_active"]:
        raise HTTPException(status_code=400, detail="Poll is closed")

    opt_idx = next((i for i, o in enumerate(polls[poll_idx]["options"]) if o["id"] == data.option_id), None)
    if opt_idx is None:
        raise HTTPException(status_code=404, detail="Option not found")

    polls[poll_idx]["options"][opt_idx]["votes"] += 1
    polls[poll_idx]["total_votes"] += 1
    write_json("polls.json", polls)

    return {"message": "Vote recorded", "poll": polls[poll_idx]}


# ─── CREATE POLL (cook only) ───────────────────────────────
@router.post("/")
def create_poll(data: CreatePollRequest, authorization: str = Header(...)):
    user = get_current_user(authorization)
    if user.get("role") != "cook":
        raise HTTPException(status_code=403, detail="Only cooks can create polls")

    cooks = read_json("cooks.json")
    cook = next((c for c in cooks if c["user_id"] == user["sub"]), None)
    if not cook:
        raise HTTPException(status_code=404, detail="Cook profile not found")

    polls = read_json("polls.json")
    # Close existing polls for this cook
    for p in polls:
        if p["cook_id"] == cook["id"]:
            p["is_active"] = False

    new_poll = {
        "id": f"poll_{uuid.uuid4().hex[:8]}",
        "cook_id": cook["id"],
        "cook_name": cook["name"],
        "title": data.title,
        "is_active": True,
        "closes_at": "",
        "total_votes": 0,
        "options": [
            {"id": f"opt_{uuid.uuid4().hex[:6]}", "dish": dish, "description": "", "votes": 0}
            for dish in data.options
        ]
    }

    polls.append(new_poll)
    write_json("polls.json", polls)
    return {"message": "Poll created", "poll": new_poll}
