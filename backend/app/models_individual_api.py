# Alternative model if each user has their own API key/secret

class UserCreateWithOwnAPI(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.USER
    
    # Each user provides their own API credentials
    zerodha_api_key: str           # User's own API key from developer console
    zerodha_api_secret: str        # User's own API secret from developer console
    zerodha_user_id: str           # User's trading account ID
    zerodha_password: str          # User's trading account password  
    zerodha_totp_key: str          # User's TOTP secret

class UserInDBWithOwnAPI(UserBase):
    id: str
    hashed_password: str
    
    # Encrypted API credentials (user's own)
    zerodha_api_key_encrypted: str
    zerodha_api_secret_encrypted: str
    
    # Encrypted login credentials
    zerodha_user_id: str
    zerodha_password_encrypted: str
    zerodha_totp_key_encrypted: str
    
    created_at: datetime
    last_login: Optional[datetime] = None
    zerodha_access_token_file: Optional[str] = None