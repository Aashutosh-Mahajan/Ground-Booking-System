from cryptography.fernet import Fernet
import os

SECRET_KEY = os.environ.get("FIELD_ENCRYPTION_KEY")

if not SECRET_KEY:
    raise Exception("FIELD_ENCRYPTION_KEY not set")

fernet = Fernet(SECRET_KEY.encode())

def encrypt_data(data: str) -> str:
    if data is None:
        return None
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    if data is None:
        return None
    return fernet.decrypt(data.encode()).decode()
