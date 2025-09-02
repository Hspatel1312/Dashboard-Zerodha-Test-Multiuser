# backend/app/database.py - SQLite Database with SQLAlchemy for Multi-User Support
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from datetime import datetime
import os
import uuid
from typing import Optional, List
from .models import UserCreate, UserUpdate

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption for sensitive Zerodha credentials
def get_or_create_encryption_key() -> bytes:
    """Get or create encryption key for sensitive data"""
    key_file = "encryption.key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        return key

encryption_key = get_or_create_encryption_key()
cipher_suite = Fernet(encryption_key)

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data like passwords and TOTP keys"""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# SQLAlchemy User Model
class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Authentication
    hashed_password = Column(String, nullable=False)
    
    # Zerodha credentials (encrypted)
    zerodha_api_key_encrypted = Column(Text, nullable=False)
    zerodha_api_secret_encrypted = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # File paths
    zerodha_access_token_file = Column(String, nullable=True)
    user_data_directory = Column(String, nullable=False)

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User CRUD operations
class UserService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> UserDB:
        """Create a new user"""
        # Check if username already exists
        if UserService.get_user_by_username(db, user_data.username):
            raise ValueError("Username already exists")
        
        # Check if email already exists
        if UserService.get_user_by_email(db, user_data.email):
            raise ValueError("Email already exists")
        
        # Generate user ID and create user directory
        user_id = str(uuid.uuid4())
        user_data_dir = f"user_data/{user_id}"
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Create database user
        db_user = UserDB(
            id=user_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=user_data.is_active,
            hashed_password=UserService.get_password_hash(user_data.password),
            zerodha_api_key_encrypted=encrypt_sensitive_data(user_data.zerodha_api_key),
            zerodha_api_secret_encrypted=encrypt_sensitive_data(user_data.zerodha_api_secret),
            zerodha_access_token_file=f"{user_data_dir}/zerodha_access_token.txt",
            user_data_directory=user_data_dir
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[UserDB]:
        """Get user by ID"""
        return db.query(UserDB).filter(UserDB.id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[UserDB]:
        """Get user by username"""
        return db.query(UserDB).filter(UserDB.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[UserDB]:
        """Get user by email"""
        return db.query(UserDB).filter(UserDB.email == email).first()
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[UserDB]:
        """Update user information"""
        db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if not db_user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Handle sensitive data encryption
        if "zerodha_api_key" in update_data:
            db_user.zerodha_api_key_encrypted = encrypt_sensitive_data(
                update_data.pop("zerodha_api_key")
            )
        
        if "zerodha_api_secret" in update_data:
            db_user.zerodha_api_secret_encrypted = encrypt_sensitive_data(
                update_data.pop("zerodha_api_secret")
            )
        
        # Update other fields
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_last_login(db: Session, user_id: str) -> None:
        """Update user's last login timestamp"""
        db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
        if db_user:
            db_user.last_login = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def list_users(db: Session) -> List[UserDB]:
        """List all users"""
        return db.query(UserDB).all()
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[UserDB]:
        """Authenticate user with username and password"""
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        if not UserService.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    @staticmethod
    def get_decrypted_zerodha_credentials(user: UserDB) -> dict:
        """Get decrypted Zerodha credentials for a user"""
        return {
            "api_key": decrypt_sensitive_data(user.zerodha_api_key_encrypted),
            "api_secret": decrypt_sensitive_data(user.zerodha_api_secret_encrypted)
        }