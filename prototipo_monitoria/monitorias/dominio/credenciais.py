"""Funções auxiliares para gerar e verificar hashes de senhas para autenticação no sistema."""

import hashlib
import hmac
import secrets

# Constantes
ALGORITMO = "sha256"
ITERACOES = 600_000
TAMANHO_SAL = 16

def gerar_hash_senha(senha: str) -> tuple[bytes, bytes]:
    """Gera um hash PBKDF2 e um sal aleatório para armazenar no banco.
    Recebe: senha em texto
    Devolve: (hash, sal), em bytes.
    Lança ValueError se a senha for vazia ou não for str."""

    if not isinstance(senha, str) or not senha:
        raise ValueError("A senha deve ser um texto não vazio.")

    sal = secrets.token_bytes(TAMANHO_SAL)
    senha_hash = hashlib.pbkdf2_hmac(ALGORITMO, senha.encode("utf-8"), sal, ITERACOES)

    return senha_hash, sal


def verificar_senha(senha: str, senha_hash: bytes, sal: bytes) -> bool:
    """Devolve True se a senha corresponde ao hash e ao sal armazenados.
    Não consulta o banco nem altera os dados."""
    
    if not isinstance(senha, str):
        return False

    hash_calculado = hashlib.pbkdf2_hmac(ALGORITMO, senha.encode("utf-8"), sal, ITERACOES)
    
    return hmac.compare_digest(hash_calculado, senha_hash)
