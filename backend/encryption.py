import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

def get_master_key() -> bytes:
    key_hex = os.environ.get("HEALTHCARE_ENCRYPTION_KEY")
    if not key_hex:
        raise ValueError("HEALTHCARE_ENCRYPTION_KEY environment variable is not set!")
    return bytes.fromhex(key_hex)

def generate_encryption_key() -> str:
    """Utility to generate a new master key for the .env file."""
    return AESGCM.generate_key(bit_length=256).hex()

def encrypt_record_data(plaintext_dict: dict) -> dict:
    """
    Encrypts the record data using Envelope Encryption (AES-GCM).
    Returns a dict with hex strings: encrypted_data, data_nonce, data_tag, encrypted_dek, dek_nonce, dek_tag.
    """
    master_key = get_master_key()
    kek_gcm = AESGCM(master_key)
    
    # 1. Generate DEK
    dek = AESGCM.generate_key(bit_length=256)
    
    # 2. Encrypt DEK
    dek_nonce = os.urandom(12)
    encrypted_dek_with_tag = kek_gcm.encrypt(dek_nonce, dek, None)
    # AESGCM in cryptography appends the 16-byte tag to the ciphertext
    encrypted_dek = encrypted_dek_with_tag[:-16]
    dek_tag = encrypted_dek_with_tag[-16:]
    
    # 3. Encrypt Data
    data_gcm = AESGCM(dek)
    data_nonce = os.urandom(12)
    plaintext_bytes = json.dumps(plaintext_dict).encode('utf-8')
    encrypted_data_with_tag = data_gcm.encrypt(data_nonce, plaintext_bytes, None)
    encrypted_data = encrypted_data_with_tag[:-16]
    data_tag = encrypted_data_with_tag[-16:]
    
    return {
        "encrypted_data": encrypted_data.hex(),
        "data_nonce": data_nonce.hex(),
        "data_tag": data_tag.hex(),
        "encrypted_dek": encrypted_dek.hex(),
        "dek_nonce": dek_nonce.hex(),
        "dek_tag": dek_tag.hex()
    }

def decrypt_record_data(enc_metadata: dict) -> dict:
    """
    Decrypts the record data using Envelope Encryption.
    Raises InvalidTag if tampering occurred.
    """
    master_key = get_master_key()
    kek_gcm = AESGCM(master_key)
    
    encrypted_dek = bytes.fromhex(enc_metadata["encrypted_dek"])
    dek_nonce = bytes.fromhex(enc_metadata["dek_nonce"])
    dek_tag = bytes.fromhex(enc_metadata["dek_tag"])
    
    # Reconstruct the combined ciphertext+tag for cryptography library
    dek = kek_gcm.decrypt(dek_nonce, encrypted_dek + dek_tag, None)
    
    data_gcm = AESGCM(dek)
    encrypted_data = bytes.fromhex(enc_metadata["encrypted_data"])
    data_nonce = bytes.fromhex(enc_metadata["data_nonce"])
    data_tag = bytes.fromhex(enc_metadata["data_tag"])
    
    plaintext_bytes = data_gcm.decrypt(data_nonce, encrypted_data + data_tag, None)
    return json.loads(plaintext_bytes.decode('utf-8'))
