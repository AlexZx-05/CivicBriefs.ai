import os
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from app.services.mailer import send_email
from app.services.subscriber_store import subscriber_store
from app.services.user_store import user_store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/test")
def test_auth():
    return {"message": "Auth route working"}


class SubscriptionRequest(BaseModel):
    name: str
    email: EmailStr


class PauseSubscriptionRequest(BaseModel):
    paused: bool


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=64)
    phone_number: str | None = Field(default=None, min_length=8, max_length=16)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=64)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)
    new_password: str = Field(..., min_length=6, max_length=64)


def _public_user(user: dict) -> dict:
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "phone_number": user.get("phone_number"),
        "created_at": user.get("created_at"),
    }


def _parse_token(authorization: str | None = Header(default=None)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header.",
        )
    return token


def _current_user(token: str = Depends(_parse_token)):
    user = user_store.resolve_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
        )
    return user, token


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup_user(payload: SignupRequest):
    try:
        user = user_store.create_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            phone_number=payload.phone_number,
        )
    except ValueError as exc:
        error_msg = str(exc)
        code = (
            status.HTTP_409_CONFLICT
            if "already exists" in error_msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=error_msg) from exc

    token = user_store.create_session(user_id=user["id"])
    subscriber_store.ensure_subscriber(name=user["name"], email=user["email"])
    return {"token": token, "user": _public_user(user)}


@router.post("/login")
def login_user(payload: LoginRequest):
    try:
        user = user_store.verify_credentials(
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        if "not found" in str(exc).lower() or "password" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password.",
        ) from exc

    token = user_store.create_session(user_id=user["id"])
    subscriber_store.ensure_subscriber(name=user["name"], email=user["email"])
    return {"token": token, "user": _public_user(user)}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, request: Request):
    # Always return success to avoid leaking whether an email exists.
    token = user_store.create_password_reset_token(email=payload.email)
    if token:
        public_base = (
            os.getenv("APP_PUBLIC_BASE_URL", "").strip()
            or str(request.base_url).rstrip("/")
        )
        reset_link = f"{public_base}/?reset_token={token}"
        send_email(
            recipient=payload.email,
            subject="CivicBriefs Password Reset",
            body=(
                "<p>Hi,</p>"
                "<p>We received a request to reset your CivicBriefs password.</p>"
                f'<p><a href="{reset_link}">Click here to reset password</a></p>'
                "<p>This link is valid for 30 minutes.</p>"
                "<p>If you did not request this, you can ignore this email.</p>"
            ),
        )
    return {
        "status": "success",
        "message": "If your email is registered, a password reset link has been sent.",
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    ok = user_store.reset_password_with_token(
        token=payload.token,
        new_password=payload.new_password,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    return {"status": "success", "message": "Password has been reset successfully."}


@router.get("/session")
def fetch_session(context=Depends(_current_user)):
    user, _ = context
    return {"user": _public_user(user)}


@router.post("/logout")
def logout_user(context=Depends(_current_user)):
    _, token = context
    user_store.drop_session(token)
    return {"status": "success"}


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_user(request: SubscriptionRequest):
    try:
        subscriber_store.ensure_subscriber(name=request.name, email=request.email)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    send_email(
        recipient=request.email,
        subject="Welcome to CivicBriefs.AI",
        body=f"<h3>Hi {request.name},</h3><p>Thanks for subscribing to our UPSC Daily Capsule!</p>",
    )

    return {
        "status": "success",
        "message": f"{request.name}, you have been subscribed to CivicBriefs.AI daily capsule.",
    }


@router.get("/subscription")
def get_subscription_status(context=Depends(_current_user)):
    user, _ = context
    status_payload = subscriber_store.get_status(email=user["email"])
    return {"status": "success", **status_payload}


@router.post("/subscription/pause")
def pause_subscription(payload: PauseSubscriptionRequest, context=Depends(_current_user)):
    user, _ = context
    try:
        status_payload = subscriber_store.set_paused(email=user["email"], paused=payload.paused)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    message = "Delivery paused." if status_payload["paused"] else "Delivery resumed."
    return {"status": "success", "message": message, **status_payload}
