from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from app.schemas import UserSignup, UserLogin
from app.models import users_collection, files_collection
from app.auth import hash_password, verify_password, create_access_token, decode_access_token
import uuid, os

router = APIRouter(prefix="/ops", tags=["Ops User"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="ops/login")

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/signup")
def signup(user: UserSignup):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(400, detail="Email already registered")
    if user.role != "ops_user":
        raise HTTPException(403, detail="Only ops_user allowed")
    users_collection.insert_one({
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role
    })
    return {"message": "Ops user registered"}

@router.post("/login")
def login(user: UserLogin):
    db_user = users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(401, detail="Invalid credentials")
    if db_user["role"] != "ops_user":
        raise HTTPException(403, detail="Unauthorized role")
    token = create_access_token({"sub": user.email, "role": "ops_user"})
    return {"access_token": token, "token_type": "bearer"}

def get_current_ops_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "ops_user":
        raise HTTPException(401, detail="Unauthorized")
    return payload

@router.post("/upload")
def upload_file(file: UploadFile = File(...), user=Depends(get_current_ops_user)):
    # ✅ Validate file extension
    ALLOWED_EXTENSIONS = {".pptx", ".docx", ".xlsx"}
    ext = os.path.splitext(file.filename)[1]
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    files_collection.insert_one({
        "file_id": file_id,
        "filename": file.filename,
        "path": file_path
    })
    return {"file_id": file_id, "message": "Upload successful"}

