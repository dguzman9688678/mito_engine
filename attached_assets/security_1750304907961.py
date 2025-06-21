import redis
from cryptography.fernet import Fernet
import bcrypt
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid
from config import config
from database import db_manager
from logging_setup import logger

class AdvancedSecurityManager:
    def __init__(self):
        self.fernet_key = Fernet.generate_key()
        self.fernet = Fernet(self.fernet_key)
        self.jwt_secret = config.SECRET_KEY
        self.redis = db_manager.redis_client

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, password: str, hash_pw: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hash_pw.encode("utf-8"))

    def generate_api_key(self) -> str:
        return secrets.token_hex(config.API_KEY_LENGTH // 2)

    def hash_api_key(self, api_key: str) -> str:
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def generate_jwt_token(self, user_id: str, role: str, expires_hours: int = None) -> str:
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=expires_hours or config.TOKEN_EXPIRY_HOURS)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_jwt_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except Exception as e:
            logger.error("jwt_verification_failed", error=str(e))
            return {}

    def encrypt(self, plaintext: str) -> str:
        return self.fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.fernet.decrypt(ciphertext.encode()).decode()

    def rate_limit_check(self, user_id: str, action: str, limit: int, window_seconds: int) -> bool:
        key = f"rate:{user_id}:{action}"
        current = self.redis.get(key)
        if current and int(current) >= limit:
            return False
        pipe = self.redis.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, window_seconds)
        pipe.execute()
        return True

    def log_auth_attempt(self, user_id: str, success: bool):
        logger.info("auth_attempt", user_id=user_id, success=success, timestamp=datetime.utcnow().isoformat())