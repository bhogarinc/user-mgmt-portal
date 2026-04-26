"""
Security utilities for User Management Portal.

This module provides authentication, authorization, encryption,
and other security-related functionality.

GitHub Issue: HLD-004
"""

import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import jwt
from argon2 import PasswordHasher
from argon2.low_level import Type
from cryptography.fernet import Fernet
from azure.identity import DefaultAzureCredential
from azure.keyvault.keys import KeyClient
from azure.keyvault.keys.crypto import CryptographyClient, EncryptionAlgorithm

from app.core.config import settings
from app.core.errors import ErrorCode, UMPException


# Argon2id configuration (OWASP recommended)
password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=Type.ID
)


class PasswordManager:
    """Password hashing and verification using Argon2id."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using Argon2id.
        
        Args:
            password: Plain text password
            
        Returns:
            Argon2id hash string
        """
        return password_hasher.hash(password)
    
    @staticmethod
    def verify_password(password: str, hash_string: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hash_string: Stored hash
            
        Returns:
            True if password matches
        """
        try:
            password_hasher.verify(hash_string, password)
            return True
        except Exception:
            return False
    
    @staticmethod
    def needs_rehash(hash_string: str) -> bool:
        """Check if password needs rehashing (parameters changed)."""
        return password_hasher.check_needs_rehash(hash_string)


class JWTManager:
    """JWT token creation and verification."""
    
    @staticmethod
    def create_access_token(
        user_id: str,
        role: str,
        permissions: List[str],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User UUID
            role: User role
            permissions: List of permission strings
            expires_delta: Token expiry duration
            
        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)
        
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iss": "ump-auth-service",
            "aud": "ump-api",
            "iat": now,
            "exp": now + expires_delta,
            "jti": secrets.token_urlsafe(32),
            "role": role,
            "permissions": permissions,
            "scope": " ".join(permissions)
        }
        
        return jwt.encode(
            payload,
            settings.JWT_PRIVATE_KEY,
            algorithm="RS256",
            headers={"kid": settings.JWT_KEY_ID}
        )
    
    @staticmethod
    def create_refresh_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT refresh token.
        
        Args:
            user_id: User UUID
            expires_delta: Token expiry duration
            
        Returns:
            JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(days=7)
        
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iss": "ump-auth-service",
            "aud": "ump-api",
            "iat": now,
            "exp": now + expires_delta,
            "jti": secrets.token_urlsafe(32),
            "type": "refresh"
        }
        
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm="HS256"
        )
    
    @staticmethod
    def decode_token(token: str, verify_exp: bool = True) -> Dict[str, Any]:
        """
        Decode and verify JWT token.
        
        Args:
            token: JWT token string
            verify_exp: Whether to verify expiration
            
        Returns:
            Decoded token payload
            
        Raises:
            UMPException: If token is invalid or expired
        """
        try:
            # Try RS256 first (access token)
            return jwt.decode(
                token,
                settings.JWT_PUBLIC_KEY,
                algorithms=["RS256"],
                audience="ump-api",
                options={"verify_exp": verify_exp}
            )
        except jwt.InvalidTokenError:
            try:
                # Try HS256 (refresh token)
                return jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=["HS256"],
                    audience="ump-api",
                    options={"verify_exp": verify_exp}
                )
            except jwt.ExpiredSignatureError:
                raise UMPException(ErrorCode.AUTH_TOKEN_EXPIRED)
            except jwt.InvalidTokenError:
                raise UMPException(ErrorCode.AUTH_TOKEN_INVALID)


class FieldEncryption:
    """Field-level encryption for sensitive data."""
    
    def __init__(self):
        self.credential = DefaultAzureCredential()
        self.key_client = KeyClient(
            vault_url=settings.AZURE_KEY_VAULT_URL,
            credential=self.credential
        )
        self.key = self.key_client.get_key("field-encryption-key")
        self.crypto_client = CryptographyClient(self.key, self.credential)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt sensitive field data.
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            Base64 encoded ciphertext
        """
        result = self.crypto_client.encrypt(
            EncryptionAlgorithm.a256_gcm,
            plaintext.encode()
        )
        return base64.b64encode(result.ciphertext).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt sensitive field data.
        
        Args:
            ciphertext: Base64 encoded ciphertext
            
        Returns:
            Decrypted plaintext
        """
        result = self.crypto_client.decrypt(
            EncryptionAlgorithm.a256_gcm,
            base64.b64decode(ciphertext)
        )
        return result.plaintext.decode()


class PermissionChecker:
    """RBAC permission checking utilities."""
    
    @staticmethod
    def has_permission(user_permissions: List[str], required: str) -> bool:
        """
        Check if user has required permission.
        
        Supports wildcards and scoped permissions:
        - "*" matches all
        - "user:read" matches "user:read" and "user:read:own"
        - "user:write:own" matches only exact scope
        
        Args:
            user_permissions: List of user's permissions
            required: Required permission string
            
        Returns:
            True if user has permission
        """
        if "*" in user_permissions:
            return True
        
        for perm in user_permissions:
            if perm == required:
                return True
            # Check wildcard resource
            if perm.endswith(":*") and required.startswith(perm[:-1]):
                return True
            # Check parent permission
            if required.startswith(perm + ":"):
                return True
        
        return False
    
    @staticmethod
    def require_permissions(user_permissions: List[str], required: List[str]) -> bool:
        """
        Check if user has all required permissions.
        
        Args:
            user_permissions: List of user's permissions
            required: List of required permissions
            
        Returns:
            True if user has all permissions
        """
        return all(
            PermissionChecker.has_permission(user_permissions, req)
            for req in required
        )


def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash token for storage (e.g., refresh tokens in database)."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, hash_string: str) -> bool:
    """Verify token against stored hash."""
    return hash_token(token) == hash_string
