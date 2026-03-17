# -*- coding: utf-8 -*-
"""
Shared Encryption - Criptografia Fernet para dados sensíveis.

Fornece criptografia simétrica autenticada (AES-128-CBC + HMAC-SHA256)
via biblioteca cryptography (Fernet), com suporte a:
- Rotação de chaves (chaves múltiplas / MultiFernet)
- Derivação de chave a partir de senha (PBKDF2HMAC)
- Hash unidirecional para dados não-recuperáveis (SHA-256)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Optional

from cryptography.fernet import Fernet, MultiFernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """
    Serviço de criptografia usando Fernet (AES-128-CBC + HMAC-SHA256).

    Uso típico:
        svc = EncryptionService(key="minha-chave-base64")
        cifrado = svc.encrypt("dado sensível")
        original = svc.decrypt(cifrado)
    """

    def __init__(
        self,
        key: Optional[str] = None,
        additional_keys: Optional[list[str]] = None,
    ) -> None:
        """
        Inicializa o serviço de criptografia.

        Args:
            key: Chave Fernet em base64 (url-safe). Se None, gera uma nova.
            additional_keys: Chaves adicionais para rotação (MultiFernet).
                             A primeira chave é usada para criptografar;
                             todas são tentadas na descriptografia.
        """
        if key is None:
            key = Fernet.generate_key().decode()

        self._primary_key = self._ensure_valid_key(key)
        self._primary_fernet = Fernet(self._primary_key)

        if additional_keys:
            all_keys = [self._primary_fernet] + [
                Fernet(self._ensure_valid_key(k)) for k in additional_keys
            ]
            self._fernet = MultiFernet(all_keys)
        else:
            self._fernet = self._primary_fernet

    @staticmethod
    def generate_key() -> str:
        """Gera uma nova chave Fernet aleatória."""
        return Fernet.generate_key().decode()

    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        Deriva uma chave Fernet a partir de uma senha usando PBKDF2HMAC.

        Args:
            password: Senha em texto plano.
            salt: Salt de 16 bytes. Se None, gera aleatoriamente.

        Returns:
            Tupla (key_b64, salt_hex) — a chave em base64 e o salt em hex.
        """
        if salt is None:
            salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
        )
        key_bytes = kdf.derive(password.encode("utf-8"))
        key_b64 = base64.urlsafe_b64encode(key_bytes).decode()
        return key_b64, salt.hex()

    # ── Criptografia / Descriptografia ─────────────────────────────────────

    def encrypt(self, plaintext: str) -> str:
        """
        Criptografa uma string usando Fernet.

        Args:
            plaintext: Dado em texto plano.

        Returns:
            Token Fernet em base64 (url-safe).
        """
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        """
        Descriptografa um token Fernet.

        Args:
            token: Token Fernet em base64.

        Returns:
            Dado descriptografado em texto plano.

        Raises:
            ValueError: Se o token for inválido ou tiver sido adulterado.
        """
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Token de criptografia inválido ou adulterado.") from exc

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Criptografa bytes diretamente."""
        return self._fernet.encrypt(data)

    def decrypt_bytes(self, token: bytes) -> bytes:
        """Descriptografa bytes diretamente."""
        try:
            return self._fernet.decrypt(token)
        except InvalidToken as exc:
            raise ValueError("Token de criptografia inválido ou adulterado.") from exc

    # ── Hash unidirecional ──────────────────────────────────────────────────

    @staticmethod
    def hash_sha256(data: str) -> str:
        """
        Hash SHA-256 determinístico (não reversível).
        Útil para armazenar valores sensíveis para comparação (ex: e-mails para busca).

        Args:
            data: Dado em texto plano.

        Returns:
            Hash hex de 64 caracteres.
        """
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def hmac_sha256(data: str, secret: str) -> str:
        """
        HMAC-SHA256 para verificação de integridade de mensagens.

        Args:
            data: Dado a ser autenticado.
            secret: Chave secreta compartilhada.

        Returns:
            HMAC hex de 64 caracteres.
        """
        return hmac.new(
            secret.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def verify_hmac(data: str, secret: str, expected_hmac: str) -> bool:
        """
        Verifica HMAC usando comparação segura (constant-time).

        Returns:
            True se o HMAC for válido.
        """
        computed = EncryptionService.hmac_sha256(data, secret)
        return hmac.compare_digest(computed, expected_hmac)

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _ensure_valid_key(key: str) -> bytes:
        """
        Garante que a chave tem 32 bytes codificados em base64.
        Se a chave não for um Fernet key válido, deriva via SHA-256.
        """
        key_bytes = key.encode("utf-8") if isinstance(key, str) else key
        try:
            # Testa se é um Fernet key válido (32 bytes base64url)
            decoded = base64.urlsafe_b64decode(key_bytes + b"==")
            if len(decoded) == 32:
                return key_bytes
        except Exception:
            pass
        # Deriva 32 bytes via SHA-256 e re-codifica
        derived = hashlib.sha256(key_bytes).digest()
        return base64.urlsafe_b64encode(derived)


def create_encryption_service(key: Optional[str] = None) -> EncryptionService:
    """
    Cria um EncryptionService a partir de variável de ambiente ou chave fornecida.

    Se key for None, lê de ENCRYPTION_KEY no ambiente.
    Se a variável também não existir, gera uma nova chave (apenas para dev).
    """
    if key is None:
        key = os.environ.get("ENCRYPTION_KEY")
    return EncryptionService(key=key)


# Instância global (lazy) — inicializada na primeira importação
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Retorna instância global do serviço de criptografia."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = create_encryption_service()
    return _encryption_service
