"""Monitor de disciplina, identificado pela matrícula."""

from monitorias.dominio.excecoes import DadosInvalidos
from monitorias.dominio.usuario import UsuarioCadastrado, Operacao, OPERACOES_MONITOR

from abc import ABC, abstractmethod


class Monitor(UsuarioCadastrado):

    """Monitor da UFMG, com permissões de gerenciamento
    dos próprios horários de atendimento."""

    def pode(self, operacao: Operacao) -> bool:
        """Verifica se o monitor tem permissão para a operação."""
        return operacao in OPERACOES_MONITOR

    def opcoes_menu(self) -> tuple[Operacao, ...]:
        """Devolve a consulta e as operações de monitor."""
        return OPERACOES_MONITOR