# -*- coding: utf-8 -*-
"""
Teste de Propriedade: Password Bcrypt Hashing
Property 28: Valida Requisito 19.3

Verifica que senhas armazenadas começam com "$2b$" ou "$2a$" (formato bcrypt)
"""

import pytest
from hypothesis import given, strategies as st, settings, Phase
from services.auth_service import AuthService


class TestPasswordHashingProperty:
    """
    Testes de propriedade para validação de hash de senha bcrypt
    """
    
    @given(
        password=st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(
                blacklist_categories=('Cs', 'Cc'),  # Remove caracteres de controle
                blacklist_characters='\x00'  # Remove null bytes
            )
        )
    )
    @settings(
        max_examples=100,
        phases=[Phase.generate, Phase.target],
        deadline=None  # Bcrypt é lento por design (segurança)
    )
    def test_property_28_password_bcrypt_hashing(self, password):
        """
        Property 28: Password Bcrypt Hashing
        
        Valida: Requisito 19.3
        
        Propriedade: Para qualquer senha válida, o hash gerado DEVE começar
        com "$2b$" ou "$2a$" (formato bcrypt padrão)
        
        Args:
            password: Senha gerada aleatoriamente pelo Hypothesis
        """
        # Arrange: Cria instância do serviço
        auth_service = AuthService()
        
        # Act: Gera hash da senha
        password_hash = auth_service.hash_password(password)
        
        # Assert: Verifica que hash começa com prefixo bcrypt válido
        assert password_hash.startswith("$2b$") or password_hash.startswith("$2a$"), \
            f"Hash de senha deve começar com '$2b$' ou '$2a$', mas começou com: {password_hash[:4]}"
        
        # Assert adicional: Verifica que hash tem formato completo bcrypt
        # Formato: $2b$rounds$salt(22 chars)hash(31 chars) = 60 chars total
        assert len(password_hash) == 60, \
            f"Hash bcrypt deve ter 60 caracteres, mas tem {len(password_hash)}"
        
        # Assert adicional: Verifica que hash contém 12 rounds (requisito 19.3)
        assert password_hash.startswith("$2b$12$") or password_hash.startswith("$2a$12$"), \
            f"Hash deve usar 12 rounds de bcrypt, mas hash é: {password_hash[:7]}"
    
    @given(
        password=st.text(min_size=8, max_size=50)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_28_hash_uniqueness(self, password):
        """
        Propriedade adicional: Cada hash gerado deve ser único (devido ao salt aleatório)
        
        Args:
            password: Senha gerada aleatoriamente
        """
        # Arrange: Cria instância do serviço
        auth_service = AuthService()
        
        # Act: Gera dois hashes da mesma senha
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Assert: Hashes devem ser diferentes (salt aleatório)
        assert hash1 != hash2, \
            "Dois hashes da mesma senha devem ser diferentes devido ao salt aleatório"
        
        # Assert: Ambos devem ser válidos bcrypt
        assert hash1.startswith("$2b$") or hash1.startswith("$2a$")
        assert hash2.startswith("$2b$") or hash2.startswith("$2a$")
    
    @given(
        password=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_28_hash_verification(self, password):
        """
        Propriedade adicional: Hash gerado deve ser verificável com a senha original
        
        Args:
            password: Senha gerada aleatoriamente
        """
        # Arrange: Cria instância do serviço
        auth_service = AuthService()
        
        # Act: Gera hash e verifica
        password_hash = auth_service.hash_password(password)
        is_valid = auth_service.verify_password(password, password_hash)
        
        # Assert: Verificação deve retornar True
        assert is_valid, \
            "Hash gerado deve ser verificável com a senha original"
        
        # Assert: Hash deve ter formato bcrypt
        assert password_hash.startswith("$2b$") or password_hash.startswith("$2a$")
    
    @given(
        password=st.text(min_size=1, max_size=100),
        wrong_password=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, deadline=None)
    def test_property_28_wrong_password_rejection(self, password, wrong_password):
        """
        Propriedade adicional: Hash não deve verificar com senha incorreta
        
        Args:
            password: Senha original
            wrong_password: Senha incorreta
        """
        # Pula teste se senhas forem iguais
        if password == wrong_password:
            return
        
        # Arrange: Cria instância do serviço
        auth_service = AuthService()
        
        # Act: Gera hash da senha original e tenta verificar com senha errada
        password_hash = auth_service.hash_password(password)
        is_valid = auth_service.verify_password(wrong_password, password_hash)
        
        # Assert: Verificação deve retornar False
        assert not is_valid, \
            "Hash não deve verificar com senha incorreta"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
