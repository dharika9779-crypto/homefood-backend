from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, cooks, orders, polls, reviews

app = FastAPI(
    title="HomeFood Connect API",
    description="Backend API for HomeFood Connect — Hyperlocal Homemade Food Marketplace",
    version="1.0.0"
)

# ─── CORS (allow React frontend to talk to this backend) ───
# NEW
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── REGISTER ALL ROUTES ───────────────────────────────────
app.include_router(auth.router)
app.include_router(cooks.router)
app.include_router(orders.router)
app.include_router(polls.router)
app.include_router(reviews.router)


# ─── ROOT ──────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Welcome to HomeFood Connect API",
        "docs": "/docs",
        "version": "1.0.0"
    }
