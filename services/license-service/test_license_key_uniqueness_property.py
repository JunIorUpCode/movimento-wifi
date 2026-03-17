# -*- coding: utf-8 -*-
"""
Testes de Propriedade para LicenseGenerator — Property 9: License Key Uniqueness

Valida que o gerador de chaves NUNCA produz a mesma chave duas vezes.

Cada chave usa 80 bits de entropia criptograficamente segura (secrets.token_bytes(10))
codificada em Base32 customizado — a probabilidade de colisão é aproximadamente
1/2^80 ≈ 8.27 × 10⁻²⁵, que para fins práticos é indistinguível de zero.

Implementa Tarefa 5.3 | Requisitos: 4.2
"""

import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
service_dir = os.path.abspath(os.path.dirname(__file__))
if service_dir not in sys.path:
    sys.path.insert(0, service_dir)

import hashlib
import pytest
from hypothesis import given, strategies as st
from hypothesis import settings as h_settings


# ─── fixtures ─────────────────────────────────────────────────────────────────

def _gen():
    """Retorna instância de LicenseGenerator (sem DB, puro Python)."""
    from services.license_generator import LicenseGenerator

    return LicenseGenerator()


# ─── Property 9: License Key Uniqueness ──────────────────────────────────────

class TestLicenseKeyUniquenessPropery:
    """
    Property 9: Unicidade de Chaves de Ativação — Requisito 4.2

    Para qualquer número N de chaves geradas, todas devem ser distintas.
    """

    @given(n=st.integers(min_value=2, max_value=200))
    @h_settings(max_examples=50)
    def test_property_n_keys_are_always_distinct(self, n: int):
        """
        Property 9a: N chaves geradas são sempre N chaves distintas.

        Probabilidade de colisão: 1/2^80 ≈ 8.3 × 10⁻²⁵ — negligível.
        """
        gen = _gen()
        keys = [gen.generate_activation_key()[0] for _ in range(n)]
        unique_keys = set(keys)
        assert len(unique_keys) == n, (
            f"Colisão detectada! {n} chaves geradas, mas apenas {len(unique_keys)} únicas."
        )

    @given(n=st.integers(min_value=2, max_value=200))
    @h_settings(max_examples=50)
    def test_property_n_hashes_are_always_distinct(self, n: int):
        """
        Property 9b: N hashes SHA256 gerados são sempre N hashes distintos.

        Se duas chaves fossem iguais, seus hashes também seriam iguais.
        Esta propriedade detecta colisões tanto nas chaves quanto nos hashes.
        """
        gen = _gen()
        hashes = [gen.generate_activation_key()[1] for _ in range(n)]
        unique_hashes = set(hashes)
        assert len(unique_hashes) == n, (
            f"Colisão de hash detectada em {n} gerações!"
        )

    @given(n=st.integers(min_value=1, max_value=100))
    @h_settings(max_examples=50)
    def test_property_every_key_has_valid_format(self, n: int):
        """
        Property 9c: Toda chave gerada tem formato XXXX-XXXX-XXXX-XXXX.

        - 19 caracteres totais (16 chars + 3 hífens)
        - 3 hífens nas posições 4, 9, 14
        - Somente caracteres do alfabeto Base32 customizado
        """
        gen = _gen()
        for _ in range(n):
            key, _ = gen.generate_activation_key()

            assert len(key) == 19, f"Comprimento inválido: {len(key)} (esperado 19)"
            assert key[4] == "-", f"Hífen ausente na posição 4: '{key}'"
            assert key[9] == "-", f"Hífen ausente na posição 9: '{key}'"
            assert key[14] == "-", f"Hífen ausente na posição 14: '{key}'"

            key_clean = key.replace("-", "")
            assert len(key_clean) == 16, (
                f"Parte limpa deve ter 16 chars, got {len(key_clean)}"
            )
            for char in key_clean:
                assert char in gen.BASE32_ALPHABET, (
                    f"Caractere inválido '{char}' na chave '{key}'. "
                    f"Alfabeto válido: {gen.BASE32_ALPHABET}"
                )

    @given(n=st.integers(min_value=1, max_value=100))
    @h_settings(max_examples=50)
    def test_property_every_key_passes_format_validation(self, n: int):
        """
        Property 9d: Toda chave gerada passa na validação de formato.

        validate_key_format(generated_key) deve sempre retornar True.
        """
        gen = _gen()
        for _ in range(n):
            key, _ = gen.generate_activation_key()
            assert gen.validate_key_format(key) is True, (
                f"Chave gerada não passou na validação de formato: '{key}'"
            )

    @given(n=st.integers(min_value=1, max_value=100))
    @h_settings(max_examples=50)
    def test_property_hash_is_sha256_of_key(self, n: int):
        """
        Property 9e: O hash retornado é sempre o SHA256 exato da chave.

        hash_returned == hashlib.sha256(key.encode()).hexdigest()
        """
        gen = _gen()
        for _ in range(n):
            key, key_hash = gen.generate_activation_key()

            expected_hash = hashlib.sha256(key.encode()).hexdigest()
            assert key_hash == expected_hash, (
                f"Hash incorreto para chave '{key}': "
                f"esperado {expected_hash}, got {key_hash}"
            )

    @given(n=st.integers(min_value=1, max_value=100))
    @h_settings(max_examples=50)
    def test_property_hash_is_64_hex_chars(self, n: int):
        """
        Property 9f: O hash tem sempre 64 caracteres hexadecimais (SHA256 = 256 bits = 64 hex).
        """
        gen = _gen()
        valid_hex = set("0123456789abcdef")
        for _ in range(n):
            _, key_hash = gen.generate_activation_key()
            assert len(key_hash) == 64, (
                f"Hash deve ter 64 chars, got {len(key_hash)}: '{key_hash}'"
            )
            for char in key_hash:
                assert char in valid_hex, (
                    f"Hash contém caractere não-hex '{char}'"
                )


# ─── testes unitários adicionais (sem Hypothesis) ────────────────────────────

class TestLicenseGeneratorUnit:
    """Testes unitários diretos para LicenseGenerator."""

    def test_generated_keys_are_strings(self):
        """Chave e hash são sempre strings."""
        gen = _gen()
        key, key_hash = gen.generate_activation_key()
        assert isinstance(key, str)
        assert isinstance(key_hash, str)

    def test_no_ambiguous_characters_in_key(self):
        """Chaves NÃO contêm O, I, L, 1 — caracteres visualmente ambíguos."""
        gen = _gen()
        ambiguous = set("OIL1")
        for _ in range(500):
            key, _ = gen.generate_activation_key()
            key_clean = key.replace("-", "")
            overlap = set(key_clean) & ambiguous
            assert not overlap, (
                f"Chave '{key}' contém caractere ambíguo: {overlap}"
            )

    def test_hash_key_is_deterministic(self):
        """hash_key() é determinístico: mesma entrada → mesmo hash."""
        gen = _gen()
        key = "ABCD-EFGH-JKMN-PQRS"
        assert gen.hash_key(key) == gen.hash_key(key)
        assert gen.hash_key(key) == hashlib.sha256(key.encode()).hexdigest()

    def test_validate_format_accepts_valid_key(self):
        """validate_key_format retorna True para chave gerada."""
        gen = _gen()
        key, _ = gen.generate_activation_key()
        assert gen.validate_key_format(key) is True

    def test_validate_format_rejects_wrong_length(self):
        """validate_key_format retorna False para chave curta/longa."""
        gen = _gen()
        assert gen.validate_key_format("ABCD-EFGH-JKMN") is False
        assert gen.validate_key_format("ABCD-EFGH-JKMN-PQRS-XXXX") is False

    def test_validate_format_rejects_ambiguous_chars(self):
        """validate_key_format retorna False para chave com caracteres proibidos."""
        gen = _gen()
        # 'O' e 'I' não estão no alfabeto
        assert gen.validate_key_format("OIIO-EFGH-JKMN-PQRS") is False

    def test_normalize_key_removes_spaces_and_hyphens(self):
        """normalize_key padroniza para o formato XXXX-XXXX-XXXX-XXXX."""
        gen = _gen()
        raw = "ABCDEFGHJKMNPQRS"
        normalized = gen.normalize_key(raw)
        assert normalized == "ABCD-EFGH-JKMN-PQRS"

    def test_normalize_key_uppercase(self):
        """normalize_key converte para maiúsculas."""
        gen = _gen()
        lower_key = "abcd-efgh-jkmn-pqrs"
        normalized = gen.normalize_key(lower_key)
        assert normalized == normalized.upper()

    def test_base32_alphabet_has_32_chars(self):
        """O alfabeto Base32 customizado tem exatamente 32 caracteres únicos."""
        gen = _gen()
        assert len(gen.BASE32_ALPHABET) == 32
        assert len(set(gen.BASE32_ALPHABET)) == 32

    def test_two_sequential_keys_are_different(self):
        """Duas chaves geradas em sequência são sempre diferentes."""
        gen = _gen()
        key1, hash1 = gen.generate_activation_key()
        key2, hash2 = gen.generate_activation_key()
        assert key1 != key2, "Duas chaves consecutivas não podem ser iguais!"
        assert hash1 != hash2, "Dois hashes consecutivos não podem ser iguais!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
