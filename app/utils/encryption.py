import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.config.settings import settings

def get_encryption_key():
    """
    Derive a Fernet encryption key from the settings.ENCRYPTION_KEY
    
    Returns:
        Fernet: Fernet encryption instance
    """
    # Derive a key from the master key
    salt = b'analisaai-socialmedia-salt'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    # Get the key material from settings
    key_material = settings.ENCRYPTION_KEY.encode('utf-8')
    
    # Derive the key
    key = base64.urlsafe_b64encode(kdf.derive(key_material))
    
    # Create Fernet instance
    return Fernet(key)

def encrypt_value(value: str) -> str:
    """
    Encrypt a string value
    
    Args:
        value (str): Value to encrypt
    
    Returns:
        str: Encrypted value as base64 string
    """
    if not value:
        return None
        
    fernet = get_encryption_key()
    encrypted = fernet.encrypt(value.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_value(encrypted_value: str) -> str:
    """
    Decrypt a string value
    
    Args:
        encrypted_value (str): Base64 encoded encrypted value
        
    Returns:
        str: Decrypted string value
    """
    if not encrypted_value:
        return None
        
    fernet = get_encryption_key()
    decrypted = fernet.decrypt(base64.b64decode(encrypted_value))
    return decrypted.decode('utf-8')