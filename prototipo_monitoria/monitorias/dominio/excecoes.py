"""Exceções do domínio. O menu captura só a base, ErroMonitorias, e mostra a mensagem."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .atendimento import Atendimento
    from .vinculo import Vinculo


class ErroMonitorias(Exception):
    """Base de todos os erros do sistema de monitorias"""

class DadosInvalidos(ErroMonitorias):
    """Formato ou valor inválido (dia, horário, código, email ...)"""

class DisciplinaForaDoEscopo(ErroMonitorias):
    """A disciplina informada está fora do escopo do sistema.

    Atributos:
        codigo: código bem formado, mas fora do catálogo 2026/2.
    """
    def __init__(self, codigo: str) -> None:
        """Guarda o código e monta a mensagem."""
        self.codigo = codigo
        super().__init__(f"A disciplina {codigo} está fora do escopo do sistema em 2026/2.")

class MatriculaNaoCadastrada(ErroMonitorias):
    """A matrícula informada não pertence a nenhum monitor cadastrado no sistema.

    Atributos:
        matricula: matrícula informada.
    """
    def __init__(self, matricula: str) -> None:
        """Guarda a matrícula e monta a mensagem."""
        self.matricula = matricula
        super().__init__(f"A matrícula {matricula} não pertence a nenhum monitor cadastrado no sistema.")

class VinculoInexistente(ErroMonitorias):
    """O monitor existe, mas não é vinculado à disciplina informada.

    Atributos:
        matricula: matrícula do monitor.
        codigo: código da disciplina.
    """
    def __init__(self, matricula: str, codigo: str) -> None:
        """Guarda matrícula e código e monta a mensagem."""
        self.matricula = matricula
        self.codigo = codigo
        super().__init__(f"O monitor de matrícula {matricula} não é monitor da disciplina {codigo}.")


class ConflitoDeHorario(ErroMonitorias):
    """O novo horário se sobrepõe a um horário que o monitor já atende.

    Atributos:
        vinculo: vínculo (monitor + disciplina) do horário já existente.
        atendimento: atendimento já existente que causou o conflito.
    """

    def __init__(self, vinculo: Vinculo, atendimento: Atendimento) -> None:
        """Guarda o vínculo e o atendimento existentes e monta a mensagem."""
        self.vinculo = vinculo
        self.atendimento = atendimento
        super().__init__(
            "Conflito de horário: o monitor já atende "
            f"{atendimento.dia} {atendimento.inicio}–{atendimento.fim} "
            f"em {vinculo.disciplina.codigo}."
        )

class RegistroDuplicado(ErroMonitorias):
    """Tentativa de gravar um registro cuja chave já existe na base.

    O domínio deve conferir antes de gravar; esta exceção é a rede de segurança
    lançada pelo repositório quando a base recusa a chave repetida (disciplina,
    matrícula ou vínculo).

    Atributos:
        tipo: o que se tentou gravar, ex.: "disciplina".
        chave: a chave repetida, ex.: "DCC203".
    """

    def __init__(self, tipo: str, chave: str) -> None:
        """Guarda o tipo e a chave e monta a mensagem."""
        self.tipo = tipo
        self.chave = chave
        super().__init__(f"Registro duplicado: já existe {tipo} {chave} no sistema.")

class CredenciaisInvalidas(ErroMonitorias):
    """Matrícula inexistente ou senha incorreta."""
