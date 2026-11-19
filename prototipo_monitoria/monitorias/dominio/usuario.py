"""Perfis de usuário e permissões."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from monitorias.dominio.excecoes import DadosInvalidos


class Operacao(Enum):
    """Operações do sistema que dependem de permissão."""

    CONSULTAR_MONITORIAS = "consultar_monitorias"
    CADASTRAR_HORARIO = "cadastrar_horario"
    VISUALIZAR_HORARIOS = "visualizar_horarios"
    ALTERAR_HORARIO = "alterar_horario"
    REMOVER_ATENDIMENTO = "remover_atendimento"
    CADASTRAR_DISCIPLINA = "cadastrar_disciplina"
    CADASTRAR_MONITOR = "cadastrar_monitor"
    VINCULAR = "vincular"
    DESVINCULAR = "desvincular"


OPERACOES_ALUNO = (
    Operacao.CONSULTAR_MONITORIAS,
)

OPERACOES_MONITOR = (
    Operacao.CONSULTAR_MONITORIAS,
    Operacao.CADASTRAR_HORARIO,
    Operacao.VISUALIZAR_HORARIOS,
    Operacao.ALTERAR_HORARIO,
    Operacao.REMOVER_ATENDIMENTO,
)

OPERACOES_ADMINISTRADOR = (
    Operacao.CONSULTAR_MONITORIAS,
    Operacao.CADASTRAR_DISCIPLINA,
    Operacao.CADASTRAR_MONITOR,
    Operacao.VINCULAR,
    Operacao.DESVINCULAR,
)


class Usuario(ABC):
    """Quem usa o sistema. Cada perfil define o que pode fazer."""

    @abstractmethod
    def pode(self, operacao: Operacao) -> bool:
        """Devolve True se o perfil permite a operação; False caso contrário.

        Qualquer valor que não seja uma Operacao também devolve False.
        """

    @abstractmethod
    def opcoes_menu(self) -> tuple[Operacao, ...]:
        """Devolve as operações que o menu oferece ao perfil, na ordem do menu."""


class Aluno(Usuario):
    """Quem consulta sem login. Só pode consultar monitorias."""

    def pode(self, operacao: Operacao) -> bool:
        """Devolve True apenas para consultar monitorias."""
        return operacao in OPERACOES_ALUNO

    def opcoes_menu(self) -> tuple[Operacao, ...]:
        """Devolve só a consulta."""
        return OPERACOES_ALUNO


class UsuarioCadastrado(Usuario, ABC):
    """Usuário identificado por matrícula, com nome e e-mail institucional.

    Matrícula e nome são somente leitura. O e-mail tem setter que valida.
    """

    def __init__(self, matricula: str, nome: str, email: str) -> None:
        """Cria o usuário.

        Lança DadosInvalidos se matrícula ou nome forem vazios ou se o e-mail
        não for institucional.
        """
        matricula = matricula.strip()
        if not matricula:
            raise DadosInvalidos("A matrícula do usuário é obrigatória!")
        self._matricula = matricula

        nome = nome.strip()
        if not nome:
            raise DadosInvalidos("O nome do usuário é obrigatório!")
        self._nome = nome

        self.email = email

    @property
    def matricula(self) -> str:
        """Matrícula, sem espaços nas pontas. Só leitura."""
        return self._matricula

    @property
    def nome(self) -> str:
        """Nome do usuário. Só leitura."""
        return self._nome

    @property
    def email(self) -> str:
        """E-mail institucional, em minúsculas."""
        return self._email

    @email.setter
    def email(self, novo_email: str) -> None:
        """Troca o e-mail, validando antes de alterar.

        Lança DadosInvalidos se for vazio ou não terminar em "@ufmg.br"; nesse
        caso o e-mail anterior continua valendo.
        """
        novo_email = novo_email.strip().lower()
        if not novo_email or not novo_email.endswith("@ufmg.br"):
            raise DadosInvalidos("O e-mail deve ser institucional e terminar em '@ufmg.br'.")
        self._email = novo_email


class Administrador(UsuarioCadastrado):
    """Mantém disciplinas, monitores e vínculos. Não gerencia horários de terceiros."""

    def pode(self, operacao: Operacao) -> bool:
        """Devolve True para consultar, cadastrar disciplina e monitor, vincular e desvincular."""
        return operacao in OPERACOES_ADMINISTRADOR

    def opcoes_menu(self) -> tuple[Operacao, ...]:
        """Devolve a consulta e as operações de administração."""
        return OPERACOES_ADMINISTRADOR
