from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from app.schemas import UserSignup, UserLogin
from app.models import users_collection, files_collection
from app.auth import hash_password, verify_password, create_access_token, decode_access_token
import base64, time, hmac, hashlib
from urllib.parse import urlencode
from app.utils.email import send_verification_email
import os

router = APIRouter(prefix="/client", tags=["Client User"])

# --- Secret for signing download links ---
from pymongo import MongoClient

client = MongoClient(os.getenv("MONGO_URI"))
db = client["secure_file_share"]
import os
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key").encode()


# --- Auth Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="client/login")

def get_current_client_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "client_user":
        raise HTTPException(status_code=401, detail="Invalid token or role")
    return payload

# --- Auth Routes ---
@router.post("/signup")
async def signup(user: UserSignup):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if user.role != "client_user":
        raise HTTPException(status_code=403, detail="Only client_user role allowed here")

    hashed_pw = hash_password(user.password)
    users_collection.insert_one({
        "email": user.email,
        "password": hashed_pw,
        "role": user.role,
        "is_verified": False  # <--- Add this field
    })

    # Send verification email
    token = create_access_token(
        {"sub": user.email, "role": "client_user"},
        expires_minutes=15
    )
    await send_verification_email(user.email, token)

    return {"message": "Verification email sent"}

@router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if db_user["role"] != "client_user":
        raise HTTPException(status_code=403, detail="Not authorized as client_user")
    if not db_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Email not verified")

    token = create_access_token({"sub": db_user["email"], "role": "client_user"})
    return {"access_token": token, "token_type": "bearer"}

# --- Client Routes ---
@router.get("/files")
def list_files(current_user=Depends(get_current_client_user)):
    files = files_collection.find({}, {"_id": 0, "file_id": 1, "filename": 1})
    return {"files": list(files)}
@router.get("/verify-email")
def verify_email(token: str):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    users_collection.update_one({"email": payload["sub"]}, {"$set": {"is_verified": True}})
    return {"message": "Email verified successfully"}

# --- Utility: Generate Secure Link ---
def generate_signed_download_url(file_id: str, expiry_seconds: int = 300):
    expires = int(time.time()) + expiry_seconds
    data = f"{file_id}:{expires}"
    sig = hmac.new(SECRET_KEY, data.encode(), hashlib.sha256).hexdigest()
    params = urlencode({
        "file_id": file_id,
        "expires": expires,
        "sig": sig
    })
    return f"http://localhost:8000/download?{params}"

# --- Secure Download Link Route ---
@router.get("/download-link/{file_id}")
def get_secure_link(file_id: str, current_user=Depends(get_current_client_user)):
    url = generate_signed_download_url(file_id)
    return {"download_link": url, "message": "success"}
