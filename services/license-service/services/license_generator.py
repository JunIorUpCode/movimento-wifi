# -*- coding: utf-8 -*-
"""
License Generator - Gerador de chaves de ativação
Implementa geração criptograficamente segura de chaves de ativação
"""

import secrets
import hashlib
import base64
from typing import Tuple

from shared.logging import get_logger

logger = get_logger(__name__)


class LicenseGenerator:
    """
    Gerador de chaves de ativação seguras
    Usa 80 bits de entropia e formato base32 sem caracteres ambíguos
    
    Requisitos: 4.2
    """
    
    # Alfabeto base32 sem caracteres ambíguos
    # Remove: O (letra O), I (letra i), 1 (um), L (letra L)
    # Mantém: 0 (zero) pois é distinguível de O em fontes modernas
    # Total: 32 caracteres para base32
    BASE32_ALPHABET = "023456789ABCDEFGHJKMNPQRSTUVWXYZ"
    
    def __init__(self):
        """Inicializa o gerador de licenças"""
        logger.info("LicenseGenerator inicializado")
    
    def generate_activation_key(self) -> Tuple[str, str]:
        """
        Gera uma chave de ativação criptograficamente segura
        
        Formato: XXXX-XXXX-XXXX-XXXX (16 caracteres + 3 hífens = 19 chars total)
        Entropia: 80 bits (10 bytes)
        Codificação: Base32 customizado sem caracteres ambíguos
        
        Returns:
            Tuple[str, str]: (activation_key, activation_key_hash)
                - activation_key: Chave em formato XXXX-XXXX-XXXX-XXXX
                - activation_key_hash: Hash SHA256 da chave (hex)
        
        Requisitos: 4.2
        """
        # Gera 10 bytes aleatórios (80 bits de entropia)
        random_bytes = secrets.token_bytes(10)
        
        # Converte para base32 customizado
        key = self._encode_base32(random_bytes)
        
        # Formata como XXXX-XXXX-XXXX-XXXX
        formatted_key = f"{key[0:4]}-{key[4:8]}-{key[8:12]}-{key[12:16]}"
        
        # Gera hash SHA256 da chave
        key_hash = hashlib.sha256(formatted_key.encode()).hexdigest()
        
        logger.info(
            "Chave de ativação gerada com sucesso",
            key_length=len(formatted_key),
            entropy_bits=80
        )
        
        return formatted_key, key_hash
    
    def _encode_base32(self, data: bytes) -> str:
        """
        Codifica bytes em base32 customizado sem caracteres ambíguos
        
        Args:
            data: Bytes a serem codificados
        
        Returns:
            String codificada em base32 (16 caracteres)
        """
        # Converte bytes para inteiro
        num = int.from_bytes(data, byteorder='big')
        
        # Codifica em base32 customizado
        result = []
        for _ in range(16):  # 16 caracteres para 80 bits
            result.append(self.BASE32_ALPHABET[num % 32])
            num //= 32
        
        # Inverte para ordem correta
        return ''.join(reversed(result))
    
    def validate_key_format(self, key: str) -> bool:
        """
        Valida o formato de uma chave de ativação
        
        Args:
            key: Chave a ser validada
        
        Returns:
            True se formato válido, False caso contrário
        """
        # Remove hífens
        key_clean = key.replace("-", "")
        
        # Verifica comprimento (16 caracteres)
        if len(key_clean) != 16:
            return False
        
        # Verifica se todos os caracteres são válidos
        for char in key_clean.upper():
            if char not in self.BASE32_ALPHABET:
                return False
        
        return True
    
    def normalize_key(self, key: str) -> str:
        """
        Normaliza uma chave de ativação
        Remove espaços, converte para maiúsculas e adiciona hífens
        
        Args:
            key: Chave a ser normalizada
        
        Returns:
            Chave normalizada no formato XXXX-XXXX-XXXX-XXXX
        """
        # Remove espaços e hífens
        key_clean = key.replace(" ", "").replace("-", "").upper()
        
        # Adiciona hífens
        if len(key_clean) == 16:
            return f"{key_clean[0:4]}-{key_clean[4:8]}-{key_clean[8:12]}-{key_clean[12:16]}"
        
        return key_clean
    
    def hash_key(self, key: str) -> str:
        """
        Gera hash SHA256 de uma chave de ativação
        
        Args:
            key: Chave a ser hasheada
        
        Returns:
            Hash SHA256 em hexadecimal
        """
        return hashlib.sha256(key.encode()).hexdigest()


# Instância global do gerador de licenças
license_generator = LicenseGenerator()
