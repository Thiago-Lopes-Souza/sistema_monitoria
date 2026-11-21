"""Resultado da F2 (consultar monitorias): só descreve dados, sem print nem input."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .atendimento import Atendimento
from .disciplina import Disciplina
from .monitor import Monitor


class SituacaoConsulta(Enum):
    """As quatro respostas válidas de uma consulta (nenhuma é rejeição)."""

    COM_HORARIOS = "com_horarios"
    MONITOR_SEM_HORARIOS = "monitor_sem_horarios"
    SEM_HORARIOS_NA_MODALIDADE = "sem_horarios_na_modalidade"
    NENHUMA_MONITORIA_CADASTRADA = "nenhuma_monitoria_cadastrada"


@dataclass(frozen=True)
class ItemConsulta:
    """Um monitor e seus horários na disciplina, já filtrados e ordenados."""

    monitor: Monitor
    atendimentos: tuple[Atendimento, ...]


@dataclass(frozen=True)
class ResultadoConsulta:
    """Retorno de CadastroMonitorias.consultar_monitorias.

    modalidade é "presencial", "online" ou None (todas); dia é um dia de
    segunda a sábado ou None (todos).
    """

    disciplina: Disciplina
    situacao: SituacaoConsulta
    itens: tuple[ItemConsulta, ...]
    modalidade: str | None
    dia: str | None = None