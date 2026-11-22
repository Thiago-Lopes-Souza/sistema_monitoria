"""Hash de senha com sal, só com a biblioteca padrão (decisão D2).

A senha nunca é guardada: guardamos o resultado do PBKDF2-HMAC-SHA256 e o sal
aleatório usado. Para conferir, recalculamos com a senha digitada e o mesmo sal
e comparamos os dois resultados em tempo constante.

Usado pela carga de demonstração (seed_demo), por cadastrar_monitor (frente C)
e por entrar (frente B).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from .excecoes import DadosInvalidos

#: Repetições do PBKDF2. Quanto maior, mais caro fica testar senhas em massa
#: caso a base vaze. 600 000 é o valor recomendado pela OWASP para SHA-256.
ITERACOES = 600_000

#: Tamanho do sal, em bytes (um sal diferente por usuário).
TAMANHO_SAL = 16


def _calcular(senha: str, sal: bytes) -> bytes:
    """Calcula o hash de uma senha com um sal."""
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal, ITERACOES)


def gerar_hash_senha(senha: str) -> tuple[bytes, bytes]:
    """Gera o hash de uma senha nova.

    Recebe:
        senha: a senha em texto; não pode ser vazia.
    Devolve:
        (senha_hash, senha_sal), os dois valores que vão para a tabela usuarios.
    Lança:
        DadosInvalidos se a senha for vazia ou só espaços.
    """
    if not isinstance(senha, str) or not senha.strip():
        raise DadosInvalidos("A senha não pode ser vazia.")
    sal = secrets.token_bytes(TAMANHO_SAL)
    return _calcular(senha, sal), sal


def conferir_senha(senha: str, senha_hash: bytes, senha_sal: bytes) -> bool:
    """Diz se a senha digitada corresponde ao hash guardado.

    A comparação usa hmac.compare_digest, que leva o mesmo tempo acerte ou
    erre, para não dar pistas a quem tenta adivinhar a senha.
    """
    if not isinstance(senha, str):
        return False
    return hmac.compare_digest(_calcular(senha, senha_sal), senha_hash)
