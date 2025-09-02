# backend/app/models.py - User Management Models
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    zerodha_api_key: str
    zerodha_api_secret: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    zerodha_api_key: Optional[str] = None
    zerodha_api_secret: Optional[str] = None

class UserInDB(UserBase):
    id: str
    hashed_password: str
    zerodha_api_key_encrypted: str
    zerodha_api_secret_encrypted: str
    created_at: datetime
    last_login: Optional[datetime] = None
    zerodha_access_token_file: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    full_name: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None

# User-specific Zerodha authentication request
class ZerodhaAuthRequest(BaseModel):
    request_token: Optional[str] = None
    
# Response models
class UserResponse(BaseModel):
    success: bool
    message: str
    user: Optional[User] = None
    
class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[Token] = None
    user: Optional[User] = None