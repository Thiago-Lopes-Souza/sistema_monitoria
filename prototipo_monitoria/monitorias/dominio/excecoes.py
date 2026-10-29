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
    """A disciplina informada está fora do escopo do Sistema"""
    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__(f"A disciplina {codigo} está fora do escopo do Sistema em 2026/2 !")

class MatriculaNaoCadastrada(ErroMonitorias):
    """A matrícula informada não pertence a nenhum monitor cadastrado no Sistema"""
    def __init__(self, matricula: str) -> None:
        self.matricula = matricula
        super().__init__(f"A matricula {matricula} não pertence a nenhum monitor cadastrado no Sistema!")

class VinculoInexistente(ErroMonitorias):
    """Verifica se o monitor específico está cadastrado naquela matéria"""
    def __init__(self, matricula: str, codigo: str) ->None:
        self.matricula = matricula
        self.codigo = codigo
        super().__init__(f"O monitor de matricula {matricula} não é monitor da disciplina {codigo}.")


class ConflitoDeHorario(ErroMonitorias):
    """O novo horário se sobrepõe a um horário que o monitor já atende.

    Atributos:
        vinculo: vínculo (monitor + disciplina) do horário já existente.
        atendimento: atendimento já existente que causou o conflito.
    """

    def __init__(self, vinculo: Vinculo, atendimento: Atendimento) -> None:
        self.vinculo = vinculo
        self.atendimento = atendimento
        super().__init__(
            "Conflito de horário: o monitor já atende "
            f"{atendimento.dia} {atendimento.inicio}–{atendimento.fim} "
            f"em {vinculo.disciplina.codigo}."
        )