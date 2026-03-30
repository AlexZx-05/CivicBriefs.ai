# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from app.api.routes.agents import router as agents_router
from app.api.routes.auth import router as auth_router
from app.api.routes.internal import router as internal_router
from app.api.routes.news import router as news_router
from app.services.capsule_scheduler import capsule_scheduler
from app.web.pages import render_dashboard_page, render_portal_page


@asynccontextmanager
async def lifespan(_: FastAPI):
    capsule_scheduler.start()
    try:
        yield
    finally:
        capsule_scheduler.stop()


app = FastAPI(title="CivicBriefs.AI", version="0.1.0", lifespan=lifespan)
@app.get("/health")
def health():
    return {"status": "ok", "service": "CivicBriefs backend running 🚀"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the News Agent router
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(agents_router)
app.include_router(internal_router)


@app.get("/", response_class=HTMLResponse)
def home():
    return render_portal_page()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return render_dashboard_page()
