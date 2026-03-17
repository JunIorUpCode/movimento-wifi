# -*- coding: utf-8 -*-
"""
Encryption Utils - Utilitários de Criptografia
Fornece funções para criptografar e descriptografar tokens sensíveis
"""

from cryptography.fernet import Fernet
from shared.config import settings
from shared.logging import get_logger
import base64
import hashlib

logger = get_logger(__name__)


def _get_fernet_key() -> bytes:
    """
    Gera chave Fernet a partir da ENCRYPTION_KEY das configurações.
    
    A chave deve ter 32 bytes. Se a chave configurada não tiver 32 bytes,
    usa SHA256 para derivar uma chave de 32 bytes.
    
    Returns:
        bytes: Chave Fernet válida (32 bytes, base64-encoded)
    """
    encryption_key = settings.ENCRYPTION_KEY.encode()
    
    # Deriva chave de 32 bytes usando SHA256
    key_bytes = hashlib.sha256(encryption_key).digest()
    
    # Codifica em base64 para formato Fernet
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_token(token: str) -> str:
    """
    Criptografa um token sensível usando Fernet (AES-128).
    
    **Segurança**: Usa criptografia simétrica com chave derivada de ENCRYPTION_KEY
    
    **Uso**: Criptografar bot_token, webhook_secret, API keys antes de salvar no banco
    
    Args:
        token: Token em texto plano
    
    Returns:
        str: Token criptografado (base64)
    
    Example:
        >>> encrypted = encrypt_token("123456:ABC-DEF")
        >>> print(encrypted)
        'gAAAAABf...'
    """
    try:
        fernet = Fernet(_get_fernet_key())
        encrypted_bytes = fernet.encrypt(token.encode())
        encrypted_str = encrypted_bytes.decode()
        
        logger.debug("Token criptografado com sucesso")
        
        return encrypted_str
    
    except Exception as e:
        logger.error(f"Erro ao criptografar token: {str(e)}", exc_info=True)
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Descriptografa um token criptografado.
    
    **Segurança**: Usa mesma chave derivada de ENCRYPTION_KEY
    
    **Uso**: Descriptografar bot_token, webhook_secret, API keys ao usar
    
    Args:
        encrypted_token: Token criptografado (base64)
    
    Returns:
        str: Token em texto plano
    
    Raises:
        Exception: Se token for inválido ou chave estiver incorreta
    
    Example:
        >>> decrypted = decrypt_token("gAAAAABf...")
        >>> print(decrypted)
        '123456:ABC-DEF'
    """
    try:
        fernet = Fernet(_get_fernet_key())
        decrypted_bytes = fernet.decrypt(encrypted_token.encode())
        decrypted_str = decrypted_bytes.decode()
        
        logger.debug("Token descriptografado com sucesso")
        
        return decrypted_str
    
    except Exception as e:
        logger.error(f"Erro ao descriptografar token: {str(e)}", exc_info=True)
        raise
