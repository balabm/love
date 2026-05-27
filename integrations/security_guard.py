"""
Vault Encryption System for Plaintext Credentials

Provides secure encryption/decryption for API tokens and OAuth secrets.
Uses cryptography.fernet when available, with XOR fallback.
"""

import os
import base64
import hashlib
import json
from typing import Dict


class SecretVault:
    """Secure vault for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        self.master_key = os.environ.get('LOVE_MASTER_KEY', '')
        if not self.master_key:
            raise ValueError("LOVE_MASTER_KEY environment variable must be set")
        
        self._fernet = None
        self._use_fernet = self._init_fernet()
    
    def _init_fernet(self) -> bool:
        """Initialize Fernet encryption if cryptography library is available."""
        try:
            from cryptography.fernet import Fernet
            
            # Derive a 32-byte key from the master key
            key_bytes = self.master_key.encode('utf-8')
            derived_key = hashlib.sha256(key_bytes).digest()
            self._fernet = Fernet(base64.urlsafe_b64encode(derived_key))
            return True
        except ImportError:
            # Fallback to XOR obfuscation
            return False
    
    def _xor_obfuscate(self, data: str, key: str) -> str:
        """XOR obfuscation as fallback encryption method."""
        key_bytes = key.encode('utf-8')
        data_bytes = data.encode('utf-8')
        
        obfuscated = bytearray()
        for i, byte in enumerate(data_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            obfuscated.append(byte ^ key_byte)
        
        return base64.urlsafe_b64encode(obfuscated).decode('utf-8')
    
    def _xor_deobfuscate(self, obfuscated: str, key: str) -> str:
        """Reverse XOR obfuscation."""
        key_bytes = key.encode('utf-8')
        obfuscated_bytes = base64.urlsafe_b64decode(obfuscated.encode('utf-8'))
        
        data = bytearray()
        for i, byte in enumerate(obfuscated_bytes):
            key_byte = key_bytes[i % len(key_bytes)]
            data.append(byte ^ key_byte)
        
        return data.decode('utf-8')
    
    def encrypt_data(self, plain_text: str) -> str:
        """
        Encrypt plaintext data.
        
        Args:
            plain_text: The plaintext string to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plain_text:
            raise ValueError("Cannot encrypt empty string")
        
        if self._use_fernet and self._fernet:
            encrypted = self._fernet.encrypt(plain_text.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        else:
            return self._xor_obfuscate(plain_text, self.master_key)
    
    def decrypt_data(self, cipher_text: str) -> str:
        """
        Decrypt encrypted data.
        
        Args:
            cipher_text: The encrypted string to decrypt
            
        Returns:
            Decrypted plaintext string
        """
        if not cipher_text:
            raise ValueError("Cannot decrypt empty string")
        
        try:
            if self._use_fernet and self._fernet:
                encrypted_bytes = base64.urlsafe_b64decode(cipher_text.encode('utf-8'))
                decrypted = self._fernet.decrypt(encrypted_bytes)
                return decrypted.decode('utf-8')
            else:
                return self._xor_deobfuscate(cipher_text, self.master_key)
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")


def secure_save_token(service_name: str, token_data: Dict) -> str:
    """
    Serialize, encrypt, and save token data as a .vault file.
    
    Args:
        service_name: Name of the service (e.g., 'google', 'github')
        token_data: Dictionary containing token/secret information
        
    Returns:
        Path to the saved .vault file
    """
    if not service_name:
        raise ValueError("service_name cannot be empty")
    
    if not token_data:
        raise ValueError("token_data cannot be empty")
    
    # Initialize vault
    vault = SecretVault()
    
    # Serialize to JSON
    json_str = json.dumps(token_data, separators=(',', ':'))
    
    # Encrypt the JSON string
    encrypted_data = vault.encrypt_data(json_str)
    
    # Ensure secure directory exists
    secure_dir = os.path.join('data', 'secure')
    os.makedirs(secure_dir, exist_ok=True)
    
    # Save to .vault file
    vault_path = os.path.join(secure_dir, f"{service_name}.vault")
    with open(vault_path, 'w', encoding='utf-8') as f:
        f.write(encrypted_data)
    
    return vault_path


def secure_load_token(service_name: str) -> Dict:
    """
    Load and decrypt token data from a .vault file.
    
    Args:
        service_name: Name of the service to load
        
    Returns:
        Dictionary containing the decrypted token data
    """
    if not service_name:
        raise ValueError("service_name cannot be empty")
    
    vault_path = os.path.join('data', 'secure', f"{service_name}.vault")
    
    if not os.path.exists(vault_path):
        raise FileNotFoundError(f"Vault file not found: {vault_path}")
    
    # Read encrypted data
    with open(vault_path, 'r', encoding='utf-8') as f:
        encrypted_data = f.read()
    
    # Decrypt
    vault = SecretVault()
    json_str = vault.decrypt_data(encrypted_data)
    
    # Deserialize
    return json.loads(json_str)
