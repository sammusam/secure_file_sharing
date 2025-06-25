from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from app.routes import client_user, ops_user
from app.auth import decode_access_token
from app.models import files_collection
import base64

app = FastAPI()

# Routers
app.include_router(client_user.router)
app.include_router(ops_user.router)

# Health check endpoint
@app.get("/")
def root():
    return {"message": "Secure File Sharing API is running 🚀"}

# Ping DB
@app.get("/ping")
def ping():
    return {"message": "MongoDB is alive 🧠"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="client/login")

# Secure download
@app.get("/download/{encrypted_id}")
def secure_download(encrypted_id: str, token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload or payload.get("role") != "client_user":
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        file_id = base64.urlsafe_b64decode(encrypted_id.encode()).decode()
        file_entry = files_collection.find_one({"file_id": file_id})
        if not file_entry:
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(file_entry["path"], filename=file_entry["filename"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid link")
