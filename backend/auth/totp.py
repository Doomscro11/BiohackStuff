# TOTP (Time-based One-Time Password) for Admin 2FA
import os
import base64
import pyotp
from motor.motor_asyncio import AsyncIOMotorClient

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'peptimancer_db')]
users_collection = db['users']

async def ensure_totp_secret(user_id: str) -> str:
    """
    Ensure user has a TOTP secret, create one if not exists
    Returns the secret key
    """
    doc = await users_collection.find_one({"_id": user_id})
    
    if doc and doc.get("otpSecret"):
        return doc["otpSecret"]
    
    # Generate new TOTP secret
    secret = base64.b32encode(os.urandom(20)).decode("utf-8").strip("=")
    
    await users_collection.find_one_and_update(
        {"_id": user_id},
        {"$set": {"otpSecret": secret}},
        upsert=True
    )
    
    return secret

def get_otpauth_uri(email: str, secret: str, issuer: str = "Peptimancer") -> str:
    """
    Generate OTP Auth URI for QR code generation
    """
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)

async def verify_totp(user_id: str, code: str) -> bool:
    """
    Verify TOTP code for user
    Returns True if valid, False otherwise
    """
    doc = await users_collection.find_one({"_id": user_id}, {"otpSecret": 1})
    
    if not doc or not doc.get("otpSecret"):
        return False
    
    totp = pyotp.TOTP(doc["otpSecret"])
    # valid_window=1 allows ±30s time drift
    return totp.verify(code, valid_window=1)
